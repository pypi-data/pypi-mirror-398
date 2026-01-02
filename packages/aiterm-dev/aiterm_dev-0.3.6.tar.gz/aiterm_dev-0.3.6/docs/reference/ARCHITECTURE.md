# ARCHITECTURE

Technical design document for **aiterm** - Terminal optimizer for AI development.

---

## Overview

**aiterm** is a Python CLI tool that optimizes terminals for AI-assisted development workflows. It manages terminal profiles, context detection, Claude Code configuration, and multi-tool integration.

**Design Philosophy:**
- CLI-first architecture (library → CLI → UI)
- Progressive enhancement (MVP → features)
- Medium integration depth (active control, not just config generation)
- ADHD-friendly (fast, clear, actionable)

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────┐
│                   User Interface                     │
│  ┌──────────────────┐      ┌────────────────────┐  │
│  │   CLI (Typer)    │      │  Web UI (Future)   │  │
│  │   - aiterm init  │      │  - Streamlit       │  │
│  │   - aiterm doctor│      │  - Config builder  │  │
│  └────────┬─────────┘      └──────────┬─────────┘  │
└───────────┼────────────────────────────┼────────────┘
            │                            │
┌───────────▼────────────────────────────▼────────────┐
│              Core Library (aiterm/)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  Terminal    │  │   Context    │  │  Claude   │ │
│  │  Backends    │  │  Detection   │  │  Code     │ │
│  │              │  │              │  │  Mgmt     │ │
│  │ - iTerm2     │  │ - Project    │  │ - Hooks   │ │
│  │ - Warp       │  │   types      │  │ - Commands│ │
│  │ - Alacritty  │  │ - Git info   │  │ - Settings│ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │           Utils & Configuration               │  │
│  │  - Config files  - Shell integration         │  │
│  │  - Logging       - Error handling            │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
            │                            │
┌───────────▼────────────────────────────▼────────────┐
│              External Integrations                   │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   iTerm2     │  │  Claude Code │  │  Gemini   │ │
│  │   - Profiles │  │  - Settings  │  │  - Config │ │
│  │   - Python   │  │  - MCP       │  │  - CLI    │ │
│  │     API      │  │  - Hooks     │  │           │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
aiterm/
├── src/aiterm/                  # Main package
│   ├── __init__.py              # Package init, version
│   │
│   ├── cli/                     # CLI layer (Typer)
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point, global commands
│   │   ├── profile.py           # Profile subcommands
│   │   ├── claude.py            # Claude Code subcommands
│   │   ├── gemini.py            # Gemini subcommands (future)
│   │   └── context.py           # Context subcommands
│   │
│   ├── terminal/                # Terminal backends
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract base class
│   │   ├── detector.py          # Auto-detect terminal type
│   │   ├── iterm2.py            # iTerm2 implementation
│   │   ├── warp.py              # Warp implementation (future)
│   │   ├── alacritty.py         # Alacritty implementation (future)
│   │   └── kitty.py             # Kitty implementation (future)
│   │
│   ├── context/                 # Context detection
│   │   ├── __init__.py
│   │   ├── detector.py          # Main detection logic
│   │   ├── git.py               # Git integration
│   │   └── patterns.py          # Detection patterns
│   │
│   ├── claude/                  # Claude Code integration
│   │   ├── __init__.py
│   │   ├── settings.py          # Settings management
│   │   ├── hooks.py             # Hook templates & installation
│   │   ├── commands.py          # Command templates
│   │   └── mcp.py               # MCP server management (future)
│   │
│   ├── gemini/                  # Gemini CLI integration (future)
│   │   ├── __init__.py
│   │   └── config.py
│   │
│   └── utils/                   # Shared utilities
│       ├── __init__.py
│       ├── config.py            # Config file handling
│       ├── shell.py             # Shell integration helpers
│       ├── logger.py            # Logging setup
│       └── exceptions.py        # Custom exceptions
│
├── templates/                   # User-facing templates
│   ├── profiles/                # Terminal profiles
│   │   ├── iterm2/
│   │   │   ├── r-dev.json
│   │   │   ├── python-dev.json
│   │   │   └── ...
│   │   └── themes/
│   │       ├── cool-blues.json
│   │       └── ...
│   ├── hooks/                   # Hook templates
│   │   ├── session-start.sh
│   │   ├── pre-commit.sh
│   │   └── cost-tracker.sh
│   └── commands/                # Command templates
│       ├── workflow/
│       │   ├── recap.md
│       │   └── next.md
│       └── research/
│           └── literature.md
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── test_cli.py              # CLI command tests
│   ├── test_terminal.py         # Terminal backend tests
│   ├── test_context.py          # Context detection tests
│   ├── test_claude.py           # Claude integration tests
│   └── integration/             # Integration tests
│       └── test_iterm2.py
│
├── docs/                        # Documentation (MkDocs)
│   ├── index.md
│   ├── quickstart.md
│   ├── guide/
│   └── reference/
│
├── pyproject.toml               # Project config (Poetry/pip)
├── setup.py                     # Setup script (if needed)
├── requirements.txt             # Dependencies
├── requirements-dev.txt         # Dev dependencies
├── .gitignore
├── README.md
├── LICENSE
├── CHANGELOG.md
├── IDEAS.md
├── ROADMAP.md
├── ARCHITECTURE.md              # This file
└── CLAUDE.md                    # Claude Code guidance
```

---

## Core Modules

### 1. Terminal Module (`src/aiterm/terminal/`)

**Purpose:** Abstract terminal operations across different terminal emulators

**Key Classes:**

```python
# base.py
class TerminalBase(ABC):
    """Abstract base for terminal backends"""

    @abstractmethod
    def detect() -> bool:
        """Detect if this terminal is active"""

    @abstractmethod
    def switch_profile(profile: str) -> None:
        """Switch to a profile"""

    @abstractmethod
    def set_title(title: str) -> None:
        """Set terminal title"""

    @abstractmethod
    def set_user_var(name: str, value: str) -> None:
        """Set user variable (for status bar)"""

