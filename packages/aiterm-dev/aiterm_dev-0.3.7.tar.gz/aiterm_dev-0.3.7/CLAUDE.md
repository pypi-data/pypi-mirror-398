# CLAUDE.md

This file provides guidance to Claude Code when working with the aiterm project.

## Project Overview

**aiterm** - AI Terminal Optimizer CLI for Claude Code, OpenCode, and Gemini CLI workflows.

**What it does:**
- Optimizes terminal setup (iTerm2 primarily) for AI coding workflows
- Manages terminal profiles, context detection, and visual customization
- Integrates with Claude Code CLI (hooks, commands, auto-approvals, MCP servers)
- **NEW: OpenCode configuration management** (models, agents, MCP servers)
- Supports Gemini CLI integration
- Provides workflow templates for different dev contexts

**Target Users:**
- Primary: DT (power user, R developer, statistician, ADHD-friendly workflows)
- Secondary: Public release (developers using Claude Code/Gemini CLI/OpenCode)

**Tech Stack:**
- **Language:** Python 3.10+
- **CLI Framework:** Typer (modern CLI with type hints)
- **Terminal:** Rich (beautiful terminal output)
- **Prompts:** Questionary (interactive prompts)
- **Testing:** pytest (135 tests, 85%+ coverage)
- **Distribution:** Homebrew (macOS primary), pip/PyPI (cross-platform)

---

## Project Status: v0.3.6 ✅ RELEASED

**Current Version:** v0.3.6 (Dec 27, 2025)

**v0.3.6 Release (Dec 27, 2025):**
- [x] **curl installer:** `install.sh` with smart auto-detection (uv/pipx/brew/pip)
- [x] **Documentation:** Comprehensive updates to commands reference and guides

**v0.3.5 Release (Dec 27, 2025):**
- [x] **Dogfooding tests:** Via Craft orchestrator v2.1
  - `ait hello` - Diagnostic greeting command
  - `ait goodbye` - Farewell command
  - `ait info` - System diagnostics
  - Enhanced `--version` output

**v0.3.1-0.3.4 Releases (Dec 26, 2025):**
- [x] **Session Prune:** `ait sessions prune` for stale session cleanup
- [x] **IDE Integrations:** VS Code, Cursor, Zed, Positron, Windsurf support
- [x] **Session Coordination:** Hook-based session tracking & conflict detection

**Next Phase:** v0.4.0 - Workflow Automation & Craft Integration
- [ ] **Phase 1:** Workflow Templates (`ait recipes list/show/apply`)
- [ ] **Phase 2:** Craft Plugin Management (`ait craft install/sync/run`)
- [ ] **Phase 3:** Session-Aware Workflows

**Integration with Craft plugin v1.6.0-dev:**
- 58 commands available for workflow recipes
- 15 skills for intelligent task routing
- Mode system (default, debug, optimize, release)
- Distribution commands (homebrew, curl-install)
- **NEW:** Docs workflow commands (update, feature, done, site)

**See:**
- `V0.4.0-PLAN.md` - Full v0.4.0 implementation plan
- `CHANGELOG.md` - Full release history
- `.STATUS` - Current progress and session history

---

## v0.1.0 Achievements ✅

**Completed (Dec 2024):**
- [x] UV build system and virtual environment
- [x] Python project structure (hatchling, src/ layout)
- [x] Core CLI commands (doctor, detect, switch)
- [x] Terminal integration (iTerm2 escape sequences)
- [x] Claude Code settings management
- [x] Auto-approval presets (8 presets)
- [x] Testing & documentation (51 tests, 83% coverage)
- [x] Basic docs (2,647 lines, deployed to GitHub Pages)
- [x] Repository renamed to "aiterm"
- [x] **Homebrew distribution** (private tap: data-wise/tap)

**Installation:**
```bash
# Quick Install (auto-detects best method)
curl -fsSL https://raw.githubusercontent.com/Data-Wise/aiterm/main/install.sh | bash

# macOS (Homebrew)
brew install data-wise/tap/aiterm

# Cross-platform (PyPI)
pip install aiterm-dev

# Using uv (fastest)
uv tool install aiterm-dev

# Using pipx
pipx install aiterm-dev
```

