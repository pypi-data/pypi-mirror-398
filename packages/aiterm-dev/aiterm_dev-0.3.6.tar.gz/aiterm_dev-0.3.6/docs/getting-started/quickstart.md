# Quick Start

Get up and running with **aiterm** in 2 minutes.

---

## Install (Choose Your Method)

### macOS (Recommended)

```bash
# One command installation
brew install data-wise/tap/aiterm
```

### All Platforms

```bash
# Install with UV (fastest)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install git+https://github.com/Data-Wise/aiterm
```

---

## Verify Installation

```bash
# Check version
aiterm --version
# or use short alias
ait --version

# Run health check
ait doctor
```

Expected output:
```
✅ Terminal: iTerm.app
✅ Shell: /bin/zsh
✅ Python: 3.12.0
✅ aiterm: 0.1.0

All systems go!
```

---

## Try It Out

### 1. Detect Your Context

```bash
# Navigate to any project
cd ~/projects/my-r-package

# Detect project type
ait detect
```

Output:
```
Context: R-Pkg 📦
Profile: R-Dev (blue theme)
Git: main (clean)
```

### 2. Check Claude Code Settings

```bash
# View current settings
ait claude settings

# List available auto-approval presets
ait claude approvals presets
```

### 3. Add Auto-Approvals

```bash
# Add safe file reading permissions
ait claude approvals preset --name safe-reads

# Add git operations permissions
ait claude approvals preset --name git-ops
```

---

## What Happens

### Context Detection (8 Types)

| When you `cd` to... | Context | Icon | Profile |
|---------------------|---------|------|---------|
| R package (DESCRIPTION) | R-Pkg | 📦 | R-Dev (blue) |
| Python project (pyproject.toml) | Python | 🐍 | Python-Dev (green) |
| Node project (package.json) | Node | 📦 | Node-Dev (dark) |
| Quarto project (_quarto.yml) | Quarto | 📊 | R-Dev (blue) |
| MCP server (mcp-server/) | AI-Session | 🤖 | AI-Session (purple) |
| Production path (*/production/*) | Production | 🚨 | Production (red) |
| Dev tools (.git + scripts/) | Dev-Tools | 🔧 | Dev-Tools (amber) |
| Claude sessions (*/claude-sessions/*) | AI-Session | 🤖 | AI-Session (purple) |

### Auto-Approvals (8 Presets)

After adding presets, Claude Code will auto-approve:

- **safe-reads**: Read files (cat, ls, grep)
- **git-ops**: Git commands (status, diff, log, add, commit, push)
- **github-cli**: GitHub CLI (gh pr, gh issue)
- **python-dev**: Python tools (pytest, black, ruff)
- **node-dev**: Node tools (npm, npx)
- **r-dev**: R tools (Rscript, R CMD)
- **web-tools**: Web search, fetch
- **minimal**: Only read + git status

---

## Common Commands

```bash
# Health check
ait doctor

# Detect current context
ait detect

# Switch profile (manual override)
ait switch

# View all profiles
ait profile list

# Claude Code integration
ait claude settings           # View settings
ait claude backup             # Backup settings
ait claude approvals list     # Show current approvals
ait claude approvals presets  # List available presets
```

---

## Next Steps

### Learn More
- 📖 **[Full Installation Guide](installation.md)** - All installation methods
- 🎯 **[Context Detection](../guide/context-detection.md)** - How detection works
- ⚙️ **[Claude Integration](../guide/claude-integration.md)** - Auto-approvals explained
- 🎨 **[Profiles](../guide/profiles.md)** - Customize colors

### Workflows
- 📊 **[Common Workflows](../guide/workflows.md)** - Real-world examples
- 🔧 **[Status Bar](../guide/status-bar.md)** - Customize your status bar

### Reference
- 💻 **[Command Reference](../reference/commands.md)** - All commands
- 🐛 **[Troubleshooting](../reference/troubleshooting.md)** - Common issues

---

## Update

Keep aiterm up to date:

```bash
# Homebrew
brew upgrade aiterm

# UV
uv tool upgrade aiterm

# pipx
pipx upgrade aiterm
```

---

## Getting Help

- **Documentation:** [https://data-wise.github.io/aiterm](https://data-wise.github.io/aiterm)
- **Issues:** [GitHub Issues](https://github.com/Data-Wise/aiterm/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Data-Wise/aiterm/discussions)