# iterm2.py
class ITerm2Terminal(TerminalBase):
    """iTerm2-specific implementation"""

    def detect() -> bool:
        return os.environ.get('TERM_PROGRAM') == 'iTerm.app'

    def switch_profile(profile: str) -> None:
        # Use escape sequence
        print(f'\033]1337;SetProfile={profile}\007', end='')

    def set_title(title: str) -> None:
        # OSC 2 escape sequence
        print(f'\033]2;{title}\007', end='')

# detector.py
def detect_terminal() -> TerminalBase:
    """Auto-detect current terminal"""
    for terminal_class in [ITerm2Terminal, WarpTerminal, ...]:
        if terminal_class.detect():
            return terminal_class()
    return GenericTerminal()
```

**Design Decisions:**
- Abstract base class for extensibility
- Escape sequences for speed (no external deps)
- Python API integration deferred to Phase 2
- Graceful degradation for unsupported features

---

### 2. Context Module (`src/aiterm/context/`)

**Purpose:** Detect project type and context based on file patterns and paths

**Key Functions:**

```python
# detector.py
@dataclass
class Context:
    """Detected context information"""
    type: str           # rpkg, python, node, production, etc.
    icon: str           # 📦, 🐍, 🚨, etc.
    profile: str        # R-Dev, Python-Dev, Production, etc.
    name: str           # Project name
    git_info: GitInfo   # Branch, dirty status

def detect_context(path: Path = None) -> Context:
    """
    Detect context for given path (or cwd)

    Priority order:
    1. Production/AI sessions (safety first)
    2. File-based detection (DESCRIPTION, pyproject.toml, etc.)
    3. Default fallback
    """
    path = path or Path.cwd()

    # Priority overrides
    if 'production' in path.parts or 'prod' in path.parts:
        return Context(type='production', icon='🚨', ...)

    # File-based detection
    if (path / 'DESCRIPTION').exists():
        pkg_name = _extract_r_package_name(path / 'DESCRIPTION')
        return Context(type='rpkg', icon='📦', name=pkg_name, ...)

    # ... more patterns

    return Context(type='default', ...)

# git.py
@dataclass
class GitInfo:
    branch: str
    dirty: bool
    ahead: int = 0
    behind: int = 0

def get_git_info(path: Path) -> GitInfo | None:
    """Get git info for path"""
    # Use gitpython or subprocess
