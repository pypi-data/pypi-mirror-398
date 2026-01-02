# aiterm Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│ AITERM v0.3.6 - Terminal Optimizer for AI Development      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ESSENTIAL                                                   │
│ ──────────                                                  │
│ ait doctor              Check installation                  │
│ ait detect              Show project context                │
│ ait switch              Apply context to terminal           │
│ ait hello               Diagnostic greeting                 │
│ ait info                System diagnostics (--json)         │
│                                                             │
│ CLAUDE CODE                                                 │
│ ──────────                                                  │
│ ait claude settings     View current settings               │
│ ait claude backup       Backup settings file                │
│ ait claude approvals    Manage auto-approvals               │
│   approvals list        Show current approvals              │
│   approvals add <cmd>   Add approval rule                   │
│   approvals preset      Apply preset (safe/moderate/full)   │
│                                                             │
│ CONTEXT DETECTION                                           │
│ ─────────────────                                           │
│ ait context detect      Detect project type                 │
│ ait context show        Alias for detect                    │
│ ait context apply       Apply profile to terminal           │
│                                                             │
│ PROFILES                                                    │
│ ─────────                                                   │
│ ait profile list        List available profiles             │
│ ait profile show        Show current profile                │
│                                                             │
│ MCP SERVERS                                                 │
│ ───────────                                                 │
│ ait mcp list            List configured servers             │
│ ait mcp status          Check server health                 │
│ ait mcp test <name>     Test specific server                │
│                                                             │
│ HOOKS & COMMANDS                                            │
│ ────────────────                                            │
│ ait hooks list          List installed hooks                │
│ ait commands list       List command templates              │
│                                                             │
│ DOCUMENTATION                                               │
│ ─────────────                                               │
│ ait docs check          Validate documentation              │
│ ait docs serve          Preview docs locally                │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ COMMON WORKFLOWS                                            │
│ ────────────────                                            │
│                                                             │
│ Quick install:                                              │
│   curl -fsSL .../install.sh | bash                          │
│                                                             │
│ First-time setup:                                           │
│   ait doctor && ait hello                                   │
│                                                             │
│ Switch context when entering project:                       │
│   cd ~/my-project && ait switch                             │
│                                                             │
│ Backup before changes:                                      │
│   ait claude backup && ait claude approvals preset safe     │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ SHELL ALIASES                                               │
│ ─────────────                                               │
│ ait          aiterm (main CLI)                              │
│ oc           opencode (OpenCode CLI)                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ CONFIG LOCATIONS                                            │
│ ────────────────                                            │
│ ~/.claude/settings.json       Claude Code settings          │
│ ~/.config/opencode/config.json  OpenCode settings           │
│ ~/.config/aiterm/config.json  aiterm settings (future)      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Docs: https://data-wise.github.io/aiterm/                   │
│ Repo: https://github.com/Data-Wise/aiterm                   │
└─────────────────────────────────────────────────────────────┘
```

## Domain-Specific Reference Cards

| Topic | File |
|-------|------|
| Claude Code | [REFCARD-CLAUDE.md](reference/REFCARD-CLAUDE.md) |
| MCP Servers | [REFCARD-MCP.md](reference/REFCARD-MCP.md) |
| Hooks | [REFCARD-HOOKS.md](reference/REFCARD-HOOKS.md) |
| Context Detection | [REFCARD-CONTEXT.md](reference/REFCARD-CONTEXT.md) |
| OpenCode | [REFCARD-OPENCODE.md](reference/REFCARD-OPENCODE.md) |

## Print Version

For a printer-friendly version without markdown formatting:

```bash
# Print to terminal
ait --help

# Save to file
ait --help > aiterm-help.txt
```
