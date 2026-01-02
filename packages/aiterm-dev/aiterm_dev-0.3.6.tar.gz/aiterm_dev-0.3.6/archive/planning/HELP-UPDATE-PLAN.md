# aiterm Help Files Update Plan

**Created:** 2025-12-25
**Based on:** flow-cli documentation standards
**Status:** Planning

---

## Current State Analysis

### What Exists

| Asset | Status | Location |
|-------|--------|----------|
| CLI `--help` | Good (Typer) | Built-in |
| Templates | Templates only | `standards/adhd/` |
| Tutorials | Extensive | `docs/*.md` |
| REFCARD | Missing | - |
| QUICK-START | Missing | - |
| CLI Examples | Missing | In help output |

### Gaps vs Flow-CLI Standards

| Standard | Flow-CLI | aiterm | Priority |
|----------|----------|--------|----------|
| REFCARD (1-page) | Yes | No | **P1** |
| QUICK-START | Yes | No | **P1** |
| CLI Examples | In help | Missing | **P2** |
| Subcommand consistency | Strict | Variable | **P2** |
| ZSH integration help | Extensive | Basic alias | **P3** |

---

## Phase 1: Core Help Documents (Quick Wins)

### 1.1 Create REFCARD.md

**Location:** `docs/REFCARD.md`
**Format:** ASCII Box Style (fits one page)

```
┌─────────────────────────────────────────────────────────────┐
│ AITERM v0.2.1 - Quick Reference                             │
├─────────────────────────────────────────────────────────────┤
│ ESSENTIAL                                                   │
│ ──────────                                                  │
│ ait doctor           Check installation                     │
│ ait detect           Show project context                   │
│ ait switch           Apply context to terminal              │
│                                                             │
│ CLAUDE CODE                                                 │
│ ──────────                                                  │
│ ait claude settings  View settings                          │
│ ait claude backup    Backup settings                        │
│ ait claude approvals Manage auto-approvals                  │
│                                                             │
│ CONTEXT                                                     │
│ ────────                                                    │
│ ait context detect   Detect project type                    │
│ ait context apply    Apply profile to terminal              │
│                                                             │
│ PROFILES                                                    │
│ ─────────                                                   │
│ ait profile list     List available profiles                │
│ ait profile show     Show current profile                   │
│                                                             │
│ WORKFLOW                                                    │
│ ─────────                                                   │
│ cd ~/project && ait switch   # One-time context switch      │
│ ait doctor && ait init       # First-time setup             │
└─────────────────────────────────────────────────────────────┘
```

**Checklist:**
- [ ] Fits 80 cols × 40 lines
- [ ] Essential commands first
- [ ] Grouped by task (not alphabetical)
- [ ] 2-4 word descriptions
- [ ] Aliases included (ait)
- [ ] Version number
- [ ] One workflow pattern

---

### 1.2 Create QUICK-START.md

**Location:** `docs/QUICK-START.md`
**Template:** Flow-CLI QUICK-START format

```markdown
# aiterm

> **TL;DR:** Terminal optimizer for Claude Code and Gemini CLI workflows.

## 30-Second Setup

```bash
# Install (choose one)
brew install data-wise/tap/aiterm    # macOS
uv tool install aiterm               # All platforms

# Verify
ait doctor
```

## What This Does

- Detects project context (R, Python, Node, etc.)
- Switches iTerm2 profiles automatically
- Manages Claude Code auto-approvals
- Optimizes terminal for AI-assisted development

## Common Tasks

| I want to... | Run this |
|-------------|----------|
| Check setup | `ait doctor` |
| See context | `ait detect` |
| Apply context | `ait switch` |
| View Claude settings | `ait claude settings` |
| Backup settings | `ait claude backup` |
| Manage approvals | `ait claude approvals list` |

## Where Things Are

| File | Purpose |
|------|---------|
| `~/.claude/settings.json` | Claude Code config |
| `~/.config/opencode/config.json` | OpenCode config |
| `~/.config/aiterm/` | aiterm config (future) |

## Need Help?

- `ait --help` - All commands
- `ait <cmd> --help` - Command details
- https://data-wise.github.io/aiterm/
```

---

## Phase 2: CLI Help Improvements

### 2.1 Add Examples to Subcommands

**Pattern:** Each command should have at least one example

