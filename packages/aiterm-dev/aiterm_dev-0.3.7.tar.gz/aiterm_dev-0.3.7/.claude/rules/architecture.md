---
paths:
  - "src/**"
  - "pyproject.toml"
---

# Architecture Rules

## High-Level Structure

```
aiterm/
├── src/aiterm/              # Main package
│   ├── __init__.py
│   ├── cli/                 # CLI commands (Typer)
│   │   ├── __init__.py
│   │   ├── main.py          # Main entry point
│   │   ├── profile.py       # Profile commands
│   │   ├── claude.py        # Claude Code commands
│   │   └── context.py       # Context commands
│   ├── terminal/            # Terminal backends
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract base
│   │   ├── iterm2.py        # iTerm2 implementation
│   │   └── detector.py      # Auto-detect terminal
│   ├── context/             # Context detection
│   │   ├── __init__.py
│   │   └── detector.py      # Project type detection
│   ├── claude/              # Claude Code integration
│   │   ├── __init__.py
│   │   ├── settings.py      # Settings management
│   │   ├── hooks.py         # Hook management
│   │   └── commands.py      # Command templates
│   └── utils/               # Utilities
│       ├── __init__.py
│       ├── config.py        # Config file handling
│       └── shell.py         # Shell integration
├── templates/               # User-facing templates
│   ├── profiles/            # iTerm2 profile JSON
│   ├── hooks/               # Hook templates
│   └── commands/            # Command templates
├── tests/                   # Test suite
├── docs/                    # Documentation (MkDocs)
├── pyproject.toml           # Project config
└── README.md
```

## Key Design Principles

1. **CLI-First Architecture**
   - Core logic in library (`src/aiterm/`)
   - CLI wraps library (thin layer in `cli/`)
   - Testable, reusable components

2. **Progressive Enhancement**
   - Start simple (MVP in 1 week)
   - Add features incrementally
   - Maintain backwards compatibility

3. **Terminal Abstraction**
   - Abstract base class for terminals
   - iTerm2 first, others later
   - Graceful degradation for unsupported features

4. **Medium Integration Depth**
   - Active terminal control (escape sequences, API)
   - Not just config generation
   - Not full IDE replacement

## File-Specific Guidance

### `src/aiterm/cli/main.py`
- Main entry point
- Registers all subcommands
- Global options (--verbose, --config)
- Version info

### `src/aiterm/terminal/iterm2.py`
- iTerm2-specific implementation
- Escape sequences for profile/title
- Python API integration (future)
- Status bar user variables

### `src/aiterm/context/detector.py`
- Project type detection
- File-based detection (DESCRIPTION, package.json, etc.)
- Path-based detection (production/, claude-sessions/)
- Git integration

### `src/aiterm/claude/settings.py`
- Read/write `~/.claude/settings.json`
- Validate settings structure
- Merge auto-approvals
- Backup functionality
