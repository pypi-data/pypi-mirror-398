# Gemini CLI: The Developer's Guide

Welcome to the Gemini CLI! This tool is an advanced AI agent running directly in your terminal, capable of interacting with your codebase, system, and external services through a powerful ecosystem of extensions and MCP (Model Context Protocol) servers.

## 1. Project Overview

The Gemini CLI operates as a **Context-Aware Agent**. It doesn't just chat; it *acts*.

### Key Components:
*   **The Agent:** Your AI pair programmer.
*   **Workspace:** The current directory (`.`) where the agent has file access.
*   **MCP Servers:** Bridges to external tools (GitHub, SQLite, etc.).
*   **Extensions:** Specialized capabilities like Image Generation (Nano Banana) or R Development (Mediationverse).

## 2. Core Workflow

The most effective way to work with Gemini CLI is the **Plan -> Act -> Verify** loop.

1.  **Request:** State your goal clearly.
    > "Refactor `src/utils.py` to use `pathlib` instead of `os.path`."
2.  **Plan:** The agent will analyze the file and propose a plan (often using `codebase_investigator` for complex tasks).
3.  **Act:** The agent uses tools like `replace` or `write_file` to modify code.
4.  **Verify:** The agent runs tests or linters (`run_shell_command`) to ensure correctness.

## 3. Extension Deep Dive

### 👩‍💻 Jules: The Autonomous Engineer
**Best for:** Large, complex tasks that require modifying multiple files or deep reasoning.

*   **Workflow:**
    1.  **Trigger:** `/jules start "Upgrade all dependencies and fix breaking changes"`
    2.  **Process:** Jules takes over, creating a separate session to plan and execute the changes autonomously.
    3.  **Monitor:** Check progress with `/jules status`.

### 🖼️ Nano Banana: Visual Assets
**Best for:** Creating placeholders, documentation assets, or diagrams.

*   **Example: Create a flow diagram for your docs**
    ```bash
    /diagram prompt="User login flow with OAuth2" type=flowchart
    ```
*   **Example: Generate an app icon**
    ```bash
    /icon prompt="Terminal with a brain" style=modern background=transparent
    ```

### 🔍 GitHub Integration (via MCP)
**Best for:** CI/CD workflows, issue management, and cross-repo research.

*   **Setup:** Ensure `github-mcp-server` is configured in `.gemini/settings.json`.
*   **Usage:**
    *   "Search for open issues about 'bugs' in this repo."
    *   "Fetch the latest `main` branch version of `README.md`."

### 📦 Mediationverse (R Specialists)
**Best for:** R package developers.

*   **Workflow:**
    1.  `/r-init` to scaffold a package.
    2.  Write code interactively.
    3.  `/r-check` and `/r-test` to validate before CRAN submission.
    4.  `/r-docs` to auto-generate `roxygen2` documentation.

## 4. Configuration & Customization

### `.gemini/GEMINI.md` (Context File)
This file defines the agent's "Brain". Use it to:
*   Set a persona (e.g., "You are a Senior SRE").
*   Define coding standards ("Always use TypeScript").
*   Set communication rules ("Be concise, BLUF").

**Example:**
```markdown
# IDENTITY
You are a Python Performance Expert.

# RULES
1. Always profile before optimizing.
2. Use snake_case.
```

### `.gemini/settings.json` (System Config)
Configures the MCP servers that give the agent tools.

**Example (GitHub + Filesystem):**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "node",
      "args": ["path/to/server", "/projects"]
    },
    "github": {
      "command": "github-mcp-server",
      "env": { "GITHUB_TOKEN": "..." }
    }
  }
}
```

## 5. Best Practices

1.  **Be Specific:** "Fix the bug" is weak. "Fix the IndexError in `parser.py` line 42 when input is empty" is strong.
2.  **Use Context:** The agent reads your project files. Refer to them by name.
3.  **Verify:** Always ask the agent to run tests after making changes.
4.  **Chain Commands:** You can combine requests. "Create a file named `hello.py`, write a main function, and then run it."

## 6. Troubleshooting

*   **Tools failing?** Check `.gemini/settings.json`.
*   **Agent "forgot" something?** Use `save_memory` for permanent facts or update `.gemini/GEMINI.md`.
*   **Need a clean slate?** Use `/clear` to reset the conversation window (but not the project files).
