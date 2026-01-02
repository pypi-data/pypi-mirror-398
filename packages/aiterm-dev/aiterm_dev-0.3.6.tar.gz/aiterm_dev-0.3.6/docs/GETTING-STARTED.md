# Getting Started with aiterm

> **Time:** ~10 minutes | **Level:** Beginner

This hands-on tutorial walks you through setting up aiterm and using its core features.

## Prerequisites

Before starting, verify you have:

```bash
# Check Python version (3.10+ required)
python3 --version

# Check terminal (iTerm2 recommended)
echo $TERM_PROGRAM
```

## Part 1: Installation (2 min)

### Install aiterm

Choose your preferred method:

=== "Quick Install (Recommended)"
    ```bash
    curl -fsSL https://raw.githubusercontent.com/Data-Wise/aiterm/main/install.sh | bash
    ```
    Auto-detects best method: uv → pipx → brew → pip

=== "Homebrew (macOS)"
    ```bash
    brew install data-wise/tap/aiterm
    ```

=== "UV (All Platforms)"
    ```bash
    uv tool install aiterm-dev
    ```

=== "pipx (All Platforms)"
    ```bash
    pipx install aiterm-dev
    ```

=== "pip"
    ```bash
    pip install aiterm-dev
    ```

### Verify Installation

```bash
ait doctor
```

Expected output:
```
aiterm doctor - Health check

Terminal: iTerm.app
Shell: /bin/zsh
Python: 3.12.0
aiterm: 0.3.5

Basic checks passed!
```

### Checkpoint

- [ ] `ait --version` shows version number
- [ ] `ait doctor` shows "Basic checks passed"

---

## Part 2: Context Detection (3 min)

aiterm automatically detects your project type and applies the right terminal profile.

### Try Detection

Navigate to any project and run:

```bash
cd ~/some-project
ait detect
```

Example output for a Python project:
```
┌────────────────────────────────────┐
│ Context Detection                  │
├────────────────────────────────────┤
│ Directory │ /Users/you/my-project  │
│ Type      │ 🐍 python              │
│ Name      │ my-project             │
│ Profile   │ Python-Dev             │
│ Git Branch│ main                   │
└────────────────────────────────────┘
```

### Supported Project Types

| Type | Detected By | Profile |
|------|-------------|---------|
| R Package | `DESCRIPTION` file | R-Dev |
| Python | `pyproject.toml` | Python-Dev |
| Node.js | `package.json` | Node-Dev |
| Quarto | `_quarto.yml` | R-Dev |
| MCP Server | `mcp-server/` dir | AI-Session |

### Apply Context

To actually switch your terminal profile:

```bash
ait switch
```

This:
1. Detects project type
2. Switches iTerm2 profile
3. Updates tab title

### Checkpoint

- [ ] `ait detect` shows your project type
- [ ] `ait switch` applies the profile (iTerm2 only)

---

## Part 3: Claude Code Integration (3 min)

aiterm helps manage Claude Code settings and auto-approvals.

### View Current Settings

```bash
ait claude settings
```

Example output:
```
┌────────────────────────────────────┐
│ Claude Code Settings               │
├────────────────────────────────────┤
│ File        │ ~/.claude/settings.json │
│ Permissions (allow) │ 15           │
│ Permissions (deny)  │ 0            │
│ Hooks       │ 2                    │
└────────────────────────────────────┘

Allowed:
  ✓ Bash(git status:*)
  ✓ Bash(npm test:*)
  ... and 13 more
```

### Backup Settings

Before making changes, always backup:

```bash
ait claude backup
```

### Manage Auto-Approvals

View available presets:

```bash
ait claude approvals presets
```

Output:
```
┌────────────────────────────────────────────┐
│ Available Presets                          │
├──────────┬────────────────────┬────────────┤
│ Name     │ Description        │ Permissions│
├──────────┼────────────────────┼────────────┤
│ safe     │ Read-only commands │ 8          │
│ moderate │ Safe file edits    │ 15         │
│ git      │ Git operations     │ 12         │
│ full     │ All permissions    │ 25         │
└──────────┴────────────────────┴────────────┘
```

Add a preset:

```bash
ait claude approvals add safe
```

### Checkpoint

- [ ] `ait claude settings` shows your config
- [ ] `ait claude backup` creates a backup
- [ ] `ait claude approvals list` shows current approvals

---

## Part 4: MCP Servers (2 min)

Manage MCP (Model Context Protocol) servers for Claude Code.

### List Configured Servers

```bash
ait mcp list
```

### Test a Server

```bash
ait mcp test filesystem
```

### Validate Configuration

```bash
ait mcp validate
```

### Checkpoint

- [ ] `ait mcp list` shows your servers
- [ ] `ait mcp validate` passes

---

## Summary

You've learned how to:

| Task | Command |
|------|---------|
| Check installation | `ait doctor` |
| Detect project context | `ait detect` |
| Apply context to terminal | `ait switch` |
| View Claude settings | `ait claude settings` |
| Backup settings | `ait claude backup` |
| Manage auto-approvals | `ait claude approvals` |
| List MCP servers | `ait mcp list` |

## Quick Reference

```bash
# Essential
ait doctor                  # Health check
ait detect                  # Show context
ait switch                  # Apply context

# Claude Code
ait claude settings         # View settings
ait claude backup           # Backup
ait claude approvals list   # Show approvals

# MCP
ait mcp list               # List servers
ait mcp validate           # Check config
```

## Next Steps

1. **Enable shell completion:** [Shell Completion Guide](guide/shell-completion.md)
2. **Explore hooks:** `ait hooks list`
3. **Read the full reference:** [REFCARD](REFCARD.md)

## Need Help?

- `ait --help` - All commands
- `ait <command> --help` - Command details
- [Full Documentation](https://data-wise.github.io/aiterm/)
