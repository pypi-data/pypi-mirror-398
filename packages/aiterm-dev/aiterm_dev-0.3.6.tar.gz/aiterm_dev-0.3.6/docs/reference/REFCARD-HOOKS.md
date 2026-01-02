# Hooks Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│ AITERM - Hook Management Commands                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ LISTING                                                     │
│ ────────                                                    │
│ ait hooks list           Show installed + available hooks   │
│                                                             │
│ INSTALLATION                                                │
│ ─────────────                                               │
│ ait hooks install <name>     Install from template          │
│ ait hooks install <n> -f     Force reinstall                │
│ ait hooks uninstall <name>   Remove hook                    │
│ ait hooks uninstall <n> -y   Skip confirmation              │
│                                                             │
│ TESTING                                                     │
│ ────────                                                    │
│ ait hooks test <name>    Execute hook and show output       │
│ ait hooks validate       Check all hooks are executable     │
│ ait hooks validate <n>   Check specific hook                │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ HOOK TYPES                                                  │
│ ───────────                                                 │
│                                                             │
│ PreToolUse        Before Claude runs a tool                 │
│ PostToolUse       After Claude runs a tool                  │
│ PrePromptSubmit   Before sending prompt to Claude           │
│ PostPromptSubmit  After Claude responds                     │
│ SessionStart      When Claude Code session starts           │
│ SessionEnd        When session ends                         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ AVAILABLE TEMPLATES                                         │
│ ────────────────────                                        │
│                                                             │
│ prompt-optimizer   Enhance prompts with context             │
│ context-auto       Auto-detect and switch context           │
│ session-logger     Log session activity                     │
│ git-guard          Prevent dangerous git commands           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ HOOK LOCATIONS                                              │
│ ──────────────                                              │
│ Installed: ~/.claude/hooks/<name>.sh                        │
│ Templates: ~/.local/share/aiterm/templates/hooks/           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ HOOK SCRIPT FORMAT                                          │
│ ───────────────────                                         │
│                                                             │
│ #!/bin/bash                                                 │
│ # Hook: PreToolUse                                          │
│ # Description: What this hook does                          │
│                                                             │
│ # Environment variables available:                          │
│ # $CLAUDE_TOOL_NAME - Tool being called                     │
│ # $CLAUDE_TOOL_ARGS - JSON args to tool                     │
│ # $CLAUDE_SESSION_ID - Current session                      │
│                                                             │
│ # Exit codes:                                               │
│ # 0 = continue (allow tool/prompt)                          │
│ # 1 = block (prevent tool/prompt)                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ COMMON WORKFLOWS                                            │
│ ────────────────                                            │
│                                                             │
│ Install prompt optimizer:                                   │
│   ait hooks install prompt-optimizer                        │
│   ait hooks test prompt-optimizer                           │
│                                                             │
│ Check all hooks:                                            │
│   ait hooks validate                                        │
│                                                             │
│ Fix permissions:                                            │
│   chmod +x ~/.claude/hooks/*.sh                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ PERFORMANCE                                                 │
│ ───────────                                                 │
│ Hooks should complete in <500ms to avoid delays.            │
│ ait hooks test shows execution time.                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ SEE ALSO                                                    │
│ ─────────                                                   │
│ Main REFCARD:   docs/REFCARD.md                             │
│ Claude REFCARD: docs/reference/REFCARD-CLAUDE.md            │
│ MCP REFCARD:    docs/reference/REFCARD-MCP.md               │
└─────────────────────────────────────────────────────────────┘
```
