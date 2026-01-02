"""
Copyright 2025 Annenkov Yuriy

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

------------------------------------------------------------------------------
MODULE: Edit Math Supervisor (MCP Server)
DESCRIPTION: Architectural Gatekeeper for AI coding. 
             Enforces dependency checks before file edits.
VERSION: 1.4.0 (State Machine + 'ok' Token Security)
------------------------------------------------------------------------------
"""

from mcp.server.fastmcp import FastMCP
import os
import traceback
import ast
from typing import List, Dict, Set, Tuple, Optional, Union

# --- БЛОК ИНИЦИАЛИЗАЦИИ TREE-SITTER ---
try:
    from tree_sitter import Language, Parser
    import tree_sitter_javascript
    import tree_sitter_typescript
    import tree_sitter_html
except ImportError:
    raise ImportError("Run: pip install tree-sitter==0.21.3 tree-sitter-javascript==0.21.0 tree-sitter-typescript==0.21.0 tree-sitter-html==0.20.3")

mcp = FastMCP("EditMathSupervisor")

# МАШИНА СОСТОЯНИЙ: "NONE" -> "PENDING" -> "APPROVED"
APPROVAL_STATE: Dict[str, str] = {}

# Глобальные переменные для парсеров
parser_js = None
parser_ts = None
parser_html = None
JS_LANGUAGE = None
TS_LANGUAGE = None

def init_parsers():
    """Инициализация парсеров с явной обработкой каждого языка."""
    global parser_js, parser_ts, parser_html, JS_LANGUAGE, TS_LANGUAGE
    
    def make_language(ptr, name):
        try:
            return Language(ptr, name)
        except TypeError:
            return Language(ptr)
        except Exception:
            return ptr

    try:
        js_ptr = tree_sitter_javascript.language()
        JS_LANGUAGE = make_language(js_ptr, "javascript")
        parser_js = Parser()
        parser_js.set_language(JS_LANGUAGE)
        
        ts_ptr = tree_sitter_typescript.language_typescript()
        TS_LANGUAGE = make_language(ts_ptr, "typescript")
        parser_ts = Parser()
        parser_ts.set_language(TS_LANGUAGE)

        html_ptr = tree_sitter_html.language()
        html_lang = make_language(html_ptr, "html")
        parser_html = Parser()
        parser_html.set_language(html_lang)
        
    except Exception as e:
        print(f"CRITICAL ERROR initializing Tree-sitter: {e}")
        traceback.print_exc()

init_parsers()

# -------------------------------------------------------

def has_syntax_errors(tree) -> bool:
    if not tree: return False
    root = tree.root_node
    return root.has_error

# --- ЛОГИКА PYTHON (AST) ---
def _extract_python_dependencies(code: str, target_name: str, ignore_custom: Optional[List[str]] = None) -> Tuple[Set[str], List[str]]:
    dependencies = set()
    logs = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return set(), [f"Python Syntax Error: {e}"]

    target_node = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == target_name:
                target_node = node
                break
    
    if target_node:
        logs.append(f"✅ Found Python target: {type(target_node).__name__}")
    else:
        logs.append("❌ Target node NOT found. Scanning entire snippet.")
        target_node = tree

    IGNORE_PYTHON = {
        "print", "len", "str", "int", "float", "bool", "list", "dict", "set", "tuple",
        "range", "enumerate", "zip", "map", "filter", "sum", "min", "max", "abs",
        "isinstance", "issubclass", "type", "super", "getattr", "setattr", "hasattr",
        "open", "dir", "id", "input", "repr", "round", "sorted", "reversed",
        "__init__", "__str__", "__repr__", "self"
    }
    if ignore_custom:
        IGNORE_PYTHON.update(ignore_custom)

    for node in ast.walk(target_node):
        call_name = None
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
                if isinstance(node.func.value, ast.Name) and node.func.value.id == 'self':
                    logs.append(f"Found self call: {call_name}")
        
        if call_name:
            if call_name not in IGNORE_PYTHON and call_name != target_name:
                dependencies.add(call_name)

    return dependencies, logs