**Links:**
- **Repo:** https://github.com/Data-Wise/aiterm
- **Docs:** https://Data-Wise.github.io/aiterm/
- **PyPI:** https://pypi.org/project/aiterm-dev/
- **Homebrew Tap:** https://github.com/Data-Wise/homebrew-tap
- **Status:** v0.3.5 released, v0.4.0 in planning

---

## Next: Phase 1 Implementation (After Docs)

**After Phase 0 documentation complete:**
- Implement `rforge:plan` (main ideation tool)
- Implement `rforge:plan:quick-fix` (fast iterations)
- 2 weeks to working MVP
- Validate pattern with real usage

---

## Quick Reference

### Shell Aliases

```bash
ait          # → aiterm (main CLI via UV symlink)
oc           # → opencode (OpenCode CLI)
```

**Location:** `~/.config/zsh/.zshrc`

### Common Commands

```bash
# Essential
ait doctor                       # Check installation
ait detect                       # Show project context
ait switch                       # Apply context to terminal

# Claude Code
ait claude settings              # View settings
ait claude backup                # Backup settings
ait claude approvals list        # Show auto-approvals
ait claude approvals add safe    # Apply safe preset

# MCP Servers
ait mcp list                     # List configured servers
ait mcp test filesystem          # Test specific server
ait mcp validate                 # Check configuration

# Session Coordination (NEW!)
ait sessions live                # Show active Claude Code sessions
ait sessions conflicts           # Detect parallel session conflicts
ait sessions history             # Browse archived sessions

# Development
python -m pytest                 # Run tests
```

### Quick Help Docs

| Doc | Purpose |
|-----|---------|
| `docs/REFCARD.md` | One-page quick reference |
| `docs/QUICK-START.md` | 30-second setup guide |
| `ait --help` | All CLI commands |
| `ait <cmd> --help` | Command-specific help |

### Key Files

- `IDEAS.md` - Full feature brainstorm
- `ROADMAP.md` - Week 1 day-by-day plan
- `ARCHITECTURE.md` - Technical design
- `.STATUS` - Current progress
- `zsh/` and `scripts/` - Existing code (reference)
- `MCP-MIGRATION-PLAN.md` - Complete MCP organization plan (2025-12-19)

---

## Integration with DT's Existing Setup

**Existing Tools:**
- `~/.claude/statusline-p10k.sh` - Status bar (will integrate)
- `~/.claude/settings.json` - Claude Code config (will manage)
- `~/.config/zsh/functions.zsh` - Shell functions (will complement)

**Workflow Commands:**
- `/recap`, `/next`, `/focus` - ADHD-friendly workflow (will enhance)
- `/workflow:done` - Session completion with documentation automation (NEW!)
- `work`, `finish`, `dash`, `pp` - Project management (will integrate with context)

**MCP Servers (Now Organized!):**
- **Location:** `~/projects/dev-tools/mcp-servers/` (unified, 2025-12-19)
- **Servers:** statistical-research, shell, project-refactor
- **ZSH Tools:** `mcp-list`, `mcp-cd`, `mcp-test`, `mcp-status` (+ 6 more)
- **Aliases:** `ml` (list), `mc` (cd), `mcps` (status), `mcpp` (picker)
- **Index:** `~/projects/dev-tools/_MCP_SERVERS.md`
- **Config:** `~/.claude/settings.json`, `claude-mcp/MCP_SERVER_CONFIG.json`
- **Planned for aiterm v0.2.0:** `aiterm mcp list|test|validate`

**@smart Feature (NEW!):**
- UserPromptSubmit hook: `~/.claude/hooks/prompt-optimizer.sh`
- Optimizes prompts with project context
- Interactive menu: Submit/Revise/Delegate/Cancel
- Docs: `~/.claude/PROMPT-OPTIMIZER-GUIDE.md`

---

## OpenCode Integration (NEW - Dec 25, 2025)

**Module:** `src/aiterm/opencode/`
**Tests:** 55 tests in `tests/test_opencode_config.py`
**Config:** `~/.config/opencode/config.json`

