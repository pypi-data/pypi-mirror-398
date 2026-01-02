# aiterm User Guide

**Version:** 0.1.0-dev
**Last Updated:** 2025-12-21
**Reading Time:** 15 minutes
**Difficulty:** Beginner

---

## Welcome to aiterm! 🎉

This guide will help you get started with aiterm, the terminal optimizer for AI-assisted development with Claude Code and Gemini CLI.

---

## Table of Contents

1. [What is aiterm?](#what-is-aiterm)
2. [Installation](#installation)
3. [First-Time Setup](#first-time-setup)
4. [Daily Workflows](#daily-workflows)
5. [Advanced Features](#advanced-features)
6. [Tips & Tricks](#tips-tricks)
7. [FAQ](#faq)

---

## What is aiterm?

### The Problem

When working with AI coding assistants (Claude Code, Gemini CLI), switching between different project types is manual and error-prone:

**Before aiterm:**
```bash
$ cd ~/projects/r-packages/RMediation
# Manual: Change iTerm2 profile to "R-Dev"
# Manual: Set auto-approvals for R package tools
# Manual: Update tab title
# Manual: Remember which profile to use
```

**Repeat this every time you switch projects!** 😫

### The Solution

**aiterm automatically optimizes your terminal for each project:**

```bash
$ cd ~/projects/r-packages/RMediation
# ✅ Auto-detects: R package
# ✅ Auto-switches: R-Dev profile (blue theme)
# ✅ Auto-sets: Tab title "RMediation v1.0.0"
# ✅ Auto-applies: R-specific auto-approvals
```

**Just `cd` and everything is configured!** 🚀

---

### Key Features

✅ **Automatic Context Detection**
- Detects R packages, Python projects, Node.js apps, production paths, AI sessions
- 8 built-in context types, extensible for custom types

✅ **Automatic Profile Switching**
- iTerm2 profile changes based on project type
- Visual cues (colors, themes) for different contexts
- Production safety mode (red theme, extra confirmations)

✅ **Claude Code Integration**
- Auto-approval presets for different workflows
- 8 built-in presets (minimal, development, production, r-package, etc.)
- Settings management with automatic backups

✅ **ADHD-Friendly Design**
- Zero manual configuration needed
- Visual feedback for all operations
- Fast operations (< 200ms for everything)
- Clear error messages with solutions

---

## Installation

### Prerequisites

**Required:**
- Python 3.10 or higher
- iTerm2 3.4.0+ (macOS) *for full features*
- Claude Code CLI (for Claude integration)

**Optional:**
- UV package manager (10-100x faster than pip)
- Git (for version-controlled projects)

### Method 1: UV (Recommended - Fastest!)

**Install UV first:**
```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart terminal for PATH changes
```

**Install aiterm:**
```bash
# Install from GitHub
uv pip install git+https://github.com/Data-Wise/aiterm.git

# Or install from PyPI (when published)
uv pip install aiterm
```

**Time:** ~30 seconds ⚡

---

### Method 2: pip (Standard)

```bash
# Install from GitHub
pip install git+https://github.com/Data-Wise/aiterm.git

# Or install from PyPI (when published)
pip install aiterm
```

**Time:** ~2-3 minutes

---

### Method 3: From Source (Development)

```bash
# Clone repository
git clone https://github.com/Data-Wise/aiterm.git
cd aiterm

# Install in development mode
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

**Use this if:** You want to contribute or customize aiterm

---

### Verify Installation

```bash
$ aiterm --version
aiterm version 0.1.0-dev

$ aiterm doctor
╔════════════════════════════════════════════════════╗
║  aiterm Installation Check                         ║
╚════════════════════════════════════════════════════╝

✅ Python: 3.11.5
✅ Terminal: iTerm2 (Build 3.5.0)
✅ Claude Code: 0.2.0 (~/.claude/)
✅ Settings: ~/.aiterm/config.json

System Status: All checks passed!
```

**If any checks fail:** See [Troubleshooting Guide](../troubleshooting/AITERM-TROUBLESHOOTING.md)

---

## First-Time Setup

### Step 1: Run Doctor Check

```bash
aiterm doctor
```

This verifies:
- ✅ Python version (≥ 3.10)
- ✅ Terminal type (iTerm2 preferred)
- ✅ Claude Code installation
- ✅ Configuration files

**Example - All Good:**
```
✅ Python: 3.11.5
✅ Terminal: iTerm2 (Build 3.5.0)
✅ Claude Code: 0.2.0
✅ Settings: ~/.aiterm/config.json

System Status: All checks passed!
```

**Example - Need iTerm2:**
```
✅ Python: 3.11.5
❌ Terminal: Terminal.app (unsupported)
   → iTerm2 3.4.0+ required for full features
   → Download: https://iterm2.com
✅ Claude Code: 0.2.0
✅ Settings: ~/.aiterm/config.json

System Status: 1 check failed
```

---

### Step 2: Test Context Detection

Navigate to a project and test detection:

```bash
$ cd ~/projects/r-packages/RMediation
$ aiterm detect

╔════════════════════════════════════════════════════╗
║  Context Detection                                 ║
╚════════════════════════════════════════════════════╝

📁 Path: /Users/dt/projects/r-packages/RMediation
🎯 Type: R Package
📦 Package: RMediation
📋 Profile: R-Dev
🎨 Title: RMediation v1.0.0

Detected: R package development environment
```

**What it detects:**
- DESCRIPTION file → R package
- pyproject.toml → Python project
- package.json → Node.js project
- */production/* path → Production environment
- */claude-sessions/* → AI coding session
- And more! (See [Context Types](#context-types))

---

### Step 3: Explore Available Profiles

```bash
$ aiterm profile list

╔════════════════════════════════════════════════════╗
║  Available Profiles                                ║
╚════════════════════════════════════════════════════╝

📋 R-Dev
   → For R package development
   🎨 Blue theme, white text
   🔧 Optimized for ESS/Claude Code

📋 Python-Dev
   → For Python projects
   🎨 Green theme, white text
   🔧 Optimized for pytest/Claude Code

📋 Production
   → For production deployments (SAFE MODE)
   🎨 Red theme, black text
   ⚠️  Read-only, extra confirmations

📋 AI-Session
   → For Claude Code/Gemini sessions
   🎨 Purple theme, white text
   🔧 Optimized for AI coding workflows

📋 Default
   → Standard profile
   🎨 Default iTerm2 theme
```

---

### Step 4: (Optional) Set Auto-Approvals

If you use Claude Code, configure auto-approvals:

```bash
$ aiterm claude approvals list

╔════════════════════════════════════════════════════╗
║  Auto-Approval Presets                             ║
╚════════════════════════════════════════════════════╝

⚡ minimal (15 tools)
   → Essential operations only

🚀 development (45 tools)
   → Full development workflow

🔒 production (20 tools)
   → Production-safe operations

🎯 r-package (35 tools)
   → R package development

...
```

**Apply a preset:**
```bash
$ aiterm claude approvals set r-package

✅ Applied preset: r-package
📋 Approved tools: 35
📝 Updated: ~/.claude/settings.json
```

**Done!** aiterm is now configured.

---

## Daily Workflows

### Workflow 1: R Package Development

**Scenario:** You're developing an R package

**Before aiterm:**
```bash
$ cd ~/projects/r-packages/RMediation
# 1. Manually change iTerm2 profile to "R-Dev"
# 2. Manually update tab title
# 3. Manually set Claude Code auto-approvals
# 4. Remember R-specific commands
```

**With aiterm:**
```bash
$ cd ~/projects/r-packages/RMediation
# ✅ Auto-switched to R-Dev profile (blue theme)
# ✅ Title: "RMediation v1.0.0"
# ✅ Status bar: "R PKG | RMediation"
# ✅ Claude Code auto-approvals: R package tools
```

**Visual change:**
- Background: Dark blue
- Foreground: White
- Accent: Light blue
- Tab title: "RMediation v1.0.0"

**What you can do:**
```bash
# All R development commands work
R CMD check .
R CMD build .
devtools::test()
# Claude Code knows R package context
```

---

### Workflow 2: Python Development

**Scenario:** You're working on a Python project

**Before:**
```bash
$ cd ~/projects/python/my-api
# Manually configure everything...
```

**With aiterm:**
```bash
$ cd ~/projects/python/my-api
# ✅ Auto-switched to Python-Dev profile (green theme)
# ✅ Title: "my-api"
# ✅ Status bar: "PYTHON | my-api"
```

**Visual change:**
- Background: Dark green
- Foreground: White
- Tab title: "my-api"

**What you can do:**
```bash
pytest
python -m mypy .
# Claude Code knows Python context
```

---

### Workflow 3: Production Deployment (SAFE MODE)

**Scenario:** You need to deploy to production

**Critical:** Production mode has EXTRA SAFETY

**Before:**
```bash
$ cd ~/production/api-server
# ⚠️ No visual indicator you're in production!
# ⚠️ Easy to run destructive commands by accident
```

**With aiterm:**
```bash
$ cd ~/production/api-server
# ✅ Auto-switched to Production profile (RED theme)
# ✅ Title: "⚠️ PROD: api-server"
# ✅ Status bar: "⚠️ PRODUCTION"
# ✅ Extra confirmations enabled
```

**Visual change:**
- **Background: RED** 🔴 (impossible to miss!)
- Foreground: Black
- Tab title: "⚠️ PROD: api-server"
- Every destructive command requires confirmation

**Safety features:**
```bash
$ rm important-file.txt
⚠️  PRODUCTION MODE - Are you sure? [y/N]

$ git push --force
⚠️  PRODUCTION MODE - Force push detected. Confirm: [y/N]
```

**Use this for:**
- Production servers
- Deployments
- Database migrations
- Any high-risk environment

---

### Workflow 4: AI Coding Session

**Scenario:** You're doing intensive AI-assisted coding

**Before:**
```bash
$ cd ~/claude-sessions/refactor-2025
# Generic terminal setup
# Have to manually configure Claude Code
```

**With aiterm:**
```bash
$ cd ~/claude-sessions/refactor-2025
# ✅ Auto-switched to AI-Session profile (purple theme)
# ✅ Title: "Claude Session: refactor-2025"
# ✅ Maximum auto-approvals (50 tools)
# ✅ Optimized for rapid iteration
```

**Visual change:**
- Background: Dark purple
- Foreground: White
- Tab title: "Claude Session: refactor-2025"

**What's different:**
- Broadest auto-approvals (50 tools)
- Fast iteration focus
- Optimized for Claude Code workflows

---

### Workflow 5: Switching Between Projects

**Scenario:** You work on multiple projects daily

**Example session:**
```bash
# Morning: R package work
$ cd ~/projects/r-packages/RMediation
# → R-Dev profile (blue)

# Afternoon: Python API
$ cd ~/projects/python/api-server
# → Python-Dev profile (green)

# Evening: Production hotfix
$ cd ~/production/api-server
# → Production profile (RED, safe mode)

# Night: AI coding session
$ cd ~/claude-sessions/new-feature
# → AI-Session profile (purple)
```

**Each `cd` automatically:**
- ✅ Detects context
- ✅ Switches profile
- ✅ Updates title
- ✅ Sets appropriate auto-approvals
- ✅ Adjusts safety settings

**No manual steps needed!**

---

## Advanced Features

### Context Types

aiterm detects 8 context types (priority order):

| Priority | Type | Detection | Profile | Use Case |
|----------|------|-----------|---------|----------|
| 1 | Production | `*/production/*` or `*/prod/*` | Production | Deployments, servers |
| 2 | AI Session | `*/claude-sessions/*` or `*/gemini-sessions/*` | AI-Session | AI coding |
| 3 | R Package | `DESCRIPTION` + `R/` | R-Dev | R development |
| 4 | Python | `pyproject.toml` or `setup.py` | Python-Dev | Python development |
| 5 | Node.js | `package.json` | Node-Dev | JavaScript/TypeScript |
| 6 | Quarto | `_quarto.yml` | R-Dev | Quarto documents |
| 7 | MCP Server | `mcp-server/` directory | AI-Session | MCP development |
| 8 | Dev Tools | `.git/` + `scripts/` | Dev-Tools | Tool development |
| 9 | Default | (no match) | Default | Generic work |

**Priority matters:** If a directory matches multiple types, the highest priority wins.

**Example:**
```bash
$ cd ~/production/r-api
# Contains both */production/* AND DESCRIPTION
# → Production wins (priority 1 > priority 3)
# → Production profile applied (safety first!)
```

---

### Manual Profile Switching

**When automatic detection isn't enough:**

```bash
# Switch to specific profile
$ aiterm profile switch R-Dev
✅ Switched to profile: R-Dev

# Switch with custom title
$ aiterm profile switch Python-Dev --title "API Server"
✅ Switched to profile: Python-Dev
🎨 Title: API Server
```

**Use cases:**
- Override automatic detection
- Work in non-standard directory structure
- Temporary profile change
- Testing different profiles

---

### Disabling Auto-Switching

**If you prefer manual control:**

```bash
# Disable automatic switching
export AITERM_AUTO_SWITCH=0

# Add to ~/.zshrc or ~/.bashrc for permanent
echo 'export AITERM_AUTO_SWITCH=0' >> ~/.zshrc
```

**Then manually switch:**
```bash
aiterm profile switch PROFILE_NAME
```

---

### Claude Code Auto-Approval Presets

**8 Built-in Presets:**

| Preset | Tools | Use Case |
|--------|-------|----------|
| `minimal` | 15 | Essential read operations only |
| `development` | 45 | Full development workflow |
| `production` | 20 | Production-safe (read-only) |
| `r-package` | 35 | R package development |
| `python-dev` | 40 | Python development |
| `teaching` | 30 | Teaching/course development |
| `research` | 35 | Research/manuscript writing |
| `ai-session` | 50 | AI coding sessions (broadest) |

**Applying presets:**

```bash
# Apply preset
$ aiterm claude approvals set r-package
✅ Applied preset: r-package (35 tools)

# Merge with existing approvals
$ aiterm claude approvals set development --merge
✅ Merged preset: development
📋 Total approved: 58 tools
```

**What gets approved:**

**r-package preset example:**
```
✅ Bash(git *)          # All git commands
✅ Bash(R CMD *)        # R CMD build/check/install
✅ Bash(Rscript:*)      # Run R scripts
✅ Bash(pytest:*)       # Run tests
✅ Read(**)             # Read any file
✅ Write(**)            # Write any file
✅ Edit(**)             # Edit any file
... (28 more)
```

---

### Checking Current Settings

```bash
$ aiterm claude settings show

╔════════════════════════════════════════════════════╗
║  Claude Code Settings                              ║
╚════════════════════════════════════════════════════╝

📁 Settings: ~/.claude/settings.json
📊 File size: 2.4 KB
🕐 Modified: 2025-12-21 10:30:45

Auto-Approvals:
  ✅ 35 tools approved
  📋 Active preset: r-package

Status Line:
  ✅ Configured: /bin/bash ~/.claude/statusline-p10k.sh
  ⏱️  Update interval: 300ms

MCP Servers:
  ✅ statistical-research (14 tools)
  ✅ shell (5 tools)
  ✅ project-refactor (4 tools)
```

---

## Tips & Tricks

### Tip 1: Use `detect` to Preview

Before relying on automatic switching, preview what aiterm detects:

```bash
$ cd ~/my-project
$ aiterm detect

📁 Path: /Users/dt/my-project
🎯 Type: Python
📋 Profile: Python-Dev
🎨 Title: my-project
```

**Then decide:**
- Automatic switching correct? → Let it happen
- Need different profile? → Manual switch
- Context not detected? → See Troubleshooting

---

### Tip 2: Production Safety Workflow

**Always check before production work:**

```bash
$ aiterm detect
# Should show:
# 🎯 Type: Production
# ⚠️  Profile: Production (safe mode)

# If NOT showing Production:
$ aiterm profile switch Production
```

**Visual confirmation:**
- Background MUST be RED 🔴
- Title MUST have ⚠️ symbol
- Every command should feel slower (confirmations)

---

### Tip 3: Rapid Context Switching

**Work on multiple projects:**

```bash
# Use shell aliases for common projects
alias rmed='cd ~/projects/r-packages/RMediation'
alias api='cd ~/projects/python/api-server'
alias prod='cd ~/production/api-server'

# Then just:
$ rmed    # → R-Dev profile
$ api     # → Python-Dev profile
$ prod    # → Production profile (RED!)
```

**aiterm handles the rest automatically!**

---

### Tip 4: Custom Context Detection (Advanced)

**Coming in Phase 2:** Custom detector plugins

**Preview:**
```python
# ~/.aiterm/custom_detectors.py
from aiterm.context import ContextDetector, Context

class MyProjectDetector(ContextDetector):
    def detect(self, path: str) -> Context | None:
        if self._has_file(path, ".myproject"):
            return Context(
                type="my-project",
                profile="My-Profile",
                title="My Project",
                path=path
            )
        return None
```

---

### Tip 5: Backup and Recovery

**aiterm automatically backs up Claude Code settings:**

```bash
# Backups location
ls ~/.claude/settings.json.backup.*

# Restore from backup
cp ~/.claude/settings.json.backup.20251221_103045 \
   ~/.claude/settings.json
```

**Backups created when:**
- Applying auto-approval presets
- Updating settings
- Before any destructive operation

**Retention:** Last 5 backups

---

## FAQ

### Q: Does aiterm work outside iTerm2?

**A:** Partial support. Context detection works everywhere, but profile switching requires iTerm2.

**Supported features without iTerm2:**
- ✅ Context detection
- ✅ Auto-approval management
- ✅ Settings management
- ❌ Profile switching (terminal-specific)
- ❌ Title updates (terminal-specific)

**Planned:** Wezterm, Alacritty, Kitty support (Phase 3)

---

### Q: Will automatic switching slow down my terminal?

**A:** No! aiterm is extremely fast:
- Context detection: < 50ms
- Profile switching: < 150ms
- Total overhead: < 200ms per `cd`

**You won't notice any delay.**

---

### Q: Can I customize profiles?

**A:** Yes! Edit `~/.aiterm/config.json`:

```json
{
  "profiles": {
    "My-Custom": {
      "theme": "my-theme",
      "triggers": [".myproject"],
      "auto_approvals": ["Bash(git *)", "Read(**)"]
    }
  }
}
```

**Coming in Phase 2:** Profile creation wizard

---

### Q: What if I work on production AND development in the same path?

**A:** Production always wins (priority 1).

**Example:**
```bash
$ cd ~/production/my-r-package
# Contains: */production/* AND DESCRIPTION
# → Production profile applied (safety first!)
```

**Override if needed:**
```bash
$ aiterm profile switch R-Dev
# Manually switch to R-Dev for development work
# → But be careful! You're in production path
```

---

### Q: How do I uninstall aiterm?

**With UV:**
```bash
uv pip uninstall aiterm
```

**With pip:**
```bash
pip uninstall aiterm
```

**Remove config files (optional):**
```bash
rm -rf ~/.aiterm
```

**Note:** Claude Code settings are NOT removed (safe to keep)

---

### Q: Can I use aiterm with Gemini CLI?

**A:** Basic support now, full integration planned for Phase 2.

**Currently works:**
- ✅ Context detection
- ✅ Profile switching
- ✅ AI-Session detection (gemini-sessions/ paths)

**Planned:**
- Gemini-specific auto-approvals
- Gemini settings management
- Gemini MCP integration

---

### Q: What's the difference between presets?

**Quick comparison:**

| Feature | minimal | development | production | ai-session |
|---------|---------|-------------|-----------|------------|
| Read operations | ✅ | ✅ | ✅ | ✅ |
| Write operations | ❌ | ✅ | ❌ | ✅ |
| Git commands | Basic | All | Read-only | All |
| Testing | ❌ | ✅ | ❌ | ✅ |
| Package management | ❌ | ✅ | ❌ | ✅ |
| Destructive operations | ❌ | ⚠️ Some | ❌ | ⚠️ Some |

**Choose:**
- `minimal` - Untrusted environments
- `development` - Daily development
- `production` - Production systems (safest)
- `ai-session` - Rapid AI-assisted coding

---

### Q: Can I see what changed in my settings?

**A:** Yes! Compare with backup:

```bash
# Show current settings
aiterm claude settings show

# Compare with last backup
diff ~/.claude/settings.json \
     ~/.claude/settings.json.backup.20251221_103045
```

---

### Q: Does aiterm modify my existing iTerm2 profiles?

**A:** No! aiterm uses your existing profiles by name.

**What aiterm does:**
- Reads profile names from iTerm2
- Switches between profiles by name
- Does NOT modify profile settings

**What you control:**
- Profile colors, fonts, appearance (iTerm2 settings)
- Profile creation (iTerm2)
- Profile deletion (iTerm2)

**aiterm only switches between profiles you've created.**

---

## Next Steps

### Learn More

- **[API Documentation](../api/AITERM-API.md)** - Detailed CLI and Python API
- **[Architecture](../architecture/AITERM-ARCHITECTURE.md)** - How aiterm works internally
- **[Integration Guide](AITERM-INTEGRATION.md)** - Custom contexts and backends
- **[Troubleshooting](../troubleshooting/AITERM-TROUBLESHOOTING.md)** - Solve common issues

### Get Help

- **GitHub Issues:** https://github.com/Data-Wise/aiterm/issues
- **Discussions:** https://github.com/Data-Wise/aiterm/discussions
- **Documentation:** https://Data-Wise.github.io/aiterm/

### Contribute

- **Source Code:** https://github.com/Data-Wise/aiterm
- **Development Guide:** Coming in Phase 2
- **Plugin System:** Coming in Phase 2

---

## Congratulations! 🎉

You're now ready to use aiterm for optimized AI-assisted development!

**Remember:**
- ✅ Just `cd` to projects - aiterm handles the rest
- ✅ Production mode uses RED theme for safety
- ✅ Auto-approvals save time in Claude Code
- ✅ Manual override always available

**Happy coding!** 🚀

---

**Last Updated:** 2025-12-21
**Maintained By:** aiterm Development Team
