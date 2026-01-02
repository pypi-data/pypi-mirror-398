# Contributing

**aiterm** is an open-source project and welcomes contributions!

---

## Quick Start for Contributors

### 1. Setup Development Environment

```bash
# Clone repository
git clone https://github.com/Data-Wise/aiterm.git
cd aiterm

# Create virtual environment with uv
uv venv

# Activate environment
source .venv/bin/activate

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest -v

# All 51 tests should pass!
```

### 2. Development Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes
# ... edit code ...

# Run tests
pytest -v

# Format code
black src/ tests/
ruff check src/

# Type check
mypy src/

# Commit changes
git add .
git commit -m "feat: add my awesome feature"

# Push and create PR
git push origin feature/my-feature
```

---

## Project Structure

```
aiterm/
├── src/aiterm/              # Source code
│   ├── cli/                 # CLI commands (Typer)
│   ├── terminal/            # Terminal backends (iTerm2, etc.)
│   ├── context/             # Context detection
│   ├── claude/              # Claude Code integration
│   └── utils/               # Utilities
├── tests/                   # Test suite (51 tests)
├── docs/                    # MkDocs documentation
├── templates/               # User-facing templates
├── pyproject.toml           # Project configuration
└── README.md
```

---

## Adding a New Command

1. Create command in `src/aiterm/cli/`
2. Add to main app in `src/aiterm/cli/main.py`
3. Write tests in `tests/`
4. Update documentation
5. Submit PR

**Example:**

```python
# src/aiterm/cli/hooks.py
import typer
from rich import print

app = typer.Typer()

@app.command()
def list():
    """List installed hooks."""
    print("[bold]Installed Hooks:[/bold]")
    # Implementation
```

---

## Running Tests

```bash
# All tests
pytest -v

# Specific test file
pytest tests/test_cli.py -v

# Specific test
pytest tests/test_cli.py::test_doctor -v

# With coverage
pytest --cov=aiterm

# Watch mode (requires pytest-watch)
ptw
```

---

## Code Style

**aiterm** follows standard Python conventions:

- **Formatter:** black (line length: 88)
- **Linter:** ruff
- **Type hints:** mypy
- **Docstrings:** Google style

```bash
# Format code
black src/ tests/

# Lint
ruff check src/

# Type check
mypy src/
```

---

## Documentation

Update docs when adding features:

```bash
# Edit docs in docs/
vim docs/guide/my-feature.md

# Preview locally
mkdocs serve
# Visit: http://localhost:8000

# Build
mkdocs build
```

---

## Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes with tests
4. **Run** tests and linters
5. **Update** documentation
6. **Submit** PR with clear description

### PR Checklist

- [ ] Tests pass (`pytest -v`)
- [ ] Code formatted (`black src/ tests/`)
- [ ] Linter clean (`ruff check src/`)
- [ ] Types check (`mypy src/`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow conventions

---

## Commit Message Convention

```bash
feat: add new feature
fix: bug fix
docs: documentation only
style: formatting, missing semicolons, etc
refactor: code restructuring
test: adding tests
chore: maintain, dependencies, etc
```

**Examples:**
```bash
feat: add hook management commands
fix: context detection for nested projects
docs: update Claude integration guide
test: add tests for profile switching
```

---

## Areas Needing Help

### High Priority

- [ ] Multi-terminal support (beyond iTerm2)
- [ ] Hook management system
- [ ] MCP server integration
- [ ] Windows support
- [ ] Linux support

### Documentation

- [ ] Video tutorials
- [ ] More workflow examples
- [ ] Troubleshooting guides
- [ ] API documentation

### Testing

- [ ] Integration tests
- [ ] Performance tests
- [ ] Cross-platform tests

---

## Development Tips

### Use UV for Speed

```bash
# Install dependencies (10-100x faster!)
uv pip install -e ".[dev]"

# Add new dependency
# 1. Edit pyproject.toml
# 2. Run: uv pip install -e ".[dev]"
```

### Test Your Changes Locally

```bash
# Install in editable mode
uv pip install -e ".[dev]"

# Use aiterm directly
aiterm doctor
aiterm detect

# Changes to code are immediately reflected!
```

### Debugging

```bash
# Add breakpoints
import pdb; pdb.set_trace()

# Run pytest with pdb
pytest --pdb

# Verbose output
aiterm --help  # Shows Typer debug info
```

---

## Getting Help

- **Questions:** [GitHub Discussions](https://github.com/Data-Wise/aiterm/discussions)
- **Bugs:** [GitHub Issues](https://github.com/Data-Wise/aiterm/issues)
- **Chat:** (Coming soon)

---

## Code of Conduct

Be kind, respectful, and constructive. We're all here to build something useful!

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
