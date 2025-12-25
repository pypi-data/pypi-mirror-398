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
VERSION: 1.0.1 (Robust Version Compatibility)
------------------------------------------------------------------------------
"""

from mcp.server.fastmcp import FastMCP
import os
import traceback
from typing import List, Dict, Set, Tuple, Optional

# --- БЛОК ИНИЦИАЛИЗАЦИИ TREE-SITTER (УНИВЕРСАЛЬНЫЙ) ---
try:
    from tree_sitter import Language, Parser
    import tree_sitter_javascript
    import tree_sitter_typescript
except ImportError:
    raise ImportError("Run: pip install tree-sitter tree-sitter-javascript tree-sitter-typescript")

mcp = FastMCP("EditMathSupervisor")
APPROVAL_STATE: Dict[str, bool] = {}

# Глобальные переменные для парсеров
parser_js = None
parser_ts = None
JS_LANGUAGE = None
TS_LANGUAGE = None

def init_parsers():
    """Инициализация парсеров с поддержкой разных версий библиотеки."""
    global parser_js, parser_ts, JS_LANGUAGE, TS_LANGUAGE
    
    try:
        # Получаем указатели на языки
        js_ptr = tree_sitter_javascript.language()
        ts_ptr = tree_sitter_typescript.language_typescript()
        
        # Попытка 1: Новая версия (0.22+) требует имя языка
        try:
            JS_LANGUAGE = Language(js_ptr, "javascript")
            TS_LANGUAGE = Language(ts_ptr, "typescript")
        except TypeError:
            # Попытка 2: Старая версия (0.21.x) не принимает имя
            JS_LANGUAGE = Language(js_ptr)
            TS_LANGUAGE = Language(ts_ptr)
            
        # Инициализация парсеров
        parser_js = Parser()
        parser_js.set_language(JS_LANGUAGE)
        
        parser_ts = Parser()
        parser_ts.set_language(TS_LANGUAGE)
        
    except Exception as e:
        print(f"CRITICAL ERROR initializing Tree-sitter: {e}")
        # Не роняем сервер сразу, чтобы увидеть ошибку в логах MCP
        pass

# Запускаем инициализацию
init_parsers()

# -------------------------------------------------------

def has_syntax_errors(tree) -> bool:
    if not tree: return False
    root = tree.root_node
    return root.has_error

def _extract_dependencies_from_tree(tree, target_name: str, ignore_custom: Optional[List[str]] = None) -> Tuple[Set[str], List[str]]:
    if not tree:
        return set(), ["Error: Tree is None"]
        
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

        for i in range(node.child_count):
            find_calls(node.child(i))

    find_calls(target_node)
    return dependencies, logs

@mcp.tool()
def scan_dependencies(code: str, target_function: str, language: str = "auto", ignore_custom: List[str] = None) -> str:
    """
    Scans code for dependencies.
    """
    # ЗАЩИТА ОТ ПАДЕНИЯ
    try:
        if parser_js is None:
            return "CRITICAL ERROR: Tree-sitter parsers failed to initialize. Check server logs."

        APPROVAL_STATE[target_function] = False
        
        lang_lower = language.lower()
        selected_parser = parser_js
        logs_prefix = "JavaScript"

        # --- ЛОГИКА АВТО-ДЕТЕКЦИИ ---
        if lang_lower == "auto":
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
        else:
            selected_parser = parser_js
            logs_prefix = "JavaScript"

        # --- ПАРСИНГ ---
        tree_raw = selected_parser.parse(bytes(code, "utf8"))
        deps, logs = _extract_dependencies_from_tree(tree_raw, target_function, ignore_custom)
        
        used_wrapper = False
        if not deps:
            logs.append("--- Attempting Auto-Wrapper ---")
            wrapped_code = f"class AutoWrapper {{ {code} }}"
            tree_wrapped = selected_parser.parse(bytes(wrapped_code, "utf8"))
            deps_wrapped, logs_wrapped = _extract_dependencies_from_tree(tree_wrapped, target_function, ignore_custom)
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
        # Возвращаем ошибку в чат, а не крашим сервер
        return f"INTERNAL SERVER ERROR during scanning: {str(e)}\nTraceback: {traceback.format_exc()}"

@mcp.tool()
def calculate_integrity_score(
    target_function: str, 
    dependencies: List[str], 
    verified_dependencies: List[str],
    user_confirmed: bool = False
) -> str:
    """
    Рассчитывает Integrity Score.
    Если есть зависимости, ТРЕБУЕТ подтверждения от пользователя (Strict Mode).
    """
    # 1. Если зависимостей нет - зеленый свет сразу
    if not dependencies:
        APPROVAL_STATE[target_function] = True
        return f"Score: 1.0 (No dependencies). Edit to '{target_function}' is safe."

    # 2. Если зависимости есть, но нет флага подтверждения - БЛОКИРУЕМ
    if not user_confirmed:
        return f"""
        ✋ STRICT MODE INTERVENTION
        --------------------------
        Dependencies detected: {len(dependencies)} ({', '.join(dependencies[:3])}...)
        
        The server FORBIDS silent edits when dependencies exist.
        
        INSTRUCTION FOR AI:
        1. STOP. Do not edit yet.
        2. Explain your plan to the user: "I see dependencies. I plan to change X and update Y. Proceed?"
        3. Wait for the user's "Yes".
        4. Call this tool again with `user_confirmed=True`.
        """

    # 3. Если флаг есть - считаем математику (для проформы) и даем доступ
    # Мы доверяем флагу user_confirmed, так как ИИ не может его поставить, 
    # не получив ответ от юзера (в рамках диалога).
    
    BASE_WEIGHT = 0.5
    REMAINING_WEIGHT = 0.5
    count_deps = len(dependencies)
    weight_per_dep = REMAINING_WEIGHT / count_deps
    current_score = BASE_WEIGHT
    
    details = [f"1. Target '{target_function}' edited: +{BASE_WEIGHT}"]
    
    for dep in dependencies:
        if dep in verified_dependencies:
            current_score += weight_per_dep
            details.append(f"2. Dependency '{dep}' VERIFIED: +{weight_per_dep:.4f}")
        else:
            details.append(f"3. Dependency '{dep}' NOT VERIFIED: +0.0")

    # В строгом режиме, если юзер подтвердил, мы можем простить мелкие недочеты математики,
    # либо требовать и математику, и подтверждение. 
    # Сделаем строго: математика тоже должна сойтись.
    is_safe = current_score >= 0.99
    
    if is_safe:
        APPROVAL_STATE[target_function] = True
        return f"Integrity Score: {current_score:.4f} / 1.0\nSTATUS: ✅ ACCESS GRANTED (User Confirmed)"
    else:
        return f"""
        Integrity Score: {current_score:.4f} / 1.0
        STATUS: ⛔ ACCESS DENIED
        
        User confirmed, BUT you missed verifying some dependencies in the list.
        Please verify: {[d for d in dependencies if d not in verified_dependencies]}
        """

@mcp.tool()
def commit_safe_edit(target_function: str, file_path: str, full_file_content: str, force_override: bool = False) -> str:
    has_ticket = APPROVAL_STATE.get(target_function, False)
    
    if not has_ticket and not force_override:
        return f"""
        ⛔ SECURITY BLOCK
        -----------------
        Integrity Score is NOT 1.0. Access Denied.
        OPTIONS:
        1. Verify dependencies.
        2. Ask user for permission and use force_override=True.
        """
    
    try:
        file_path = os.path.normpath(file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_file_content)
        APPROVAL_STATE[target_function] = False
        status = "✅ SAFE COMMIT" if has_ticket else "⚠️ FORCED COMMIT"
        return f"{status}: File '{file_path}' updated."
    except Exception as e:
        return f"❌ ERROR: {str(e)}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()