---
paths:
  - "zsh/**"
  - "scripts/**"
---

# Code Migration from v2.5.0

## Priority 1: Core Functionality

**From:** `zsh/iterm2-integration.zsh` (186 lines)
**To:** `src/aiterm/terminal/iterm2.py` + `src/aiterm/context/detector.py`

Key functions to port:
- `_iterm_detect_context()` - Main detection logic
- `_iterm_switch_profile()` - Profile switching
- `_iterm_set_title()` - Tab title setting
- `_iterm_set_status_vars()` - Status bar variables
- `_iterm_git_info()` - Git branch/dirty detection

Context detection patterns (8 types):
1. Production paths (`*/production/*`, `*/prod/*`) → Production profile
2. AI sessions (`*/claude-sessions/*`, `*/gemini-sessions/*`) → AI-Session profile
3. R packages (`DESCRIPTION` file) → R-Dev profile
4. Python (`pyproject.toml`) → Python-Dev profile
5. Node.js (`package.json`) → Node-Dev profile
6. Quarto (`_quarto.yml`) → R-Dev profile
7. MCP (`mcp-server/` dir) → AI-Session profile
8. Dev-tools (`.git` + `scripts/`) → Dev-Tools profile

## Priority 2: Testing

**From:** `scripts/test-context-switcher.sh` (370 lines)
**To:** `tests/test_context.py`, `tests/test_terminal.py`

15 existing tests to port:
- R package detection
- Python project detection
- Node.js project detection
- MCP server detection
- Production path detection
- Git dirty indicator
- Quarto project detection
- Default fallback
- (Plus integration tests)

## Priority 3: Templates

**From:** `statusline-alternatives/`, existing profiles
**To:** `templates/profiles/`

3 theme variants:
- cool-blues
- forest-greens
- purple-charcoal

## Migration Notes

**Remember:** This is a pivot from a working project. The zsh integration still works. We're rebuilding in Python for expandability, not fixing something broken. Take time to understand the existing code before porting!
