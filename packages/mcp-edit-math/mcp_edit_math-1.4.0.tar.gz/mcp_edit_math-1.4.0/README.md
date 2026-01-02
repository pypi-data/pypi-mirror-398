# 🛡️ Edit Math Supervisor (MCP Server)

![Vibecoding](https://img.shields.io/badge/Built_with-Vibecoding-ff69b4?style=flat-square)
![PyPI](https://img.shields.io/pypi/v/mcp-edit-math)

**Architectural Gatekeeper for AI Coding Assistants.**

**Edit Math Supervisor** is an advanced [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that acts as a **Stateful Gatekeeper** for AI coding assistants (Claude Desktop, Roo Code, Cline, Lingma).

It prevents "Tunnel Vision" by forcing the AI to verify code dependencies before editing. Unlike simple linters, this server **physically blocks** file saving until the AI proves that the changes are safe.

---

### 🆕 What's New in v1.4.0
*   **Python Support:** Native AST parsing for Python files.
*   **HTML Support:** Dependency detection in `<script>` tags and event handlers.
*   **2-Step Handshake:** New security mechanism. The server now requires a specific token (`'ok'`) to confirm dangerous edits, preventing the AI from "hallucinating" user consent.
*   **Renaming Detection:** Automatically triggers Strict Mode if a function signature changes.

---

### ✨ Key Features

*   **Polyglot AST Parsing:** Accurate dependency detection for **JavaScript**, **TypeScript**, **Python**, and **HTML**.
*   **Stateful Gatekeeper:** The server tracks verification status. The `commit_safe_edit` tool returns `⛔ ACCESS DENIED` if the Integrity Score is not 1.0.
*   **Interactive Conflict Resolution:** If the AI detects breaking changes, the server forces it to **stop and ask the user** for confirmation using a secure handshake protocol.
*   **Smart Filtering:** Automatically ignores standard language methods (e.g., `.map()`, `print()`) to keep the focus on your business logic.

### 🚀 The "#editmath" Protocol

The server enforces a strict workflow:

1.  **🔍 SCAN:** The AI scans the target function using AST.
2.  **🎫 TICKET:** The AI verifies dependencies. If conflicts exist, the server puts the request in `PENDING` state and demands user confirmation.
3.  **💾 COMMIT:** Only with a valid ticket (or user override) can the AI save changes.

### 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yrannkv/mcp-edit-math.git
    cd mcp-edit-math
    ```

2.  **Install dependencies:**
    *Note: Specific versions are required for stability.*
    ```bash
    pip install mcp tree-sitter==0.21.3 tree-sitter-javascript==0.21.0 tree-sitter-typescript==0.21.0 tree-sitter-html==0.20.3
    ```

3.  **Configure your MCP Client:**
    Add this to your configuration file (e.g., `claude_desktop_config.json`):
    ```json
    {
      "mcpServers": {
        "edit-math": {
          "command": "python",
          "args": ["/absolute/path/to/mcp-edit-math/mcp_edit_math.py"]
        }
      }
    }
    ```

### ⚡ Quick Start (via uvx)

If you use `uv`, you can run the server directly without cloning the repo:

```json
{
  "mcpServers": {
    "edit-math": {
      "command": "uvx",
      "args": ["mcp-edit-math"]
    }
  }
}


### 🤖 System Prompt (Required)

Add this to your AI's **Custom Instructions** or `.cursorrules` to activate the protocol:

```text

=== 🛡️ EDIT MATH PROTOCOL (v1.4.0) ===
Trigger: When user types "#editmath".

You are operating under a strict safety protocol. Direct file editing is FORBIDDEN.
Follow this sequence precisely:

1. 🔍 SCAN: Call `scan_dependencies(code, target_function)`.
   - Determine `language` ("js", "ts", "html", "python") based on file extension.

2. 🎫 GET TICKET: Call `calculate_integrity_score`.
   - **REQUIRED:** Provide `proposed_header` to check for renaming.
   - **If server returns "STOP. INTERVENTION REQUIRED":**
     a. STOP generating immediately.
     b. Present the plan/conflicts to the user.
     c. ASK: "Do you approve? (Type 'ok')"
     d. **CRITICAL:** END YOUR TURN. Do not simulate user response.
     e. When user replies "ok", call `calculate_integrity_score` again with `confirmation_token='ok'`.

3. 💾 COMMIT: Call `commit_safe_edit`.
   - If you need to force a commit (e.g., for unverified external libs), ask the user first, then use `force_override=True`.


### 🧘‍♀️ Philosophy: The Meta-Project

This project is a **materialized Aspiration** — a testament to **Vibecoding**: a state where intuition and logic co-create.

It emerged from the synergy of **Human Aspiration and AI Execution**.

The Aspiration was clear: to transcend raw AI coding — powerful, yet *architecturally unconscious*.
In response, the core Human contribution took form: the **"Supervisor" pattern**, co-designed with **Google Gemini** — a meta-cognitive tool that compels the model to pause, reflect, and verify.

Thus, Aspiration was not just declared — **it was architected**.


<a id="donate"></a>
## ☕ Support the Project

If this tool saved you time or prevented a bug, you can support the development via crypto:

*   **EVM (Ethereum / Base / BNB):** `0x13cA48D52bd7bB4f12Daa39730299b21c6DaA566`
*   **Solana:** `3TPUjSQ77GaCESp1Dugt8AjQJaD51jHAtckEQNLuWd83`
*   **Bitcoin:** `bc1qsles2ylewztk5297hnmfqwmjt2lk9qgchd78at`

---
License: Apache-2.0
Author: Annenkov Yuriy
**Co-authored with:** Google Gemini