# --- ЛОГИКА JS/TS (Tree-sitter) ---
def _extract_dependencies_from_tree(tree, target_name: str, ignore_custom: Optional[List[str]] = None) -> Tuple[Set[str], List[str]]:
    if not tree: return set(), ["Error: Tree is None"]
    root_node = tree.root_node
    dependencies = set()
    logs = []

    def find_target_node(node, name):
        if node.type == 'class_declaration':
            name_node = node.child_by_field_name('name')
            if name_node and name_node.text.decode('utf8') == name: return node
        if node.type == 'function_declaration':
            name_node = node.child_by_field_name('name')
            if name_node and name_node.text.decode('utf8') == name: return node
        elif node.type == 'method_definition':
            name_node = node.child_by_field_name('name')
            if name_node and name_node.text.decode('utf8') == name: return node.child_by_field_name('body')
        elif node.type == 'lexical_declaration':
            for i in range(node.child_count):
                child = node.child(i)
                if child.type == 'variable_declarator':
                    name_node = child.child_by_field_name('name')
                    if name_node and name_node.text.decode('utf8') == name: return child.child_by_field_name('value')
        for i in range(node.child_count):
            res = find_target_node(node.child(i), name)
            if res: return res
        return None

    target_node = find_target_node(root_node, target_name)
    
    if target_node:
        logs.append(f"✅ Found target node type: {target_node.type}")
    else:
        logs.append("❌ Target node NOT found. Scanning root.")
        target_node = root_node

    IGNORE_LIST = {
        "console", "Math", "JSON", "Date", "Object", "Array", "Promise", "Error",
        "parseInt", "parseFloat", "setTimeout", "setInterval", "alert", "confirm",
        "require", "window", "document", "history", "navigator", "location"
    }
    
    IGNORE_METHODS = {
        "log", "error", "warn", "info", "debug",
        "push", "pop", "shift", "unshift", "splice", "slice", "join", "split",
        "map", "filter", "reduce", "forEach", "find", "some", "every",
        "toString", "toFixed", "replace", "replaceAll", "trim",
        "querySelector", "querySelectorAll", "getElementById", "addEventListener",
        "remove", "add", "has", "get", "set", "keys", "values", "entries",
        "now", "abs", "round", "floor", "ceil", "min", "max", "random",
        "then", "catch", "finally", "length", "subscribe", "unsubscribe"
    }

    if ignore_custom:
        IGNORE_LIST.update(ignore_custom)
        IGNORE_METHODS.update(ignore_custom)

    def find_calls(node):
        if node.type == 'call_expression':
            func_node = node.child_by_field_name('function')
            call_name = None
            
            if func_node.type == 'identifier':
                call_name = func_node.text.decode('utf8')
            elif func_node.type == 'member_expression':
                prop_node = func_node.child_by_field_name('property')
                obj_node = func_node.child_by_field_name('object')
                if prop_node:
                    method_name = prop_node.text.decode('utf8')
                    obj_name = obj_node.text.decode('utf8') if obj_node else "unknown"
                    if (obj_node.type == 'this') or (obj_name == 'this'):
                        call_name = method_name
                    elif method_name not in IGNORE_METHODS:
                        call_name = method_name
            
            if call_name:
                if call_name not in IGNORE_LIST and call_name != target_name:
                    dependencies.add(call_name)
                else:
                    # logs.append(f"Ignored: {call_name}")
                    pass

        for i in range(node.child_count):
            find_calls(node.child(i))

    find_calls(target_node)
    return dependencies, logs

# --- ЛОГИКА HTML ---
def _extract_html_dependencies(tree) -> Tuple[Set[str], List[str]]:
    if not tree: return set(), ["Error: HTML Tree is None"]
    root_node = tree.root_node
    dependencies = set()
    logs = []
    
    logs.append("Scanning HTML structure...")

    def traverse(node):
        if node.type == 'attribute':
            attr_name = None
            attr_value = None
            
            for i in range(node.child_count):
                child = node.child(i)
                if child.type == 'attribute_name':
                    attr_name = child.text.decode('utf8')
                elif child.type == 'quoted_attribute_value' or child.type == 'attribute_value':
                    attr_value = child.text.decode('utf8').strip('"\'')

            if attr_name and attr_value:
                if attr_name == 'src':
                    parent = node.parent
                    if parent and (parent.type == 'script_start_tag' or parent.type == 'script_element'):
                        dependencies.add(f"FILE: {attr_value}")
                        logs.append(f"Found script: {attr_value}")
                
                elif attr_name.startswith('on'):
                    func_name = attr_value.split('(')[0].strip()
                    if func_name:
                        dependencies.add(f"EVENT: {func_name}")
                        logs.append(f"Found event: {attr_name} -> {func_name}")

        for i in range(node.child_count):
            traverse(node.child(i))

    traverse(root_node)
    return dependencies, logs

