# UV Quick Start Guide

## Installation (Complete! ✅)

```bash
# Already done:
uv venv                          # Created .venv
uv pip install -e ".[dev]"       # Installed aiterm in editable mode
pytest -v                        # All 51 tests passing!
```

## Daily Usage

```bash
# Activate environment
source .venv/bin/activate

# Run commands
aiterm --help                    # Main CLI
ait --help                       # Short alias
aiterm doctor                    # Health check
aiterm detect                    # Detect project context
aiterm claude approvals list     # View auto-approvals

# Test
pytest                           # Run all tests
pytest -v                        # Verbose output
pytest tests/test_cli.py -v      # Specific test file
pytest -k "context"              # Run tests matching pattern

# Code quality
black src/ tests/                # Format code
ruff check src/                  # Lint
mypy src/                        # Type check

# Deactivate
deactivate
```

## Adding Dependencies

```bash
# Edit pyproject.toml, add to dependencies list, then:
uv pip install -e ".[dev]"
```

## Why UV?

- **10-100x faster** than pip (written in Rust)
- **Compatible** with pip/pip-tools/requirements.txt
- **No lock file confusion** (unlike Poetry)
- **Simple** - just faster pip

## Project Structure

```
aiterm/
├── .venv/                       # Virtual environment (uv venv)
├── src/aiterm/                  # Source code
│   ├── cli/                     # CLI commands
│   ├── context/                 # Context detection
│   ├── terminal/                # Terminal backends
│   ├── claude/                  # Claude Code integration
│   └── utils/                   # Utilities
├── tests/                       # Test suite (51 tests)
├── pyproject.toml               # Project config
└── UV-QUICKSTART.md            # This file
```

## Commands Available Now

- ✅ `aiterm --version` - Version info
- ✅ `aiterm doctor` - Health check
- ✅ `aiterm detect` - Context detection
- ✅ `aiterm switch` - Apply context to terminal
- ✅ `aiterm claude settings` - View Claude settings
- ✅ `aiterm claude approvals list` - View auto-approvals
- ✅ `aiterm claude approvals add <preset>` - Add approval preset

## Next Steps (Future)

- `aiterm init` - Setup wizard (coming v0.1.0)
- `aiterm profile list` - Profile management (v0.2.0)
- Hook management (v0.2.0)
- Command templates (v0.2.0)

## Resources

- UV Docs: https://github.com/astral-sh/uv
- aiterm Docs: `mkdocs serve` (port 8000)
- Tests: `pytest --help`
