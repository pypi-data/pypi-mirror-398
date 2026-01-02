# Architecture

Technical architecture and design decisions for **aiterm**.

---

## Design Principles

### 1. CLI-First

- Core logic in library (`src/aiterm/`)
- CLI is thin wrapper (commands in `cli/`)
- Testable, reusable components
- Future: Web UI, API, plugins

### 2. Progressive Enhancement

- Start simple (MVP in 1 week)
- Add features incrementally
- Maintain backwards compatibility
- Don't break existing workflows

### 3. Terminal Abstraction

- Abstract base for terminals
- iTerm2 first, others later
- Graceful degradation
- Feature detection, not assumptions

### 4. Medium Integration Depth

- Active terminal control (escape sequences, API)
- Not just config generation
- Not full IDE replacement
- Sweet spot: useful without overwhelming

---

## Project Structure

```
aiterm/
├── src/aiterm/                # Main package
│   ├── __init__.py            # Package info
│   ├── cli/                   # CLI commands
│   │   ├── __init__.py
│   │   └── main.py            # Main entry, Typer app
│   ├── terminal/              # Terminal backends
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract base class
│   │   ├── iterm2.py          # iTerm2 implementation
│   │   └── detector.py        # Auto-detect terminal
│   ├── context/               # Context detection
│   │   ├── __init__.py
│   │   └── detector.py        # Project type detection
│   ├── claude/                # Claude Code integration
│   │   ├── __init__.py
│   │   ├── settings.py        # Settings management
│   │   ├── hooks.py           # Hook management (v0.2.0)
│   │   └── commands.py        # Command templates (v0.2.0)
│   └── utils/                 # Utilities
│       ├── __init__.py
│       ├── config.py          # Config file handling
│       └── shell.py           # Shell integration
├── templates/                 # User-facing templates
│   ├── profiles/              # iTerm2 profile JSON
│   ├── hooks/                 # Hook templates
│   └── commands/              # Command templates
├── tests/                     # Test suite
├── docs/                      # Documentation (MkDocs)
├── pyproject.toml             # Project config
└── README.md
```

---

## Core Components

### CLI Layer (`src/aiterm/cli/`)

**main.py:**
- Typer app initialization
- Command registration
- Global options (--version, --verbose)
- Error handling

**Design:**
- Each major feature gets its own module
- Subcommands organized with Typer sub-apps
- Thin layer: delegates to library functions

**Example:**
```python
# src/aiterm/cli/main.py
app = typer.Typer()
context_app = typer.Typer()
app.add_typer(context_app, name="context")

@context_app.command("detect")
def context_detect(path: Path):
    from aiterm.context import detect_context
    result = detect_context(path)
    print_result(result)
```

---

### Terminal Layer (`src/aiterm/terminal/`)

**base.py:**
```python
class Terminal(ABC):
    @abstractmethod
    def switch_profile(self, profile: str) -> bool:
        """Switch terminal profile"""

    @abstractmethod
    def set_title(self, title: str) -> bool:
        """Set tab title"""
```

**iterm2.py:**
- Implements Terminal interface
- Uses escape sequences (iTerm2 proprietary extensions)
- Python API integration (future)

**detector.py:**
- Auto-detects terminal from environment
- Checks `TERM_PROGRAM`, `TERM`, etc.
- Returns appropriate Terminal instance

---

### Context Detection (`src/aiterm/context/`)

**detector.py:**

**Detection strategy:**
1. Path-based detection (production/, claude-sessions/)
2. File marker detection (DESCRIPTION, pyproject.toml)
3. Git information (branch, dirty status)
4. Fallback to default

**ContextInfo data class:**
```python
@dataclass
class ContextInfo:
    type: ContextType
    name: str
    profile: str
    icon: str
    path: Path
    branch: Optional[str]
    is_dirty: bool
```

**8 Context Types:**
- Production (path-based)
- AI Session (path-based)
- R Package (DESCRIPTION file)
- Python (pyproject.toml)
- Node.js (package.json)
- Quarto (_quarto.yml)
- Emacs (.spacemacs)
- Dev Tools (.git + scripts/)

---

### Claude Integration (`src/aiterm/claude/`)

**settings.py:**

**ClaudeSettings data class:**
```python
@dataclass
class ClaudeSettings:
    path: Path
    allow_list: List[str]
    deny_list: List[str]
    hooks: Dict[str, Any]
```

**Functions:**
- `load_settings()` - Read ~/.claude/settings.json
- `save_settings()` - Write settings atomically
- `backup_settings()` - Timestamped backup
- `add_preset_to_settings()` - Merge preset permissions

**Presets:**
8 curated permission presets (safe-reads, git-ops, etc.)
defined as Python dicts.

---