```

**Detection Patterns:**

| Priority | Pattern | Type | Profile |
|----------|---------|------|---------|
| 1 | `*/production/*` | production | Production |
| 1 | `*/claude-sessions/*` | ai-session | AI-Session |
| 2 | `DESCRIPTION` file | rpkg | R-Dev |
| 2 | `pyproject.toml` | python | Python-Dev |
| 2 | `package.json` | node | Node-Dev |
| 2 | `_quarto.yml` | quarto | R-Dev |
| 2 | `mcp-server/` dir | mcp | AI-Session |
| 3 | Default | default | Default |

---

### 3. Claude Module (`src/aiterm/claude/`)

**Purpose:** Manage Claude Code CLI configuration

**Key Classes:**

```python
# settings.py
class ClaudeSettings:
    """Manage Claude Code settings.json"""

    def __init__(self, settings_path: Path = None):
        self.path = settings_path or Path.home() / '.claude' / 'settings.json'
        self._data = None

    def load(self) -> dict:
        """Load settings from file"""
        with open(self.path) as f:
            self._data = json.load(f)
        return self._data

    def save(self) -> None:
        """Save settings to file"""
        with open(self.path, 'w') as f:
            json.dump(self._data, f, indent=2)

    def backup(self) -> Path:
        """Create timestamped backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.path.with_suffix(f'.backup.{timestamp}.json')
        shutil.copy(self.path, backup_path)
        return backup_path

    def add_auto_approvals(self, patterns: list[str]) -> None:
        """Add auto-approval patterns"""
        if 'autoApprove' not in self._data:
            self._data['autoApprove'] = []

        # Merge without duplicates
        existing = set(self._data['autoApprove'])
        new_patterns = [p for p in patterns if p not in existing]
        self._data['autoApprove'].extend(new_patterns)

# hooks.py (Phase 2)
class HookManager:
    """Manage Claude Code hooks"""

    def list_available(self) -> list[Hook]:
        """List available hook templates"""

    def install(self, name: str) -> None:
        """Install a hook from template"""

    def create(self, name: str, trigger: str) -> None:
        """Create custom hook interactively"""
```

**Auto-Approval Presets:**

```python
# Preset definitions
APPROVAL_PRESETS = {
    'safe-reads': [
        'Bash(cat:*)',
        'Bash(ls:*)',
        'Bash(find:*)',
        'Read(*)',
        'Glob(*)',
    ],
    'git-ops': [
        'Bash(git status:*)',
        'Bash(git log:*)',
        'Bash(git diff:*)',
        'Bash(git branch:*)',
    ],
    'dev-tools': [
        # DT's current 40+ patterns
        'Bash(gh pr list:*)',
        'Bash(gh issue list:*)',
        'Bash(mkdocs:*)',
        # ... etc
    ]
}
```

---

### 4. CLI Module (`src/aiterm/cli/`)

**Purpose:** User-facing CLI commands using Typer

**Main Entry Point:**

```python
# main.py
import typer
from rich.console import Console

app = typer.Typer(
    name="aiterm",
    help="Terminal optimizer for AI development",
    add_completion=True,
)
console = Console()

# Register subcommands
from aiterm.cli import profile, claude, context
app.add_typer(profile.app, name="profile")
app.add_typer(claude.app, name="claude")
app.add_typer(context.app, name="context")

@app.command()
def init():
    """Interactive setup wizard"""
    # Terminal detection
    # Profile installation
    # Test context switching
    # Success message

@app.command()
def doctor():
    """Check aiterm installation"""
    # Terminal type
    # Shell integration
    # Profiles
    # Context detection
    # Display results in table (Rich)

@app.callback()
def main(
    version: bool = typer.Option(None, "--version", "-v"),
    verbose: bool = typer.Option(False, "--verbose"),
):
    """aiterm - Terminal optimizer for AI development"""
    if version:
        console.print(f"aiterm version {__version__}")
        raise typer.Exit()

# profile.py
app = typer.Typer(help="Manage terminal profiles")

@app.command("list")
def list_profiles():
    """List available profiles"""

@app.command("install")
def install_profile(name: str):
    """Install a profile"""

@app.command("test")
def test_profile():
    """Test profile switching"""
```

---

## Data Flow

### Context Detection Flow

```
User changes directory
        ↓
zsh hook: chpwd
        ↓
Calls: aiterm context detect
        ↓
┌────────────────────────┐
│  Context Detector      │
│  - Check path patterns │
│  - Check for files     │
│  - Extract git info    │
└──────────┬─────────────┘
           ↓
┌────────────────────────┐
│  Terminal Backend      │
│  - Switch profile      │
│  - Set title          │
│  - Set status vars    │
└────────────────────────┘
```

### Settings Management Flow

```
User: aiterm claude approvals add-preset safe-reads
        ↓
┌────────────────────────┐
│  ClaudeSettings        │
│  - Load settings.json  │
│  - Get preset patterns │
│  - Merge with existing │
│  - Validate            │
│  - Save                │
└────────────────────────┘
        ↓
~/.claude/settings.json updated
```

---

## Configuration Files

### User Config (`~/.config/aiterm/config.yaml`)

```yaml
# User preferences
terminal:
  preferred: iterm2

profiles:
  r-dev:
    name: "R-Dev"
    colors: "cool-blues"
  python-dev:
    name: "Python-Dev"
    colors: "forest-greens"

context:
  auto_detect: true
  git_integration: true

claude:
  settings_path: "~/.claude/settings.json"
  auto_backup: true

statusbar:
  components:
    - icon
    - name
    - branch
    - quota
```

### Shell Integration (`~/.zshrc`)

```bash
# Auto-installed by `aiterm init`

# Hook for context detection
autoload -U add-zsh-hook

_aiterm_chpwd() {
    aiterm context detect --apply 2>/dev/null
}

add-zsh-hook chpwd _aiterm_chpwd

# Shell completion
eval "$(aiterm --install-completion zsh)"

# Aliases
alias ait='aiterm'
alias aitc='aiterm context'
alias aitd='aiterm doctor'
```

---

## Testing Strategy

### Unit Tests (`tests/`)

```python
# test_context.py
def test_detect_r_package(tmp_path):
    """Test R package detection"""
    (tmp_path / 'DESCRIPTION').write_text('Package: testpkg\n')

    context = detect_context(tmp_path)

    assert context.type == 'rpkg'
    assert context.icon == '📦'
    assert context.name == 'testpkg'

# test_claude.py
def test_add_auto_approvals():
    """Test adding auto-approval patterns"""
    settings = ClaudeSettings()
    settings._data = {'autoApprove': []}

    settings.add_auto_approvals(['Bash(ls:*)'])

    assert 'Bash(ls:*)' in settings._data['autoApprove']
```

### Integration Tests (`tests/integration/`)

```python
# test_iterm2.py
@pytest.mark.integration
@pytest.mark.skipif(not iTerm2Terminal.detect(), reason="Not in iTerm2")
def test_profile_switching():
    """Test actual profile switching in iTerm2"""
    terminal = ITerm2Terminal()
    terminal.switch_profile('R-Dev')
    # How to verify? Check escape sequence output?
```

---

## Performance Considerations

### Startup Time
**Goal:** < 500ms for typical commands

**Strategies:**
- Lazy imports (only load what's needed)
- Cache terminal detection
- Minimize file I/O
- No external API calls in critical path

```python
# Use lazy imports
@app.command()
def hooks():
    from aiterm.claude.hooks import HookManager
    # Only import when command is used
```

### Context Detection Speed
**Goal:** < 100ms per detection

**Optimizations:**
- Path checking before file I/O
- Early return on matches
- Cache git info (TTL: 5s)
- Parallel file checks (if needed)

---

## Error Handling

### Exception Hierarchy

```python
# utils/exceptions.py
class AiTermError(Exception):
    """Base exception for aiterm"""

class TerminalNotSupported(AiTermError):
    """Terminal not supported"""

class ClaudeSettingsError(AiTermError):
    """Claude settings error"""

class ProfileNotFound(AiTermError):
    """Profile not found"""
```

### User-Friendly Messages

```python
try:
    settings.load()
except FileNotFoundError:
    console.print(
        "[red]Error:[/red] Claude Code settings not found.\n"
        "[yellow]Tip:[/yellow] Run Claude Code at least once to create settings.",
        style="bold"
    )
    raise typer.Exit(1)
```

---

## Dependencies

### Core Dependencies
```toml
[tool.poetry.dependencies]
python = "^3.10"
typer = "^0.9"           # CLI framework
rich = "^13.0"           # Terminal formatting
pyyaml = "^6.0"          # Config files
gitpython = "^3.1"       # Git integration (or use subprocess)

[tool.poetry.dev-dependencies]
pytest = "^7.0"
pytest-cov = "^4.0"
black = "^23.0"
ruff = "^0.1"
mypy = "^1.0"
```

### Optional Dependencies
```toml
[tool.poetry.extras]
questionary = ["questionary"]  # Interactive prompts
iterm2 = ["iterm2"]           # iTerm2 Python API (Phase 2)
```

---

## Deployment

### Distribution via PyPI

```bash
# Build
poetry build

# Publish
poetry publish

# Install
pip install aiterm
```

### Entry Point

```toml
[tool.poetry.scripts]
aiterm = "aiterm.cli.main:app"
```

---

## Future Enhancements

### Phase 2: Advanced Features
- iTerm2 Python API integration
- Hook management system
- Command template library
- MCP server configuration

### Phase 3: Multi-Terminal
- Warp support
- Alacritty support
- Kitty support
- Windows Terminal (limited)

### Phase 4: Web UI
- Streamlit configuration builder
- Visual profile editor
- Template marketplace

---

## References

- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [iTerm2 Python API](https://iterm2.com/python-api/)
- [Claude Code Documentation](https://claude.com/code)

---

**Last Updated:** 2025-12-16
**Version:** 0.1.0-dev (95% complete)
**Author:** DT
**Status:** Phase 1 MVP complete, awaiting PR merge