### Current Config (Option A - Lean & Fast)
```json
{
  "model": "anthropic/claude-sonnet-4-5",
  "small_model": "anthropic/claude-haiku-4-5",
  "tui": { "scroll_acceleration": { "enabled": true } },
  "mcp": {
    "filesystem": { "enabled": true },
    "memory": { "enabled": true }
  }
}
```

### Python API
```python
from aiterm.opencode import load_config, validate_config, backup_config

# Load and validate
config = load_config()
valid, errors = validate_config()

# Check properties
print(config.enabled_servers)  # ['filesystem', 'memory']
print(config.has_scroll_acceleration)  # True
```

### Enhancement Roadmap
- **Option A (Applied):** Explicit models, scroll acceleration, lean MCP
- **Option B (Planned):** Custom agents, tool permissions, CLAUDE.md loading
- **Option C (Future):** Keybinds, custom commands, GitHub MCP

**See:** `OPENCODE-OPTIMIZATION-PLAN.md` for full details.

---

## Session Coordination (NEW - Dec 26, 2025)

**Hooks:** `~/.claude/hooks/session-register.sh`, `~/.claude/hooks/session-cleanup.sh`
**Data:** `~/.claude/sessions/active/`, `~/.claude/sessions/history/`

### How It Works

```
┌─────────────────┐     SessionStart      ┌─────────────────┐
│  Claude Code    │────────────────────►  │  session-       │
│  starts         │                       │  register.sh    │
└─────────────────┘                       └────────┬────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │ active/{id}.json│
                                          │ - project path  │
                                          │ - git branch    │
                                          │ - started time  │
                                          └─────────────────┘
                                                   │
┌─────────────────┐      Stop             ┌────────▼────────┐
│  Claude Code    │────────────────────►  │  session-       │
│  exits          │                       │  cleanup.sh     │
└─────────────────┘                       └────────┬────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │ history/        │
                                          │  2025-12-26/    │
                                          │   {id}.json     │
                                          └─────────────────┘
```

### CLI Commands

```bash
# Show active sessions across all projects
ait sessions live

# Show current session for this directory
ait sessions current

# Set task description for current session
ait sessions task "Implementing feature X"

# Detect same-project conflicts (parallel sessions)
ait sessions conflicts

# Browse session history by date
ait sessions history
ait sessions history --date 2025-12-26
```

### Conflict Detection

When you start Claude Code in a project that already has an active session:

```json
{
  "status": "warning",
  "message": "1 other session(s) active in this project",
  "sessions": ["1766786246-71374"],
  "hint": "Use 'ait sessions live' to see details"
}
```

### Session Manifest Format

```json
{
  "session_id": "1766786256-71941",
  "project": "aiterm",
  "path": "/Users/dt/projects/dev-tools/aiterm",
  "started": "2025-12-26T16:57:37-0600",
  "git_branch": "dev",
  "git_dirty": true,
  "pid": 71941,
  "task": null
}
```

---

## Shell Integration Standards (flow-cli)

When modifying `.zshrc` or shell configuration, follow these standards from flow-cli:

### Configuration Location
```
~/.config/zsh/           # Main ZSH config directory (XDG compliant)
├── .zshrc               # Main config file
├── .zshenv              # Sets ZDOTDIR
├── functions/           # Function libraries (separate files)
└── .zsh_plugins.txt     # Antidote plugin list
```

### ZDOTDIR Pattern (Preferred)
```bash
# In ~/.zshenv - redirect ZSH to ~/.config/zsh
echo 'export ZDOTDIR="$HOME/.config/zsh"' >> ~/.zshenv
```

### Installation Standards
```bash
# 1. Check if already installed (idempotent)
if grep -q "aiterm" "$ZSHRC"; then
    echo "Already installed"
fi

# 2. Create timestamped backup
backup="$ZSHRC.backup.$(date +%Y%m%d%H%M%S)"
cp "$ZSHRC" "$backup"

# 3. Use heredoc with markers
cat >> "$ZSHRC" << 'EOF'

# ============================================
# AITERM SHELL INTEGRATION
# ============================================
source ~/.config/aiterm/shell.zsh

EOF

# 4. Uninstall: grep -v pattern
grep -v "AITERM" "$ZSHRC" > "${ZSHRC}.tmp" && mv "${ZSHRC}.tmp" "$ZSHRC"
```

