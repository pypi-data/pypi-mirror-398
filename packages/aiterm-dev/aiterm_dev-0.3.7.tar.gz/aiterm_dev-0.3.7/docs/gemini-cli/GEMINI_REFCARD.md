# Gemini CLI Quick Reference Card

## 🚀 Core CLI Commands
| Command | Description |
|---------|-------------|
| `/help` | Display general help and available commands |
| `/clear` | Clear the current conversation history |
| `/bug` | Report a bug or provide feedback |
| `/exit` | Quit the CLI session |

## 🧩 Extension Commands

### 👩‍💻 Jules (Agentic Coding)
*Autonomous multi-file refactoring and dependency management.*

| Command | Syntax | Description |
|---------|--------|-------------|
| **Start Task** | `/jules start <description>` | Begin a new complex task (refactoring, tests) |
| **Status** | `/jules status` | Check progress of the current task |
| **Login** | `jules login` | Authenticate with Google/GitHub (Shell) |

### 🖼️ Nano Banana (Image Generation)
*Generate, edit, and restore images directly in the CLI.*

| Command | Arguments | Example |
|---------|-----------|---------|
| `/image` | `prompt`, `--count`, `--styles` | `/image prompt="cyberpunk city" --count=2` |
| `/icon` | `prompt`, `style`, `background` | `/icon prompt="rocket" style=flat bg=white` |
| `/story` | `prompt`, `steps`, `style` | `/story prompt="evolution of man" steps=4` |
| `/diagram`| `prompt`, `type` | `/diagram prompt="server architecture" type=flowchart` |
| `/pattern`| `prompt`, `repeat` | `/pattern prompt="floral" repeat=tile` |

### 📦 Mediationverse (R Package Dev)
*R development workflows and package management.*

| Command | Purpose |
|---------|---------|
| `/r-init` | Initialize a new R package |
| `/r-check` | Run `devtools::check()` |
| `/r-test` | Run tests (`testthat`) |
| `/r-docs` | Generate documentation (`roxygen2`) |
| `/r-review`| Perform CRAN-ready code review |

### 🔍 Data Commons
*Query statistical data from the Data Commons Knowledge Graph.*

| Action | Usage |
|--------|-------|
| **Search** | Natural language queries like "US unemployment rate" or "Population of France" |
| **Fetch** | Agent automatically calls `get_observations` for validated metrics |

### 👓 Code Review
| Command | Description |
|---------|-------------|
| `/code-review` | Request a review of your current pending changes |

## 🛠️ MCP Tools (Agent Capabilities)
*Implicit capabilities triggered by natural language requests.*

| Tool | Trigger Examples |
|------|------------------|
| **FileSystem** | "Read file X", "List directory Y", "Write code to Z" |
| **GitHub** | "Search repo X", "Get issue #123", "Read file from remote" |
| **Shell** | "Run command X", "Install package Y" |
| **Codebase** | "Explain the architecture", "Find where function X is used" |

## 🔑 Key Concepts

*   **Context (`.gemini/GEMINI.md`)**: Defines the agent's persona, rules, and communication style.
*   **Settings (`.gemini/settings.json`)**: Configures MCP servers and environment variables.
*   **Memory**: The agent can remember user preferences via `save_memory`.
*   **Todos**: Complex tasks are broken down into a managed Todo list.