@mcp.tool()
def scan_dependencies(
    code: str, 
    target_function: str, 
    language: str = "auto", 
    ignore_custom: Union[List[str], str, None] = None
) -> str:
    """
    Scans code for dependencies. Supports JS, TS, HTML, Python.
    """
    try:
        if parser_js is None: return "CRITICAL ERROR: Tree-sitter parsers failed to initialize."
        
        # СБРОС СОСТОЯНИЯ ПРИ НОВОМ СКАНИРОВАНИИ
        # Это важно: если ИИ начал сканировать заново, он теряет право на правку
        APPROVAL_STATE[target_function] = "NONE"
        
        normalized_ignore = []
        if isinstance(ignore_custom, list):
            normalized_ignore = ignore_custom
        elif isinstance(ignore_custom, str):
            normalized_ignore = [ignore_custom]
        
        lang_lower = language.lower()
        
        # --- PYTHON ---
        if lang_lower == "python" or lang_lower == "py":
            deps, logs = _extract_python_dependencies(code, target_function, normalized_ignore)
            sorted_deps = sorted(list(deps))
            return f"""
            [ACCESS REVOKED] Python Analysis for '{target_function}':
            --------------------------------
            Found Dependencies: {', '.join(sorted_deps) if sorted_deps else 'None'}
            SUGGESTED INDEX: {target_function + ("_" + "_".join(sorted_deps) if sorted_deps else "")}
            
            DEBUG INFO:
            {chr(10).join(logs[:15])}
            """

        # --- HTML ---
        if lang_lower == "html":
            if not parser_html: return "Error: HTML parser not initialized."
            tree = parser_html.parse(bytes(code, "utf8"))
            deps, logs = _extract_html_dependencies(tree)
            sorted_deps = sorted(list(deps))
            return f"""
            [ACCESS REVOKED] HTML Analysis for '{target_function}':
            --------------------------------
            Found Dependencies: {', '.join(sorted_deps) if sorted_deps else 'None'}
            DEBUG INFO:
            {chr(10).join(logs)}
            """

        # --- JS / TS ---
        selected_parser = parser_js
        logs_prefix = "JavaScript"

        if lang_lower == "auto":
            if "def " in code or "import " in code or "class " in code:
                 try:
                     ast.parse(code)
                     deps, logs = _extract_python_dependencies(code, target_function, normalized_ignore)
                     sorted_deps = sorted(list(deps))
                     return f"""
                     [ACCESS REVOKED] Auto-Detected Python Analysis for '{target_function}':
                     --------------------------------
                     Found Dependencies: {', '.join(sorted_deps) if sorted_deps else 'None'}
                     SUGGESTED INDEX: {target_function + ("_" + "_".join(sorted_deps) if sorted_deps else "")}
                     """
                 except:
                     pass

            tree_js = parser_js.parse(bytes(code, "utf8"))
            js_errors = has_syntax_errors(tree_js)
            tree_ts = parser_ts.parse(bytes(code, "utf8"))
            ts_errors = has_syntax_errors(tree_ts)
            
            if js_errors and not ts_errors:
                return """
                🛑 AMBIGUITY DETECTED
                ---------------------
                The code looks like TypeScript. Please ASK THE USER: "Is this JavaScript or TypeScript?"
                """
            elif not js_errors:
                selected_parser = parser_js
                logs_prefix = "Auto-Detected JS"
            else:
                selected_parser = parser_ts
                logs_prefix = "Auto-Detected TS (Fallback)"
                
        elif lang_lower in ["ts", "typescript", "tsx"]:
            selected_parser = parser_ts
            logs_prefix = "TypeScript"
        elif lang_lower == "python":
            return "Python support via AST module is available in v4.3 if needed."

        tree_raw = selected_parser.parse(bytes(code, "utf8"))
        deps, logs = _extract_dependencies_from_tree(tree_raw, target_function, normalized_ignore)
        
        used_wrapper = False
        if not deps:
            logs.append("--- Attempting Auto-Wrapper ---")
            wrapped_code = f"class AutoWrapper {{ {code} }}"
            tree_wrapped = selected_parser.parse(bytes(wrapped_code, "utf8"))
            deps_wrapped, logs_wrapped = _extract_dependencies_from_tree(tree_wrapped, target_function, normalized_ignore)
            if deps_wrapped:
                deps = deps_wrapped
                logs.extend(logs_wrapped)
                used_wrapper = True

        sorted_deps = sorted(list(deps))
        index_str = target_function + ("_" + "_".join(sorted_deps) if sorted_deps else "")
        
        debug_output = "\n    ".join(logs[:15])
        
        return f"""
        [ACCESS REVOKED] {logs_prefix} Analysis for '{target_function}':
        --------------------------------
        Found Dependencies: {', '.join(sorted_deps) if sorted_deps else 'None'}
        SUGGESTED INDEX: {index_str}
        
        DEBUG INFO:
        Wrapper Used: {used_wrapper}
        Logs:
        {debug_output}
        ...
        """
    except Exception as e:
        return f"INTERNAL SERVER ERROR during scanning: {str(e)}\nTraceback: {traceback.format_exc()}"