**Current (Missing Examples):**
```
╭─ Commands ───────────────────────────────────╮
│ detect   Detect the project context          │
╰──────────────────────────────────────────────╯
```

**Target (With Examples):**
```
╭─ Commands ───────────────────────────────────╮
│ detect   Detect the project context          │
│          Example: ait detect ~/my-project    │
╰──────────────────────────────────────────────╯
```

### Files to Update

| File | Commands | Priority |
|------|----------|----------|
| `src/aiterm/cli/main.py` | doctor, detect, switch | P2 |
| `src/aiterm/cli/claude.py` | settings, backup, approvals | P2 |
| `src/aiterm/cli/context.py` | detect, show, apply | P2 |
| `src/aiterm/cli/profile.py` | list, show | P3 |

### 2.2 Typer Epilog Pattern

Use Typer's `epilog` parameter for examples:

```python
@app.command(
    epilog="""
Examples:
  ait detect              # Current directory
  ait detect ~/projects   # Specific path
  ait detect --json       # JSON output
"""
)
def detect(...):
    ...
```

---

## Phase 3: ZSH Integration Help

### 3.1 Shell Alias Documentation

**Current:** Just `ait` alias
**Target:** Documented with related aliases

```bash
# ~/.config/zsh/.zshrc additions
alias ait='aiterm'           # Main CLI
alias aitd='aiterm doctor'   # Quick doctor
alias aits='aiterm switch'   # Quick switch
alias oc='opencode'          # OpenCode CLI
```

### 3.2 Shell Completion

Typer provides completion, but needs documentation:

```bash
# Add to shell
ait --install-completion

# Or manually
eval "$(ait --show-completion zsh)"
```

---

## Implementation Order

### Week 1: Quick Wins ✅ COMPLETE
1. [x] Create `docs/REFCARD.md` (30 min)
2. [x] Create `docs/QUICK-START.md` (30 min)
3. [x] Add to mkdocs navigation (10 min)

### Week 2: CLI Polish ✅ COMPLETE
4. [x] Add examples to main.py commands (1 hr)
5. [x] Add examples to hooks.py commands
6. [x] Add examples to mcp.py commands

### Week 3: Integration ✅ COMPLETE
7. [x] Document shell aliases in CLAUDE.md
8. [x] Document shell completion (`docs/guide/shell-completion.md`)
9. [x] Add to CLAUDE.md quick reference

### Bonus: Context-Specific REFCARDs ✅ COMPLETE
10. [x] Create `docs/GETTING-STARTED.md` (hands-on tutorial)
11. [x] Create `docs/reference/REFCARD-CLAUDE.md`
12. [x] Create `docs/reference/REFCARD-MCP.md`
13. [x] Create `docs/reference/REFCARD-HOOKS.md`
14. [x] Update mkdocs.yml navigation

---

## Validation Checklist

### REFCARD
- [ ] Prints on one page (test with `lp`)
- [ ] All essential commands included
- [ ] Descriptions are 2-4 words
- [ ] Grouped by task

### QUICK-START
- [ ] TL;DR first
- [ ] 30-second setup works
- [ ] Table of common tasks
- [ ] File locations accurate

### CLI Help
- [ ] Every command has at least one example
- [ ] Consistent description style
- [ ] No abbreviations in descriptions

---

## Flow-CLI Standards Reference

| Document | Purpose | Template |
|----------|---------|----------|
| REFCARD | Quick lookup | `standards/adhd/REFCARD-TEMPLATE.md` |
| QUICK-START | Get running fast | `standards/adhd/QUICK-START-TEMPLATE.md` |
| GETTING-STARTED | Hands-on onboarding | `standards/adhd/GETTING-STARTED-TEMPLATE.md` |
| TUTORIAL | Deep learning | `standards/adhd/TUTORIAL-TEMPLATE.md` |

**Key Principles:**
- Descriptions: Start with verb, 2-4 words, no articles
- Grouping: By task, never alphabetical
- Examples: Copy-paste ready, with comments
- ADHD-friendly: Visual hierarchy, no walls of text

---

## Next Steps

1. **Start with REFCARD** - Highest impact, lowest effort
2. **Add QUICK-START** - Essential for new users
3. **Polish CLI help** - Add examples incrementally
4. **Document in CLAUDE.md** - Reference the new docs
