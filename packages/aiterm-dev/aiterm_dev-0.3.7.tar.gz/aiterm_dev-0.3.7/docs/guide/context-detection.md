# Context Detection

How the switcher detects your project type.

## Detection Priority

Contexts are checked in this order (first match wins):

```
1. 🚨 Production   (path)        ─┐
2. 🤖 AI-Session   (path)         │ Safety first
3. 📦 R Package    (DESCRIPTION) ─┐
4. 🐍 Python       (pyproject.toml)│ Language-specific
5. 📦 Node         (package.json)  ─┘
6. 📊 Quarto       (_quarto.yml) ─┐
7. 🔌 MCP Server   (mcp-server/)  │
8. ⚡ Emacs        (Cask, etc.)   │ Tool types
9. 🔧 Dev-Tools    (scripts/)    ─┘
10.   Default      (fallback)
```

## Detection Methods

### Path-based Detection

| Context | Path Pattern | Profile |
|---------|--------------|---------|
| Production | `*/production/*` or `*/prod/*` | Production |
| AI Sessions | `*/claude-sessions/*` or `*/gemini-sessions/*` | AI-Session |

### File-based Detection

| Context | File/Directory | Profile |
|---------|----------------|---------|
| R Package | `DESCRIPTION` file with `Package:` field | R-Dev |
| Python | `pyproject.toml` file | Python-Dev |
| Node.js | `package.json` file | Node-Dev |
| Quarto | `_quarto.yml` file | R-Dev |
| MCP Server | `mcp-server/` directory or `*mcp*` with `package.json` | AI-Session |
| Emacs | `Cask`, `.dir-locals.el`, `init.el`, or `early-init.el` | Emacs |
| Dev-Tools | Git repo with `commands/` or `scripts/` directory | Dev-Tools |

## Profile + Icon Summary

| Context | Profile | Icon | Theme |
|---------|---------|------|-------|
| Production | Production | 🚨 | Red |
| AI Sessions | AI-Session | 🤖 | Purple |
| R Package | R-Dev | 📦 | Blue |
| Python | Python-Dev | 🐍 | Green |
| Node.js | Node-Dev | 📦 | Dark |
| Quarto | R-Dev | 📊 | Blue |
| MCP Server | AI-Session | 🔌 | Purple |
| Emacs | Emacs | ⚡ | Purple |
| Dev-Tools | Dev-Tools | 🔧 | Amber |
| Default | Default | (none) | Default |

## Conflict Resolution

When multiple markers exist, the **first match** wins:

| Scenario | Winner | Why |
|----------|--------|-----|
| R pkg with Quarto vignettes | 📦 R | R detected first |
| Python with Makefile | 🐍 Python | Python detected first |
| Quarto in production folder | 🚨 Production | Safety priority |
| MCP server with Node | 🔌 MCP | MCP detected before Node |

## Project Name Extraction

For some contexts, the project name is extracted from files:

| Context | Source |
|---------|--------|
| R Package | `Package:` field in DESCRIPTION |
| Node.js | `"name"` field in package.json |
| Quarto | `title:` field in _quarto.yml |
| Others | Directory name |

## Detection Requirements

### Dev-Tools Detection

Dev-tools detection requires:

1. **Git repository** (`.git` directory exists)
2. **AND** one of:
   - `commands/` directory
   - `scripts/` directory
   - `bin/` directory with `Makefile`

This prevents false positives (e.g., `~/scripts` folder).

### MCP Server Detection

MCP servers are detected by:

1. `mcp-server/` directory exists, **OR**
2. Path contains `mcp` AND has `package.json`
