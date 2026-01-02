---
paths:
  - "tests/**"
  - "**/*.py"
---

# Development Workflow

## Setting Up Dev Environment

```bash
# Clone repo
cd ~/projects/dev-tools/aiterm

# Set up Python environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Try CLI
aiterm --help
```

## Adding a New Command

1. Create command file in `src/aiterm/cli/`
2. Define command using Typer
3. Add tests in `tests/`
4. Update documentation

Example:
```python
# src/aiterm/cli/profile.py
import typer
from rich import print

app = typer.Typer()

@app.command()
def list():
    """List available profiles"""
    print("[bold]Available Profiles:[/bold]")
    # Implementation
```

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_cli.py::test_init_command

# Run with coverage
pytest --cov=aiterm

# Run integration tests (requires iTerm2)
pytest -m integration
```

## Common Git Operations

```bash
git status
git add .
git commit -m "feat: add profile management"
git push
```
