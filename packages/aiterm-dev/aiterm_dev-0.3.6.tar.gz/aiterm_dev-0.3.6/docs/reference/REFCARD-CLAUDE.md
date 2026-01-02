# Claude Code Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│ AITERM - Claude Code Commands                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ SETTINGS                                                    │
│ ─────────                                                   │
│ ait claude settings        View current settings            │
│ ait claude backup          Create timestamped backup        │
│                                                             │
│ AUTO-APPROVALS                                              │
│ ──────────────                                              │
│ ait claude approvals list     Show current approvals        │
│ ait claude approvals presets  List available presets        │
│ ait claude approvals add <p>  Add preset to approvals       │
│                                                             │
│ PRESETS                                                     │
│ ────────                                                    │
│ safe       Read-only commands (git status, ls, cat)         │
│ moderate   Safe file edits + git operations                 │
│ git        Git-specific operations                          │
│ npm        Node.js package commands                         │
│ python     Python dev commands (pytest, pip)                │
│ full       All common permissions                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ COMMON WORKFLOWS                                            │
│ ────────────────                                            │
│                                                             │
│ First-time setup:                                           │
│   ait claude backup && ait claude approvals add safe        │
│                                                             │
│ Add development permissions:                                │
│   ait claude approvals add moderate                         │
│                                                             │
│ Check what's approved:                                      │
│   ait claude approvals list                                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ CONFIG FILE                                                 │
│ ───────────                                                 │
│ Location: ~/.claude/settings.json                           │
│ Backup:   ~/.claude/settings.json.backup-YYYYMMDD-HHMMSS    │
│                                                             │
│ Structure:                                                  │
│   {                                                         │
│     "permissions": {                                        │
│       "allow": ["Bash(git:*)", "Read(*)"],                  │
│       "deny": []                                            │
│     }                                                       │
│   }                                                         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ PERMISSION PATTERNS                                         │
│ ───────────────────                                         │
│ Bash(cmd:*)         Allow command with any args             │
│ Bash(cmd:arg)       Allow specific command + arg            │
│ Read(*)             Allow reading any file                  │
│ Write(path/*)       Allow writing to path                   │
│ Edit(*)             Allow editing any file                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ SEE ALSO                                                    │
│ ─────────                                                   │
│ Main REFCARD:  docs/REFCARD.md                              │
│ MCP REFCARD:   docs/reference/REFCARD-MCP.md                │
│ Hooks REFCARD: docs/reference/REFCARD-HOOKS.md              │
└─────────────────────────────────────────────────────────────┘
```