## Data Flow

### Context Detection Flow

```
User runs: ait detect ~/project
    ↓
CLI (main.py)
    ↓
detect_context(path) → ContextInfo
    ↓
Display with Rich Table
```

### Context Application Flow

```
User runs: ait switch ~/project
    ↓
CLI (main.py)
    ↓
detect_context(path) → ContextInfo
    ↓
detect_terminal() → Terminal instance
    ↓
terminal.switch_profile(context.profile)
terminal.set_title(context.title)
    ↓
iTerm2 updates visually
```

### Settings Management Flow

```
User runs: ait claude approvals add python-dev
    ↓
load_settings() → ClaudeSettings
    ↓
get_preset("python-dev") → Dict
    ↓
add_preset_to_settings() → modified ClaudeSettings
    ↓
save_settings() → write to disk
```

---

## Testing Strategy

### Unit Tests (51 tests, 83% coverage)

**test_cli.py:**
- Command parsing
- Option handling
- Output formatting

**test_context.py:**
- Context detection for 8 types
- Git integration
- Title generation

**test_iterm2.py:**
- Terminal detection
- Profile switching
- Escape sequence generation

**test_claude_settings.py:**
- Settings loading/saving
- Preset management
- Backup functionality

### Integration Tests (future)

- End-to-end command execution
- iTerm2 integration (requires iTerm2)
- Claude Code hook testing

---

## iTerm2 Integration

### Escape Sequences

**Profile switching:**
```
\033]1337;SetProfile=ProfileName\007
```

**Tab title:**
```
\033]0;Title Text\007
```

**User variables:**
```
\033]1337;SetUserVar=key=base64value\007
```

### Detection

Check `TERM_PROGRAM` environment variable:
```python
def is_iterm2() -> bool:
    return os.getenv("TERM_PROGRAM") == "iTerm.app"
```

---

## Configuration

### System Files

```
~/.claude/settings.json        # Claude Code settings
~/.claude/hooks/               # Claude Code hooks
~/.config/aiterm/              # aiterm config (v0.2.0)
```

### Project Files

```
.claude/settings.local.json    # Project-specific settings
pyproject.toml                 # Python project marker
package.json                   # Node.js project marker
DESCRIPTION                    # R package marker
```

---

## Future Architecture (v0.2.0+)

### Hook System

```python
# src/aiterm/claude/hooks.py
class HookManager:
    def list_hooks(self) -> List[Hook]
    def install_hook(self, name: str, template: str)
    def configure_hook(self, name: str, config: Dict)
```

### MCP Integration

```python
# src/aiterm/mcp/manager.py
class MCPManager:
    def discover_servers(self) -> List[MCPServer]
    def configure_server(self, name: str)
    def test_server(self, name: str) -> TestResult
```

### Multi-Terminal Support

```python
# src/aiterm/terminal/
├── base.py          # Abstract Terminal
├── iterm2.py        # iTerm2
├── wezterm.py       # WezTerm (future)
├── kitty.py         # Kitty (future)
└── detector.py      # Auto-detection
```

---

## Dependencies

### Core

- **typer** - Modern CLI framework with type hints
- **rich** - Beautiful terminal output
- **questionary** - Interactive prompts
- **pyyaml** - YAML parsing

### Development

- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **black** - Code formatting
- **ruff** - Fast linter
- **mypy** - Type checking

### Documentation

- **mkdocs** - Documentation generator
- **mkdocs-material** - Material theme
- **pymdown-extensions** - Markdown extensions

---

## Performance

### Startup Time

Target: < 100ms for basic commands

Optimizations:
- Lazy imports
- Minimal dependencies
- No heavy I/O at startup

### Context Detection

Target: < 50ms

Strategy:
- Check path first (fastest)
- File existence checks (fast)
- File content only if needed (slower)
- Git info last (slowest)

---

## Security

### Settings Management

- Atomic writes (temp file + rename)
- Automatic backups before changes
- Permission validation
- No credential storage

### Command Execution

- No shell injection (uses subprocess with array)
- Escape sequence sanitization
- Path validation

---

## Maintainability

### Code Organization

- Single responsibility per module
- Clear separation of concerns
- Type hints everywhere
- Comprehensive docstrings

### Testing

- 51 tests, 83% coverage
- Fast test suite (< 1 second)
- Mocking for external dependencies
- Real integration tests in CI

### Documentation

- Comprehensive user docs (MkDocs)
- API documentation (docstrings)
- Architecture documentation (this file)
- Examples in every guide

---

## Resources

- **Contributing Guide:** [Contributing](contributing.md)
- **CLI Reference:** [Commands](../reference/commands.md)
- **Source Code:** [GitHub](https://github.com/Data-Wise/aiterm)
