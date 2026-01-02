# MCP Servers Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│ AITERM - MCP Server Commands (v0.3.4+)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ OPENCODE SERVERS (ait opencode servers)                     │
│ ──────────────────────────────────────                      │
│                                                             │
│ Listing & Status:                                           │
│   ait opencode servers list      List all servers           │
│   ait opencode servers templates List available templates   │
│   ait opencode servers test X    Test server X              │
│   ait opencode servers health    Check all enabled          │
│   ait opencode servers health -a Check all servers          │
│                                                             │
│ Enable/Disable:                                             │
│   ait opencode servers enable X  Enable server X            │
│   ait opencode servers disable X Disable server X           │
│                                                             │
│ Add/Remove:                                                 │
│   ait opencode servers add X -t      Add from template      │
│   ait opencode servers add X -c "."  Add with command       │
│   ait opencode servers remove X      Remove server          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ SERVER TEMPLATES (12 available)                             │
│ ──────────────────────────────                              │
│                                                             │
│ Essential:                                                  │
│   filesystem     File read/write access                     │
│   memory         Persistent context memory                  │
│                                                             │
│ Optional:                                                   │
│   sequential-thinking  Complex reasoning chains             │
│   playwright           Browser automation                   │
│   github               PR/issue management  (GITHUB_TOKEN)  │
│   time                 Timezone tracking                    │
│   brave-search         Web search           (BRAVE_API_KEY) │
│   slack                Slack integration    (SLACK_TOKEN)   │
│   sqlite               SQLite database access               │
│   puppeteer            Headless browser automation          │
│   fetch                HTTP fetch for web content           │
│   everything           Demo server (testing only)           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ CONFIG FILE                                                 │
│ ───────────                                                 │
│ Claude Code: ~/.claude/settings.json                        │
│ OpenCode:    ~/.config/opencode/config.json                 │
│                                                             │
│ Claude Code format:                                         │
│   {                                                         │
│     "mcpServers": {                                         │
│       "filesystem": {                                       │
│         "command": "npx",                                   │
│         "args": ["-y", "@anthropic/server-filesystem"]      │
│       }                                                     │
│     }                                                       │
│   }                                                         │
│                                                             │
│ OpenCode format:                                            │
│   {                                                         │
│     "mcp": {                                                │
│       "filesystem": {                                       │
│         "type": "local",                                    │
│         "command": ["npx", "-y", "@anthropic/..."],         │
│         "enabled": true                                     │
│       }                                                     │
│     }                                                       │
│   }                                                         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ COMMON WORKFLOWS                                            │
│ ────────────────                                            │
│                                                             │
│ Check all servers work:                                     │
│   ait mcp validate && ait mcp test-all                      │
│                                                             │
│ Debug a server:                                             │
│   ait mcp info <name>                                       │
│   ait mcp test <name> -t 30                                 │
│                                                             │
│ See server command:                                         │
│   ait mcp info filesystem                                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ TROUBLESHOOTING                                             │
│ ───────────────                                             │
│ "Server unreachable"                                        │
│   → Check: which npx (command exists?)                      │
│   → Check: npm install -g @anthropic/server-filesystem      │
│                                                             │
│ "Invalid JSON"                                              │
│   → Check: cat ~/.claude/settings.json | jq .               │
│                                                             │
│ "Timeout"                                                   │
│   → Try: ait mcp test <name> -t 30                          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ SEE ALSO                                                    │
│ ─────────                                                   │
│ Main REFCARD:   docs/REFCARD.md                             │
│ Claude REFCARD: docs/reference/REFCARD-CLAUDE.md            │
│ Hooks REFCARD:  docs/reference/REFCARD-HOOKS.md             │
│ MCP Registry:   https://registry.modelcontextprotocol.io    │
└─────────────────────────────────────────────────────────────┘
```
