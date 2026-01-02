# aiterm Quick Start

> **TL;DR:** Terminal optimizer for Claude Code and Gemini CLI - detects project context, switches profiles, manages auto-approvals.

## 30-Second Setup

```bash
# macOS (Recommended)
brew install data-wise/tap/aiterm

# All Platforms (UV - fastest)
uv tool install git+https://github.com/Data-Wise/aiterm

# Verify installation
ait doctor
```

## What This Does

- **Detects** project context (R, Python, Node, Quarto, MCP, etc.)
- **Switches** iTerm2 profiles automatically based on context
- **Manages** Claude Code auto-approval permissions
- **Optimizes** terminal for AI-assisted development workflows

## Common Tasks

| I want to... | Run this |
|-------------|----------|
| Check my setup | `ait doctor` |
| See current context | `ait detect` |
| Apply context to terminal | `ait switch` |
| View Claude settings | `ait claude settings` |
| Backup my settings | `ait claude backup` |
| See auto-approvals | `ait claude approvals list` |
| Apply safe preset | `ait claude approvals preset safe` |
| List MCP servers | `ait mcp list` |

## Context Types Detected

| Context | Detected By | Profile |
|---------|-------------|---------|
| R Package | `DESCRIPTION` file | R-Dev |
| Python | `pyproject.toml` | Python-Dev |
| Node.js | `package.json` | Node-Dev |
| Quarto | `_quarto.yml` | R-Dev |
| MCP Server | `mcp-server/` dir | AI-Session |
| Production | `*/production/*` path | Production |
| AI Session | `*/claude-sessions/*` | AI-Session |

## Where Things Are

| File | Purpose |
|------|---------|
| `~/.claude/settings.json` | Claude Code configuration |
| `~/.config/opencode/config.json` | OpenCode configuration |
| `~/.config/aiterm/config.json` | aiterm settings (future) |

## Shell Aliases

```bash
ait    # → aiterm (main CLI)
oc     # → opencode (OpenCode CLI)
```

## Current Status

```bash
# Quick health check
ait doctor

# See what context would be applied
ait detect

# Check Claude Code settings
ait claude settings
```

## Need Help?

| Resource | Command/Link |
|----------|--------------|
| All commands | `ait --help` |
| Subcommand help | `ait <cmd> --help` |
| Full docs | https://data-wise.github.io/aiterm/ |
| Quick reference | [REFCARD.md](REFCARD.md) |

## Next Steps

1. Run `ait doctor` to verify installation
2. Run `ait detect` in a project directory
3. Run `ait switch` to apply the context
4. Explore `ait claude approvals` for permission management