### Key Principles
| Concern | Standard |
|---------|----------|
| Location | `~/.config/zsh/` (XDG compliant) |
| Backups | Timestamped `.backup.YYYYMMDDHHMMSS` |
| Idempotent | Check with `grep -q` before adding |
| Markers | Comment blocks with project name |
| Functions | Separate files in `functions/` dir |
| Reload | `source ~/.zshrc` or `reload` alias |

---

## Current Limitations & Next Steps

### MVP Limitations (v0.1.0)
- iTerm2 only (no multi-terminal yet)
- Basic Claude Code integration (settings only, no hooks/commands managed)
- No Gemini integration yet
- No web UI
- Manual installation

### Planned for v0.2.0 (Phase 2)
- Hook management system
- Command template library
- **MCP server integration** (foundation ready: zsh-configuration/zsh/functions/mcp-utils.zsh)
  - `aiterm mcp list` - Show all configured servers
  - `aiterm mcp status` - Check server health
  - `aiterm mcp test <server>` - Validate server runs
  - `aiterm mcp validate` - Check configs are valid
- Advanced status bar builder
- **Workflow & Documentation Automation** (Phase 2.6)
  - Enhanced `/workflow:done` with documentation detection
  - Automatic CHANGELOG, CLAUDE.md, mkdocs.yml updates
  - 3-phase roadmap: Detection → Auto-updates → AI generation

---

## Key Constraints

1. **ADHD-Friendly:** Fast commands, clear output, no analysis paralysis
2. **Week 1 MVP:** Ship v0.1.0 in 7 days, DT using daily
3. **No Regressions:** Must work as well as v2.5.0 zsh version
4. **Python 3.10+:** Modern Python, type hints, async-ready
5. **Medium Integration:** Active control, not just config files

---

## Project Standards

**See:** `STANDARDS-SUMMARY.md` - Comprehensive standards for aiterm project

**Based on:** zsh-configuration standards (`~/projects/dev-tools/zsh-configuration/standards/`)

**Key Standards:**
- **Project Organization:** .STATUS file, directory structure, universal files
- **Documentation:** QUICK-START, REFCARD, TUTORIAL templates (ADHD-friendly)
- **Commit Messages:** Conventional commits (type(scope): subject)
- **Testing:** 80%+ coverage goal, arrange-act-assert pattern
- **Development:** Branch strategy, pre-commit checklist, release process

**Quick Access:**
```bash
# View all standards
cat STANDARDS-SUMMARY.md

# Reference templates
cat standards/adhd/QUICK-START-TEMPLATE.md
cat standards/adhd/REFCARD-TEMPLATE.md
cat standards/adhd/TUTORIAL-TEMPLATE.md

# Code standards
cat standards/code/COMMIT-MESSAGES.md
```

---

## Detailed Documentation

Detailed docs have been split into focused rule files in `.claude/rules/`:

- **architecture.md** - System architecture, file structure, design principles
- **migration.md** - Code migration from v2.5.0 (zsh → Python)
- **development.md** - Development workflow, testing, adding commands

These files load automatically when working in relevant paths.

---

## Success Criteria

### MVP (v0.1.0) ✅ COMPLETE
- [x] Installs in <5 minutes (with UV: < 2 minutes!)
- [x] Context switching works (8 types)
- [x] Claude Code auto-approvals manageable (8 presets)
- [x] Tests pass (51/51, 83% coverage)
- [x] Comprehensive documentation deployed
- [ ] `aiterm init` wizard (deferred to v0.2.0)
- [ ] DT uses daily for 1 week (testing in progress)

### Long-term (v1.0.0)
- [ ] Multi-terminal support
- [ ] 10+ external users
- [ ] Community templates
- [ ] Web UI option
- [ ] Featured in Claude Code docs

---

**Remember:** This is a pivot from a working project. The zsh integration still works. We're rebuilding in Python for expandability!
