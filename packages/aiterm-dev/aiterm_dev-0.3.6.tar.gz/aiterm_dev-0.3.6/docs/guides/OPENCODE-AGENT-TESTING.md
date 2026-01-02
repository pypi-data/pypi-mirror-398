# OpenCode Agent Testing Guide

Quick reference for testing custom agents in OpenCode.

## Prerequisites

Verify setup:
```bash
ait opencode config      # Check agents configured
ait opencode instructions # Verify CLAUDE.md sync
ait opencode summary     # Complete configuration overview
python -m pytest tests/test_opencode*.py  # Run all OpenCode tests (103 tests)
```

## Available Agents

| Agent | Model | Tools | Shortcut | Use Case |
|-------|-------|-------|----------|----------|
| `r-dev` | Sonnet 4.5 | bash, read, write, edit, glob, grep | `ctrl+r` | R package development |
| `quick` | Haiku 4.5 | read, glob, grep | `ctrl+q` | Fast answers, simple queries |
| `research` | Opus 4.5 | read, write, edit, glob, grep, websearch, webfetch | `ctrl+s` | Academic research & manuscripts |

## Custom Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `rpkg-check` | Run R CMD check | R package validation |
| `rpkg-document` | Generate R docs | roxygen2 documentation |
| `rpkg-test` | Run R tests | testthat execution |
| `sync` | Git add, commit, push | Quick save & sync |
| `status` | Git status + log | Check repo state |

## Tool Permissions

| Tool | Permission | Description |
|------|------------|-------------|
| bash, read, glob, grep | `auto` | Read-only, always allowed |
| write, edit | `ask` | Modifying files, requires confirmation |

## Testing Agents in OpenCode

### Start OpenCode
```bash
opencode
```

### Switch Agents
```
/agent r-dev    # Switch to R development agent
/agent quick    # Switch to quick agent
/agent build    # Switch back to default build agent
```

### Test Scenarios

#### Test r-dev Agent
```
/agent r-dev
> Help me write an R function to calculate Cohen's d effect size
> What's in DESCRIPTION file?
> Run R CMD check on this package
```

Expected: Uses Sonnet 4.5, has full tool access, understands R ecosystem.

#### Test quick Agent
```
/agent quick
> What is the main export from this package?
> How many R files are in R/ directory?
> What's the package version?
```

Expected: Uses Haiku 4.5 (fast), read-only tools, quick responses.

## Verify CLAUDE.md Sync

In OpenCode, the agent should know about:
- Project structure from CLAUDE.md
- Rules from .claude/rules/*.md
- Global instructions from ~/.claude/CLAUDE.md (via AGENTS.md symlink)

Test:
```
> What are the key commands in this project?
> What's the project status?
```

Expected: Agent references CLAUDE.md content in responses.

## Troubleshooting

### Agent not switching
```bash
# Verify agents in config
cat ~/.config/opencode/config.json | jq '.agents'
```

### Instructions not loading
```bash
# Check symlink
ls -la ~/.config/opencode/AGENTS.md

# Verify instructions config
cat ~/.config/opencode/config.json | jq '.instructions'
```

### GitHub MCP not working
```bash
# Check token available
gh auth token

# Verify server enabled
cat ~/.config/opencode/config.json | jq '.mcp.github'
```

## Quick Validation

Run the test suite:
```bash
python tests/test_opencode_agents.py
```

All 14 tests should pass:
- Config (3): model, small_model, config exists
- Agents (3): r-dev, quick, valid tools
- MCP (3): GitHub, essentials, heavy disabled
- Sync (3): instructions, AGENTS.md, CLAUDE.md
- Env (2): GITHUB_TOKEN, opencode installed
