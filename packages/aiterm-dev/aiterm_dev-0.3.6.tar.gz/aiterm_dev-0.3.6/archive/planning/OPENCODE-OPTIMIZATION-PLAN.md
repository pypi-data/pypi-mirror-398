# OpenCode Performance Optimization Plan

**Created:** 2025-12-25
**Updated:** 2025-12-26
**Status:** Phase 2 (Option B) Complete ✅
**OpenCode Version:** 1.0.201

---

## Current State Analysis

### Configuration Audit (Dec 25, 2025)

| Metric | Value |
|--------|-------|
| Sessions | 12 |
| Messages | 1,434 |
| Total Cost | $0.00 (free models) |
| Input Tokens | 11.0M |
| Output Tokens | 681.9K |
| Cache Read | 95.5M (~90% hit rate!) |
| Top Tool | bash (48.7%) |

### MCP Servers Before

| Server | Status | Notes |
|--------|--------|-------|
| filesystem | enabled | Essential - keep |
| memory | enabled | Good for context - keep |
| sequential-thinking | enabled | Heavy - disabled |
| playwright | enabled | Heavy - disabled |
| everything | disabled | Already off |
| puppeteer | disabled | Already off |

---

## Phase 1: Option A (Lean & Fast) ✅ COMPLETE

**Applied:** Dec 25, 2025
**Config:** `~/.config/opencode/config.json`

### Changes Made

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-5",      // NEW
  "small_model": "anthropic/claude-haiku-4-5", // NEW
  "tui": {
    "scroll_acceleration": { "enabled": true } // NEW
  },
  "mcp": {
    "filesystem": { "enabled": true },
    "memory": { "enabled": true },
    "sequential-thinking": { "enabled": false }, // CHANGED
    "playwright": { "enabled": false },          // CHANGED
    "everything": { "enabled": false },
    "puppeteer": { "enabled": false }
  }
}
```

### Expected Improvements

1. **Faster Startup** - 2 fewer MCP servers to initialize
2. **Explicit Model** - No guessing, consistent behavior
3. **Cheaper Summaries** - Haiku for title generation
4. **Better Scrolling** - macOS-native scroll acceleration

---

## Phase 2: Option B (Balanced Power User) ✅ COMPLETE

**Status:** Fully Implemented
**Completed:** Dec 26, 2025

### CLI Commands (Implemented Dec 26, 2025)

```bash
# View config
ait opencode config              # Show current configuration
ait opencode config --raw        # Show raw JSON
ait opencode validate            # Check config validity
ait opencode backup              # Create timestamped backup

# Manage models
ait opencode models              # List recommended models
ait opencode set-model <model>   # Set primary model
ait opencode set-model <model> --small  # Set small model

# Manage agents
ait opencode agents list         # List custom agents
ait opencode agents add r-dev --desc "R development" --model anthropic/claude-sonnet-4-5
ait opencode agents remove r-dev

# Manage MCP servers
ait opencode servers list        # List all servers
ait opencode servers enable github
ait opencode servers disable playwright
```

### Applied Configuration ✅

```json
{
  "agents": {
    "r-dev": {
      "description": "R package development specialist",
      "model": "anthropic/claude-sonnet-4-5",
      "tools": ["bash", "read", "write", "edit", "glob", "grep"]
    },
    "quick": {
      "description": "Fast responses for simple questions",
      "model": "anthropic/claude-haiku-4-5",
      "tools": ["read", "glob", "grep"]
    }
  },
  "mcp": {
    "github": {
      "type": "local",
      "enabled": true,
      "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "{env:GITHUB_TOKEN}" }
    }
  }
}
```

### Environment Setup ✅

Added to `~/.config/zsh/.zshrc`:
```bash
# Export GITHUB_TOKEN from gh CLI for MCP servers (OpenCode, Claude Code)
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    export GITHUB_TOKEN=$(gh auth token 2>/dev/null)
fi
```

### Benefits Achieved

- ✅ Custom agents for different workflows (r-dev, quick)
- ✅ GitHub MCP for PR/issue management
- ✅ Automatic GITHUB_TOKEN from gh CLI auth
- ⏳ Auto-approve safe tools (future - tool permissions)
- ⏳ CLAUDE.md file loading (future - instructions)

---

## Phase 3: Option C (Full Ecosystem Integration)

**Status:** Planning
**When:** After Phase 2 validation complete ✅
**Estimated:** 2-3 hours

### Phase 3 Features

| Feature | Priority | Effort | Benefit |
|---------|----------|--------|---------|
| Research agent (Opus) | High | 10 min | Academic writing |
| Keyboard shortcuts | Medium | 30 min | Fast agent switching |
| Custom commands | Medium | 30 min | Workflow automation |
| Tool permissions | Low | 1 hour | Auto-approve safe tools |
| Time MCP | Low | 10 min | Deadline tracking |

### Proposed Additions

```json
{
  "agents": {
    "r-dev": { /* R package work */ },
    "research": {
      "description": "Academic research and manuscript writing",
      "model": "anthropic/claude-opus-4-5",
      "tools": ["read", "write", "edit", "websearch", "webfetch"]
    },
    "quick": { /* Fast questions */ }
  },
  "keybinds": {
    "ctrl+r": "agent:r-dev",
    "ctrl+q": "agent:quick"
  },
  "commands": {
    "rpkg-check": {
      "description": "Run R CMD check on current package",
      "command": "R CMD check --as-cran ."
    },
    "sync": {
      "description": "Git sync (add, commit, push)",
      "command": "git add -A && git commit -m 'sync' && git push"
    }
  },
  "mcp": {
    "github": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "{env:GITHUB_TOKEN}" },
      "enabled": true
    }
  }
}
```

### Benefits

- Multiple specialized agents
- Keyboard shortcuts for agent switching
- Custom commands matching workflow
- GitHub integration for PRs

---

## Available Config Templates

### Location: `~/.config/opencode/`

| File | Description |
|------|-------------|
| `config.json` | Active config (Option A applied) |
| `config.json.backup-*` | Timestamped backups |
| `config-recommended.json` | Balanced setup template |
| `config-advanced-dev.json` | Full server catalog (20+ servers) |

### Switching Configs

```bash
# Backup current
cp ~/.config/opencode/config.json ~/.config/opencode/config.json.backup-$(date +%Y%m%d)

