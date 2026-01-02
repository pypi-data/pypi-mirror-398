# aiterm

**Terminal optimizer CLI for AI-assisted development with Claude Code and Gemini CLI.**

[![PyPI](https://img.shields.io/pypi/v/aiterm-dev)](https://pypi.org/project/aiterm-dev/)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![CI](https://github.com/Data-Wise/aiterm/actions/workflows/test.yml/badge.svg)](https://github.com/Data-Wise/aiterm/actions/workflows/test.yml)
![Coverage](https://img.shields.io/badge/coverage-85%25-green)
[![License](https://img.shields.io/github/license/Data-Wise/aiterm)](https://github.com/Data-Wise/aiterm/blob/main/LICENSE)

---

## What It Does

**aiterm** optimizes your terminal for AI-assisted development by:

- 🎯 **Smart Context Detection** - Automatically detects project type (Python, R, Node.js, etc.)
- 🎨 **Auto Profile Switching** - Changes iTerm2 colors based on context (production = red!)
- ⚙️ **Claude Code Integration** - Manages settings, hooks, and auto-approvals
- 🔧 **OpenCode Integration** - Configure agents, MCP servers, and models
- 📊 **Status Bar** - Shows project info, git status, and session metrics
- 🚀 **Fast Setup** - Install in < 5 minutes with `uv` or Homebrew

---

## Quick Example

```bash
# Quick Install (auto-detects best method)
curl -fsSL https://raw.githubusercontent.com/Data-Wise/aiterm/main/install.sh | bash

# Or with Homebrew (macOS)
brew install data-wise/tap/aiterm

# Or with UV (fastest)
uv tool install aiterm-dev

# Check health
aiterm doctor

# Detect current project
aiterm detect

# View Claude Code settings
aiterm claude settings

# List auto-approval presets
aiterm claude approvals presets
```

---

## Context Detection

**aiterm** automatically detects 8 project types:

| Context | Icon | Profile | When Detected |
|---------|------|---------|---------------|
| Production | 🚨 | Production | `/production/`, `/prod/` paths |
| AI Session | 🤖 | AI-Session | `/claude-sessions/`, `/gemini-sessions/` |
| R Package | 📦 | R-Dev | `DESCRIPTION` file present |
| Python | 🐍 | Python-Dev | `pyproject.toml` present |
| Node.js | 📦 | Node-Dev | `package.json` present |
| Quarto | 📊 | R-Dev | `_quarto.yml` present |
| Emacs | 🔧 | Dev-Tools | `.spacemacs` file |
| Dev Tools | 🛠️ | Dev-Tools | `.git` + `scripts/` |

---

## Features

### Context Management
- Detect project type from file markers and path patterns
- Apply context to terminal (profile, title, git status)
- Short aliases: `ait detect`, `ait switch`

### Claude Code Integration
- View and backup `~/.claude/settings.json`
- Manage auto-approval permissions with 8 presets:
  - `safe-reads` - Read-only operations
  - `git-ops` - Git commands (status, diff, log)
  - `github-cli` - GitHub CLI operations
  - `python-dev` - Python tools (pytest, pip, uv)
  - `node-dev` - Node.js tools (npm, npx, bun)
  - `r-dev` - R development tools
  - `web-tools` - Web search and fetch
  - `minimal` - Basic shell commands only

### Terminal Integration (iTerm2)
- Profile switching via escape sequences
- Tab title with project name and git branch
- Status bar variables for custom displays

---

## Installation

### macOS (Recommended)

```bash
brew install data-wise/tap/aiterm
```

**Why Homebrew?**
- ✅ One-line installation
- ✅ Automatic dependency management
- ✅ Simple updates (`brew upgrade`)
- ✅ No Python setup needed

### Cross-Platform (UV)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install aiterm
uv tool install git+https://github.com/Data-Wise/aiterm
```

**Why UV?** 10-100x faster than pip, compatible with everything, no lock file confusion.

### Install with pipx

```bash
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install aiterm
pipx install git+https://github.com/Data-Wise/aiterm
```

### Verify Installation

```bash
aiterm --version
aiterm doctor
```

---

## Quick Start

### 1. Basic Usage

```bash
# Check installation
aiterm doctor

# Detect current directory
aiterm detect

# Switch to another project
cd ~/my-python-project
aiterm switch    # Applies context to iTerm2
```

### 2. Claude Code Integration

```bash
# View current settings
aiterm claude settings

# Backup settings
aiterm claude backup

# View auto-approvals
aiterm claude approvals list

# Add safe preset
aiterm claude approvals add safe-reads

# Add development presets
aiterm claude approvals add python-dev
aiterm claude approvals add git-ops
```

### 3. Use Short Alias

```bash
ait detect      # Same as: aiterm detect
ait switch      # Same as: aiterm switch
ait doctor      # Same as: aiterm doctor
```

---

## Use Cases

### For Claude Code Users

```bash
# Set up safe auto-approvals
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add python-dev

# Verify configuration
ait claude settings
```

### For Multi-Project Developers

```bash
# Navigate between projects with auto-context
cd ~/projects/my-webapp/
ait switch    # → Node-Dev profile (green)

cd ~/projects/api-service/
ait switch    # → Python-Dev profile (blue)

cd ~/production/live-site/
ait switch    # → Production profile (RED!) 🚨
```

### For R Package Developers

```bash
cd ~/r-packages/mypackage/
ait detect    # Shows: 📦 r-package → R-Dev profile

# Context includes:
# - Package name from DESCRIPTION
# - Git branch and dirty status
# - Profile colors optimized for R work
```

---

## What's New in v0.2.1

### OpenCode CLI Integration

```bash
# View configuration
ait opencode config

# Manage agents
ait opencode agents list
ait opencode agents add my-agent --model anthropic:claude-sonnet-4-20250514

# Manage MCP servers
ait opencode servers list
ait opencode servers enable filesystem

# Set models
ait opencode set-model anthropic:claude-sonnet-4-20250514
```

### CI/CD Pipeline

- GitHub Actions test workflow
- Python 3.10, 3.11, 3.12 on Ubuntu and macOS
- 155 tests passing

## Roadmap

### v0.3.0

- **Gemini CLI Integration** - Support for Google's Gemini CLI
- **Multi-Terminal Support** - Beyond iTerm2 (Kitty, Alacritty, etc.)
- **Profile Templates** - Community-contributed themes

### v1.0.0

- **Plugin System** - Extend with custom contexts
- **Web UI** - Visual configuration tool

---

## Links

- **Documentation:** [https://data-wise.github.io/aiterm](https://data-wise.github.io/aiterm)
- **Repository:** [https://github.com/Data-Wise/aiterm](https://github.com/Data-Wise/aiterm)
- **Issues:** [https://github.com/Data-Wise/aiterm/issues](https://github.com/Data-Wise/aiterm/issues)

---

## Why aiterm?

**Built for ADHD-friendly workflows:**

- ⚡ Fast commands with clear output
- 🎯 Single-purpose commands (no analysis paralysis)
- 🎨 Visual context cues (production = red!)
- 📝 Comprehensive docs with examples
- 🧪 Well-tested (155 tests, 85% coverage)

**Perfect for:**

- Claude Code power users
- Multi-project developers
- R package maintainers
- Production/staging separation
- ADHD-friendly workflows

---

## License

MIT - see [LICENSE](https://github.com/Data-Wise/aiterm/blob/main/LICENSE) for details.
