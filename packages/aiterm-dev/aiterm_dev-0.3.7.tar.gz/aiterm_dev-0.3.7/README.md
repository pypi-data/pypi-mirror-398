# aiterm

[![PyPI](https://img.shields.io/pypi/v/aiterm-dev)](https://pypi.org/project/aiterm-dev/)
[![CI](https://img.shields.io/github/actions/workflow/status/Data-Wise/aiterm/test.yml?branch=main&label=CI)](https://github.com/Data-Wise/aiterm/actions/workflows/test.yml)
[![Python](https://img.shields.io/pypi/pyversions/aiterm-dev)](https://pypi.org/project/aiterm-dev/)
[![License](https://img.shields.io/github/license/Data-Wise/aiterm)](https://github.com/Data-Wise/aiterm/blob/main/LICENSE)

**Terminal Optimizer for AI-Assisted Development**

Optimize your terminal (iTerm2+) for AI coding with Claude Code and Gemini CLI. Manage profiles, contexts, hooks, commands, and auto-approvals from one powerful CLI.

---

## 🚀 Installation

### Quick Install (Auto-detects best method)

```bash
curl -fsSL https://raw.githubusercontent.com/Data-Wise/aiterm/main/install.sh | bash
```

### macOS (Homebrew - Recommended)

```bash
brew install data-wise/tap/aiterm
```

### Cross-Platform (PyPI)

```bash
pip install aiterm-dev
```

### Using uv (fastest)

```bash
uv tool install aiterm-dev
```

### Using pipx

```bash
pipx install aiterm-dev
```

### From Source

```bash
pip install git+https://github.com/Data-Wise/aiterm
```

### Installation Methods Comparison

| Method | Command | Platform | Best For |
|--------|---------|----------|----------|
| **curl** | `curl -fsSL .../install.sh \| bash` | All | One-liner |
| **Homebrew** | `brew install data-wise/tap/aiterm` | macOS | Mac users |
| **uv** | `uv tool install aiterm-dev` | All | Speed |
| **pipx** | `pipx install aiterm-dev` | All | Isolation |
| **pip** | `pip install aiterm-dev` | All | Quick install |
| **Source** | `pip install git+...` | All | Latest dev |

---

## 🎯 Quick Start

```bash
# Check your setup
ait doctor

# Detect project context
ait detect

# View Claude Code settings
ait claude settings
```

---

## ✨ What It Does

**aiterm** makes your terminal intelligent for AI-assisted development:

### 🎨 Context-Aware Profiles
Automatically switch terminal colors and titles based on your project:

| Context | Icon | Profile | Triggered By |
|---------|------|---------|--------------|
| Production | 🚨 | Red theme | `*/production/*` path |
| AI Sessions | 🤖 | Purple theme | `*/claude-sessions/*` |
| R Packages | 📦 | Blue theme | `DESCRIPTION` file |
| Python | 🐍 | Green theme | `pyproject.toml` |
| Node.js | 📦 | Dark theme | `package.json` |
| Quarto | 📊 | Blue theme | `_quarto.yml` |

### 🛠️ Claude Code Integration
- Manage hooks (session-start, pre-commit, cost-tracker)
- Install command templates (/recap, /next, /focus)
- Configure auto-approvals (safe-reads, git-ops, dev-tools)
- Control MCP servers

### 📊 Status Bar Customization
Build custom status bars with:
- Project icon & name
- Git branch + dirty indicator
- API quota tracking
- Time in context
- Custom components

---

## 💡 Features

### Implemented (v0.2.1)

- [x] **Context Detection** - 8 project types with auto-switching
- [x] **iTerm2 Integration** - Profiles, titles, user variables
- [x] **Claude Code Settings** - View, backup, manage approvals
- [x] **Auto-Approval Presets** - 8 ready-to-use presets
- [x] **Diagnostics** - `aiterm doctor` health checks
- [x] **Short Aliases** - `ait` for quick access

### CLI Commands

```bash
# Core commands
ait --version          # Show version
ait doctor             # Health check
ait detect             # Detect project context
ait switch             # Apply context to terminal

# Context detection
ait context detect     # Show project type, git info
ait context apply      # Apply to iTerm2

# Claude Code settings
ait claude settings    # Show settings
ait claude backup      # Backup settings

# Auto-approvals
ait claude approvals list      # List permissions
ait claude approvals presets   # Show 8 presets
ait claude approvals add <preset>  # Add preset
```

### Also Available (v0.2.1)

- [x] **Hook Management** - List, install, validate hooks
- [x] **Command Templates** - Browse and install command templates
- [x] **MCP Server Integration** - List, test, validate MCP servers
- [x] **Documentation Helpers** - Validate docs, test code examples

### Coming Soon (v0.3+)

- Gemini CLI support
- IDE integrations (Positron, Zed, VS Code)
- Workflow automation

See [IDEAS.md](IDEAS.md) for full roadmap.

---

## 🏗️ Architecture

### CLI-First Design
```
aiterm/
├── Core Library      # Business logic, testable
├── CLI Layer         # Typer commands
└── Templates         # Profiles, hooks, commands
```

### Tech Stack
- **Language:** Python 3.10+
- **CLI:** Typer (modern, type-safe)
- **Output:** Rich (beautiful tables, colors)
- **Testing:** pytest
- **Distribution:** uv/pipx/PyPI

---

## 📖 Documentation

- **[IDEAS.md](IDEAS.md)** - Feature brainstorm & roadmap
- **[ROADMAP.md](ROADMAP.md)** - Week 1 MVP plan (day-by-day)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical design
- **[CLAUDE.md](CLAUDE.md)** - Guidance for Claude Code
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

---

## 🎯 Use Cases

### For R Developers
```bash
cd ~/projects/r-packages/medfit
# Terminal switches to R-Dev profile (blue)
# Title shows: 📦 medfit (main)
# Status bar shows quota usage
```

### For AI Power Users
```bash
aiterm claude approvals add-preset safe-reads
aiterm claude hooks install session-start
aiterm context history  # See where you've been today
```

### For Multi-Project Workflows
```bash
# Automatic profile switching as you navigate
cd ~/production/app          # → Red theme, production warnings
cd ~/claude-sessions/        # → Purple theme, AI optimized
cd ~/projects/research/      # → Default theme, research context
```

---

## 🔧 Development

### Setup
```bash
# Clone repo
git clone https://github.com/Data-Wise/aiterm.git
cd aiterm

# Set up environment (using uv - recommended)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Or traditional pip
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Try CLI
aiterm --help
```

### Project Status
**Version:** 0.2.1
**Tests:** 55 passing
**Status:** Released on Homebrew & PyPI

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## 📜 History

**v2.5.0 (Dec 15, 2024):** aiterm
- zsh-based terminal integration
- 8 context types
- iTerm2 status bar support
- Comprehensive test suite (15 tests)

**v3.0.0 (Dec 15, 2024):** Pivot to **aiterm**
- Python CLI architecture
- Claude Code deep integration
- Multi-tool support (Gemini)
- Expandable plugin system

---

## 🤝 Contributing

Not accepting external contributions yet (MVP phase). Check back at v1.0!

**Target for public release:**
- Multi-terminal support
- Documentation site
- PyPI + uv/pipx distribution
- Community templates

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

Built for AI-assisted development workflows with:
- [Claude Code](https://claude.com/code) - Anthropic's CLI tool
- [Gemini CLI](https://ai.google.dev/) - Google's AI CLI
- [iTerm2](https://iterm2.com/) - macOS terminal emulator

---

## 📧 Contact

**Author:** DT
**Project:** Part of the Data-Wise development toolkit
**Repo:** https://github.com/Data-Wise/aiterm

---

**Status:** ✅ v0.2.1 Released
**Install:** `brew install data-wise/tap/aiterm` or `pip install aiterm-dev`
**Docs:** https://data-wise.github.io/aiterm/