# Apply recommended
cp ~/.config/opencode/config-recommended.json ~/.config/opencode/config.json

# Apply advanced (all servers)
cp ~/.config/opencode/config-advanced-dev.json ~/.config/opencode/config.json
```

---

## MCP Server Reference

### Core (Always Enabled)

| Server | Purpose |
|--------|---------|
| filesystem | File read/write access |
| memory | Context persistence |

### On-Demand (Enable When Needed)

| Server | Purpose | When to Enable |
|--------|---------|----------------|
| playwright | Browser automation | E2E testing, scraping |
| sequential-thinking | Complex reasoning | Multi-step problems |
| github | PR/issue management | Code review work |
| time | Timezone/deadlines | Scheduling tasks |

### Specialized (config-advanced-dev.json)

| Server | Purpose |
|--------|---------|
| postgres | Database queries |
| sqlite | Local database |
| docker | Container management |
| kubernetes | K8s cluster ops |
| sentry | Error tracking |
| figma | Design-to-code |
| slack | Team notifications |
| linear | Issue tracking |

---

## Validation Checklist

### After Option A

- [ ] OpenCode starts faster
- [ ] Scroll acceleration feels better
- [ ] Model selection works correctly
- [ ] No missing functionality from disabled servers

### After Option B

- [ ] Custom agents accessible
- [ ] Auto-approval reduces dialogs
- [ ] CLAUDE.md files loaded
- [ ] Tool restrictions work per-agent

### After Option C

- [ ] Keyboard shortcuts work
- [ ] Custom commands execute
- [ ] GitHub MCP connects
- [ ] Full workflow integration smooth

---

## Resources

- [OpenCode Config Docs](https://opencode.ai/docs/config/)
- [OpenCode CLI Reference](https://opencode.ai/docs/cli/)
- [OpenCode GitHub](https://github.com/opencode-ai/opencode)
- [MCP Server Registry](https://registry.modelcontextprotocol.io/)

---

## Next Steps

1. ~~**Validate Option A** - Use OpenCode for a day, note improvements~~ ✅
2. ~~**Apply Option B** - When ready for agents and permissions~~ ✅
3. ~~**Consider GitHub MCP** - For PR workflow integration~~ ✅
4. ~~**Sync with Claude Code** - Share CLAUDE.md files between tools~~ ✅
5. **Test agents in OpenCode** - Try `r-dev` and `quick` agents
6. **Consider Phase 3** - Keybinds, custom commands, research agent

---

## CLAUDE.md Sync Setup ✅

**Completed:** Dec 26, 2025

### Configuration

Added to `~/.config/opencode/config.json`:
```json
{
  "instructions": [
    "CLAUDE.md",
    ".claude/rules/*.md"
  ]
}
```

### Global Symlink

```bash
ln -s ~/.claude/CLAUDE.md ~/.config/opencode/AGENTS.md
```

### How It Works

| Tool | Global Instructions | Project Instructions |
|------|---------------------|---------------------|
| Claude Code | `~/.claude/CLAUDE.md` | `CLAUDE.md`, `.claude/rules/*.md` |
| OpenCode | `~/.config/opencode/AGENTS.md` → symlink | `instructions` array in config |

### CLI Command

```bash
ait opencode instructions   # Show all instruction files
```