@mcp.tool()
def calculate_integrity_score(
    target_function: str, 
    dependencies: List[str], 
    verified_dependencies: List[str],
    proposed_header: str = "",
    breaking_change_description: str = "",
    confirmation_token: str = ""
) -> str:
    """
    Рассчитывает Integrity Score.
    Использует State Machine для защиты от "читерства" ИИ.
    """
    deps_safe = dependencies if dependencies else []
    verified_safe = verified_dependencies if verified_dependencies else []

    # 1. Авто-детекция переименования
    is_renaming = False
    if proposed_header:
        if target_function not in proposed_header:
            is_renaming = True
    
    # 2. Нужна ли защита?
    needs_confirmation = (len(deps_safe) > 0) or (len(breaking_change_description) > 0) or is_renaming

    # 3. МАШИНА СОСТОЯНИЙ
    current_state = APPROVAL_STATE.get(target_function, "NONE")
    
    # Сценарий А: Первый заход (или ИИ пытается проскочить сразу)
    # Если защита нужна, но мы еще не в режиме PENDING -> БЛОКИРУЕМ
    if needs_confirmation and current_state != "PENDING":
        # Переводим в режим ожидания
        APPROVAL_STATE[target_function] = "PENDING"
        
        reasons = []
        if deps_safe: reasons.append(f"Dependencies: {len(deps_safe)}")
        if breaking_change_description: reasons.append("Breaking change declared")
        if is_renaming: reasons.append("Renaming detected")
        
        return f"""
        ✋ STRICT MODE INTERVENTION (Step 1/2)
        -------------------------------------
        Reason: {', '.join(reasons)}
        
        The server FORBIDS silent edits. You must obtain user permission.
        
        INSTRUCTION FOR AI:
        1. STOP. Do not edit yet.
        2. Explain the plan/conflicts to the user.
        3. ASK THE USER: "Type 'ok' to confirm."
        4. Wait for the user's input.
        5. Call this tool again with `confirmation_token='ok'`.
        """

    # Сценарий Б: Второй заход (после ответа пользователя)
    if current_state == "PENDING":
        # Проверяем токен "ok" (регистронезависимо)
        is_confirmed = (confirmation_token.strip().lower() == "ok")
        
        if not is_confirmed:
             return "⛔ ACCESS DENIED. I am waiting for the 'ok' token from the user."
        
        # Если токен верный - переходим к расчету баллов

    # 4. Расчет баллов
    if not deps_safe and not is_renaming and not breaking_change_description:
        APPROVAL_STATE[target_function] = "APPROVED"
        return f"Score: 1.0 (Safe). Edit to '{target_function}' is allowed."

    BASE_WEIGHT = 0.5
    REMAINING_WEIGHT = 0.5
    count_deps = len(deps_safe)
    
    if count_deps == 0:
        current_score = 1.0
    else:
        weight_per_dep = REMAINING_WEIGHT / count_deps
        current_score = BASE_WEIGHT
        for dep in deps_safe:
            if dep in verified_safe:
                current_score += weight_per_dep

    is_safe = current_score >= 0.99
    
    if is_safe:
        APPROVAL_STATE[target_function] = "APPROVED"
        return f"Integrity Score: {current_score:.4f} / 1.0\nSTATUS: ✅ ACCESS GRANTED (User Confirmed)"
    else:
        extra_verified = set(verified_safe) - set(deps_safe)
        hint_msg = f"\n💡 HINT: You verified items NOT in the list: {list(extra_verified)}.\nIf renaming, verify the ORIGINAL name." if extra_verified else ""
        return f"Integrity Score: {current_score:.4f} / 1.0\nSTATUS: ⛔ ACCESS DENIED\nUser confirmed, BUT you missed verifying dependencies: {[d for d in deps_safe if d not in verified_safe]}{hint_msg}"

@mcp.tool()
def commit_safe_edit(target_function: str, file_path: str, full_file_content: str, force_override: bool = False) -> str:
    current_state = APPROVAL_STATE.get(target_function, "NONE")
    
    if current_state != "APPROVED" and not force_override:
        return f"⛔ SECURITY BLOCK: Integrity Score is NOT 1.0. Current state: {current_state}. Access Denied."
    
    try:
        file_path = os.path.normpath(file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_file_content)
        APPROVAL_STATE[target_function] = "NONE" # Сброс после записи
        return f"✅ SAFE COMMIT: File '{file_path}' updated."
    except Exception as e:
        return f"❌ ERROR: {str(e)}"

def main():
    import os
    port = os.environ.get("PORT")
    if port:
        print(f"Starting in HTTP mode on port {port}...")
        mcp.run(transport="sse", port=int(port), host="0.0.0.0")
    else:
        mcp.run()

if __name__ == "__main__":
    main()