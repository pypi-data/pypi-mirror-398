# aiterm Architecture Documentation

**Version:** 0.1.0-dev
**Last Updated:** 2025-12-21

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flows](#data-flows)
4. [Sequence Diagrams](#sequence-diagrams)
5. [State Machines](#state-machines)
6. [Design Patterns](#design-patterns)
7. [File Structure](#file-structure)

---

## System Overview

### High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface"
        CLI[CLI Layer<br/>Typer]
    end

    subgraph "Core Library"
        Terminal[Terminal Backend<br/>Abstraction]
        Context[Context Detection<br/>Engine]
        Settings[Settings Manager]
    end

    subgraph "Integrations"
        ITerm2[iTerm2<br/>Integration]
        Claude[Claude Code<br/>Integration]
        MCP[MCP Server<br/>Management]
    end

    CLI --> Terminal
    CLI --> Context
    CLI --> Settings

    Terminal --> ITerm2
    Settings --> Claude
    Settings --> MCP

    Context --> Terminal
    Context -.-> Claude
```

**Key Components:**
- **CLI Layer** - User-facing commands (Typer framework)
- **Terminal Backend** - Abstracted terminal operations
- **Context Detection** - Project type detection
- **Settings Manager** - Configuration management
- **Integrations** - iTerm2, Claude Code, MCP servers

---

### Technology Stack

```mermaid
graph LR
    subgraph "Runtime"
        Python[Python 3.10+]
    end

    subgraph "CLI Framework"
        Typer[Typer<br/>CLI framework]
        Rich[Rich<br/>Terminal output]
        Quest[Questionary<br/>Interactive prompts]
    end

    subgraph "Build & Distribution"
        UV[UV<br/>Package manager]
        Hatchling[Hatchling<br/>Build backend]
    end

    subgraph "Testing"
        Pytest[pytest<br/>Test framework]
        Coverage[pytest-cov<br/>Coverage]
    end

    Python --> Typer
    Python --> Rich
    Python --> Quest
    Python --> UV
    UV --> Hatchling
    Python --> Pytest
```

---

## Component Architecture

### 1. Terminal Backend Architecture

```mermaid
graph TB
    subgraph "Terminal Backend"
        Base[TerminalBackend<br/>Abstract Base Class]
        ITerm2[iTerm2Terminal<br/>Implementation]
        Wezterm[WeztermTerminal<br/>Future]
        Alacritty[AlacrittyTerminal<br/>Future]

        Base -.-> ITerm2
        Base -.-> Wezterm
        Base -.-> Alacritty
    end

    subgraph "Operations"
        Profile[switch_profile]
        Title[set_title]
        Status[set_status_var]
        Query[get_current_profile]
    end

    ITerm2 --> Profile
    ITerm2 --> Title
    ITerm2 --> Status
    ITerm2 --> Query

    subgraph "iTerm2 Integration"
        Escape[Escape Sequences]
        API[Python API<br/>Future]
    end

    ITerm2 --> Escape
    ITerm2 -.-> API
```

**Design Pattern:** Abstract Factory + Strategy

**Key Abstractions:**
- `TerminalBackend` - Base interface for all terminals
- `iTerm2Terminal` - iTerm2-specific implementation
- Future: Wezterm, Alacritty, Kitty support

---

### 2. Context Detection Architecture

```mermaid
graph TB
    subgraph "Context Detection Engine"
        Detector[ContextDetector<br/>Base Class]
        Registry[DetectorRegistry<br/>Singleton]
    end

    subgraph "Built-in Detectors"
        Prod[ProductionDetector<br/>Priority: 1]
        AI[AISessionDetector<br/>Priority: 2]
        R[RPackageDetector<br/>Priority: 3]
        Py[PythonDetector<br/>Priority: 4]
        Node[NodeDetector<br/>Priority: 5]
        Quarto[QuartoDetector<br/>Priority: 6]
        MCP[MCPDetector<br/>Priority: 7]
        Dev[DevToolsDetector<br/>Priority: 8]
        Default[DefaultDetector<br/>Priority: 9]
    end

    subgraph "Custom Detectors"
        Custom[User-Defined<br/>Detectors]
    end

    Registry --> Prod
    Registry --> AI
    Registry --> R
    Registry --> Py
    Registry --> Node
    Registry --> Quarto
    Registry --> MCP
    Registry --> Dev
    Registry --> Default
    Registry -.-> Custom

    Detector <.. Prod
    Detector <.. AI
    Detector <.. R
    Detector <.. Custom
```

**Design Pattern:** Chain of Responsibility + Priority Queue

**Detection Flow:**
1. User calls `detect_context(path)`
2. Registry iterates detectors by priority
3. First detector that returns non-null wins
4. Return `Context` object with profile, title, metadata

---

### 3. Settings Management Architecture

```mermaid
graph TB
    subgraph "Settings Manager"
        Manager[SettingsManager<br/>Singleton]
        Validator[ConfigValidator]
        Backup[BackupManager]
    end

    subgraph "Configuration Files"
        Aiterm[~/.aiterm/config.json]
        Claude[~/.claude/settings.json]
    end

    subgraph "Operations"
        Read[read_settings]
        Write[write_settings]
        Validate[validate_config]
        Apply[apply_preset]
    end

    Manager --> Read
    Manager --> Write
    Manager --> Validate
    Manager --> Apply

    Read --> Aiterm
    Read --> Claude
    Write --> Aiterm
    Write --> Claude
    Validate --> Validator
    Write --> Backup

    Backup -.-> Claude
```

**Design Pattern:** Singleton + Template Method

**Key Features:**
- Automatic backups before writes
- JSON validation
- Preset management (8 presets)
- Merge strategies (replace vs merge)

---

### 4. CLI Command Architecture

```mermaid
graph TB
    subgraph "CLI Entry Point"
        Main[aiterm<br/>Main Command]
    end

    subgraph "Command Groups"
        Core[Core Commands<br/>doctor, detect]
        Profile[Profile Commands<br/>list, switch]
        Claude[Claude Commands<br/>approvals, settings]
        MCP[MCP Commands<br/>list, test, validate]
    end

    subgraph "Command Implementation"
        Handler[Command Handler]
        Validator[Input Validator]
        Output[Output Formatter<br/>Rich]
    end

    Main --> Core
    Main --> Profile
    Main --> Claude
    Main -.-> MCP

    Core --> Handler
    Profile --> Handler
    Claude --> Handler

    Handler --> Validator
    Handler --> Output
```

**Design Pattern:** Command Pattern + Decorator

**Command Structure:**
```python
@app.command()
def doctor():
    """Check aiterm installation"""
    # 1. Validate environment
    # 2. Check dependencies
    # 3. Format output (Rich)
    # 4. Return exit code
```

---

## Data Flows

### 1. Context Detection Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Detector
    participant Terminal
    participant iTerm2

    User->>CLI: cd ~/projects/RMediation
    activate CLI

    CLI->>Detector: detect_context(pwd)
    activate Detector

    Detector->>Detector: Check DESCRIPTION file
    Detector->>Detector: Check R/ directory
    Detector->>Detector: Parse package name/version

    Detector-->>CLI: Context(type=r-package, profile=R-Dev)
    deactivate Detector

    CLI->>Terminal: switch_profile("R-Dev")
    activate Terminal
    Terminal->>iTerm2: ESC]1337;SetProfile=R-Dev
    iTerm2-->>Terminal: Profile switched
    deactivate Terminal

    CLI->>Terminal: set_title("RMediation v1.0.0")
    activate Terminal
    Terminal->>iTerm2: ESC]0;RMediation v1.0.0
    iTerm2-->>Terminal: Title set
    deactivate Terminal

    CLI->>Terminal: set_status_var("project_type", "R PKG")
    activate Terminal
    Terminal->>iTerm2: ESC]1337;SetUserVar=...
    iTerm2-->>Terminal: Variable set
    deactivate Terminal

    CLI-->>User: Context switched ✅
    deactivate CLI
```

**Performance:**
- Detection: < 50ms
- Profile switch: < 150ms
- Total: < 200ms

---

### 2. Auto-Approval Application Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Settings
    participant Backup
    participant Claude

    User->>CLI: aiterm claude approvals set r-package
    activate CLI

    CLI->>Settings: read_claude_settings()
    activate Settings
    Settings->>Claude: Read ~/.claude/settings.json
    Claude-->>Settings: Current settings
    Settings-->>CLI: settings dict
    deactivate Settings

    CLI->>Backup: create_backup(settings)
    activate Backup
    Backup->>Claude: Write ~/.claude/settings.json.backup.TIMESTAMP
    Backup-->>CLI: Backup created
    deactivate Backup

    CLI->>Settings: apply_approval_preset("r-package")
    activate Settings
    Settings->>Settings: Load r-package preset (35 tools)
    Settings->>Settings: Merge with current approvals
    Settings->>Settings: Validate JSON structure
    Settings-->>CLI: Updated settings
    deactivate Settings

    CLI->>Settings: write_claude_settings(updated)
    activate Settings
    Settings->>Claude: Write ~/.claude/settings.json
    Claude-->>Settings: Write complete
    Settings-->>CLI: Success
    deactivate Settings

    CLI-->>User: ✅ Applied r-package preset (35 tools)
    deactivate CLI
```

**Safety Features:**
- Automatic backup before write
- JSON validation
- Rollback on error
- Backup retention (last 5)

---

### 3. Profile Switching Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Terminal
    participant iTerm2
    participant Shell

    User->>CLI: aiterm profile switch R-Dev
    activate CLI

    CLI->>Terminal: get_terminal()
    activate Terminal
    Terminal->>Terminal: Detect terminal type
    Terminal-->>CLI: iTerm2Terminal instance
    deactivate Terminal

    CLI->>Terminal: switch_profile("R-Dev")
    activate Terminal

    Terminal->>Terminal: Validate profile exists
    Terminal->>iTerm2: Send escape sequence<br/>ESC]1337;SetProfile=R-Dev BEL
    iTerm2->>iTerm2: Switch profile
    iTerm2->>Shell: Update environment
    iTerm2-->>Terminal: Profile switched

    Terminal-->>CLI: Success
    deactivate Terminal

    CLI->>Terminal: set_title("R Development")
    activate Terminal
    Terminal->>iTerm2: ESC]0;R Development BEL
    iTerm2-->>Terminal: Title set
    deactivate Terminal

    CLI-->>User: ✅ Switched to R-Dev
    deactivate CLI
```

---

## Sequence Diagrams

### 4. Doctor Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Checks
    participant System

    User->>CLI: aiterm doctor
    activate CLI

    CLI->>Checks: check_python_version()
    activate Checks
    Checks->>System: python --version
    System-->>Checks: 3.11.5
    Checks-->>CLI: ✅ Python 3.11.5
    deactivate Checks

    CLI->>Checks: check_terminal()
    activate Checks
    Checks->>System: $TERM_PROGRAM
    System-->>Checks: iTerm.app
    Checks->>System: iTerm2 version
    System-->>Checks: Build 3.5.0
    Checks-->>CLI: ✅ iTerm2 (Build 3.5.0)
    deactivate Checks

    CLI->>Checks: check_claude_code()
    activate Checks
    Checks->>System: ~/.claude/ exists?
    System-->>Checks: Yes
    Checks->>System: claude --version
    System-->>Checks: 0.2.0
    Checks-->>CLI: ✅ Claude Code 0.2.0
    deactivate Checks

    CLI->>Checks: check_config()
    activate Checks
    Checks->>System: ~/.aiterm/config.json exists?
    System-->>Checks: Yes
    Checks->>System: Validate JSON
    System-->>Checks: Valid
    Checks-->>CLI: ✅ Settings OK
    deactivate Checks

    CLI-->>User: All checks passed! ✅
    deactivate CLI
```

---

### 5. Profile List Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Terminal
    participant Config

    User->>CLI: aiterm profile list
    activate CLI

    CLI->>Config: read_config()
    activate Config
    Config->>Config: Load ~/.aiterm/config.json
    Config-->>CLI: Config dict
    deactivate Config

    CLI->>Terminal: get_available_profiles()
    activate Terminal
    Terminal->>Config: profiles section
    Terminal->>Terminal: Parse profile definitions
    Terminal-->>CLI: List of profiles
    deactivate Terminal

    loop For each profile
        CLI->>CLI: Format profile info
        CLI->>CLI: Add theme, triggers, description
    end

    CLI-->>User: Display formatted profile list
    deactivate CLI
```

---

## State Machines

### 1. Context Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Unknown: Start
    Unknown --> Detected: Context found
    Unknown --> Unknown: No context
    Detected --> Switched: Apply profile
    Switched --> Active: Profile applied
    Active --> Detected: Directory change
    Active --> [*]: Exit terminal
```

**States:**
- **Unknown** - No context detected
- **Detected** - Context identified
- **Switched** - Profile switching in progress
- **Active** - Profile active and in use

---

### 2. Settings Management Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Unloaded
    Unloaded --> Loading: Read request
    Loading --> Loaded: Success
    Loading --> Error: Parse fail
    Loaded --> Modifying: Update request
    Modifying --> Validating: Changes made
    Validating --> BackingUp: Validation passed
    Validating --> Error: Validation failed
    BackingUp --> Writing: Backup created
    Writing --> Loaded: Write success
    Writing --> Error: Write fail
    Error --> Loaded: Rollback
    Loaded --> [*]: Session end
```

**States:**
- **Unloaded** - Settings not read
- **Loading** - Reading from disk
- **Loaded** - Settings in memory
- **Modifying** - Changes being made
- **Validating** - Checking validity
- **BackingUp** - Creating backup
- **Writing** - Writing to disk
- **Error** - Error state (with rollback)

---

### 3. Profile Switching State

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Detecting: cd command
    Detecting --> Matched: Context found
    Detecting --> Idle: No match
    Matched --> Switching: Profile selected
    Switching --> Applied: Escape sequence sent
    Switching --> Failed: Terminal error
    Applied --> Updating: Set title/vars
    Updating --> Idle: Complete
    Failed --> Idle: Fallback to default
```

---

## Design Patterns

### 1. Singleton Pattern

**Used For:** Settings Manager, Detector Registry

```python
class SettingsManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._load_settings()
        self._initialized = True
```

**Why:** Single source of truth for settings

---

### 2. Factory Pattern

**Used For:** Terminal backend creation

```python
def get_terminal() -> TerminalBackend:
    """Factory function for terminal backends"""
    term_program = os.getenv("TERM_PROGRAM", "")

    if "iTerm" in term_program:
        return iTerm2Terminal()
    elif "WezTerm" in term_program:
        return WeztermTerminal()  # Future
    else:
        return DefaultTerminal()  # Fallback
```

**Why:** Abstract terminal selection

---

### 3. Strategy Pattern

**Used For:** Context detection

```python
class ContextDetector(ABC):
    @abstractmethod
    def detect(self, path: str) -> Context | None:
        """Detect context from path"""
        pass

class RPackageDetector(ContextDetector):
    def detect(self, path: str) -> Context | None:
        if self._has_file(path, "DESCRIPTION"):
            # R package logic
            return Context(...)
        return None
```

**Why:** Pluggable detection strategies

---

### 4. Chain of Responsibility

**Used For:** Detector priority chain

```python
class DetectorRegistry:
    def detect(self, path: str) -> Context | None:
        # Try detectors in priority order
        for detector in sorted(self.detectors, key=lambda d: d.priority):
            context = detector.detect(path)
            if context:
                return context  # First match wins
        return None  # No matches
```

**Why:** First-match-wins with priority

---

### 5. Template Method

**Used For:** Settings operations

```python
class SettingsManager:
    def apply_preset(self, preset_name: str):
        # Template method
        settings = self.read_settings()       # 1. Read
        self.backup_settings(settings)        # 2. Backup
        updated = self._merge_preset(settings, preset_name)  # 3. Merge
        self.validate_settings(updated)       # 4. Validate
        self.write_settings(updated)          # 5. Write

    def _merge_preset(self, settings, preset):
        # Subclass hook (override for custom merge)
        pass
```

**Why:** Consistent operation flow

---

## File Structure

### Project Layout

```
aiterm/
├── src/aiterm/              # Main package
│   ├── __init__.py
│   ├── cli/                 # CLI commands
│   │   ├── __init__.py
│   │   ├── main.py          # Entry point
│   │   ├── core.py          # doctor, detect
│   │   ├── profile.py       # profile commands
│   │   ├── claude.py        # Claude Code commands
│   │   └── mcp.py           # MCP commands (future)
│   ├── terminal/            # Terminal backends
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract base
│   │   ├── iterm2.py        # iTerm2 implementation
│   │   ├── wezterm.py       # Wezterm (future)
│   │   └── detector.py      # Terminal detection
│   ├── context/             # Context detection
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract detector
│   │   ├── registry.py      # Detector registry
│   │   ├── detectors/       # Built-in detectors
│   │   │   ├── production.py
│   │   │   ├── ai_session.py
│   │   │   ├── r_package.py
│   │   │   ├── python.py
│   │   │   ├── nodejs.py
│   │   │   ├── quarto.py
│   │   │   ├── mcp.py
│   │   │   └── dev_tools.py
│   │   └── types.py         # Context type definitions
│   ├── claude/              # Claude Code integration
│   │   ├── __init__.py
│   │   ├── settings.py      # Settings management
│   │   ├── presets.py       # Auto-approval presets
│   │   ├── hooks.py         # Hook management (future)
│   │   └── commands.py      # Command templates (future)
│   ├── utils/               # Utilities
│   │   ├── __init__.py
│   │   ├── config.py        # Config file handling
│   │   ├── shell.py         # Shell integration
│   │   └── exceptions.py    # Custom exceptions
│   └── version.py           # Version info
├── templates/               # User-facing templates
│   ├── profiles/            # iTerm2 profile JSON
│   │   ├── R-Dev.json
│   │   ├── Python-Dev.json
│   │   └── ...
│   ├── hooks/               # Hook templates (future)
│   └── commands/            # Command templates (future)
├── tests/                   # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/                    # Documentation
│   ├── api/
│   ├── architecture/
│   ├── guides/
│   └── troubleshooting/
├── pyproject.toml           # Project config
└── README.md
```

---

### Module Dependencies

```mermaid
graph TB
    subgraph "Public API"
        CLI[cli/]
    end

    subgraph "Core Library"
        Terminal[terminal/]
        Context[context/]
        Settings[claude/]
        Utils[utils/]
    end

    CLI --> Terminal
    CLI --> Context
    CLI --> Settings

    Terminal --> Utils
    Context --> Utils
    Settings --> Utils

    Context -.-> Terminal
```

**Dependency Rules:**
- CLI depends on Core Library
- Core Library is self-contained
- Utils are leaf modules (no dependencies)
- Context may trigger Terminal operations
- No circular dependencies

---

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**
   - Load detectors on-demand
   - Cache detector results
   - Lazy import heavy modules

2. **Caching**
   - Cache context detection results
   - Cache settings reads (TTL: 5s)
   - Cache terminal type detection

3. **Async Operations** (Future)
   - Parallel detector execution
   - Async file I/O
   - Non-blocking profile switching

---

### Performance Targets

| Operation | Target | Current | Status |
|-----------|--------|---------|--------|
| Context detection | < 50ms | ~30ms | ✅ |
| Profile switching | < 150ms | ~100ms | ✅ |
| Settings read | < 10ms | ~5ms | ✅ |
| Settings write | < 50ms | ~40ms | ✅ |
| Doctor check | < 200ms | ~150ms | ✅ |

---

## Security Considerations

### File Permissions

- `~/.aiterm/config.json` - 600 (user read/write only)
- `~/.claude/settings.json` - 600 (user read/write only)
- Backups - 600 (user read/write only)

### Input Validation

- Profile names - Alphanumeric + dashes
- Paths - Absolute paths only, no symlink following
- Settings - JSON schema validation
- Presets - Whitelist of known presets

### Escape Sequence Safety

- No user input in escape sequences (XSS risk)
- Whitelist of allowed sequences
- Sanitize all title/variable values

---

## Extension Points

### Adding New Terminal Backend

```python
from aiterm.terminal.base import TerminalBackend

class MyTerminal(TerminalBackend):
    def switch_profile(self, name: str) -> bool:
        # Custom implementation
        pass

    def set_title(self, text: str) -> bool:
        # Custom implementation
        pass
```

### Adding Custom Detector

```python
from aiterm.context.base import ContextDetector
from aiterm.context import register_detector

class MyDetector(ContextDetector):
    priority = 10

    def detect(self, path: str) -> Context | None:
        # Custom logic
        pass

register_detector(MyDetector())
```

---

## Future Architecture

### Phase 2 Additions

```mermaid
graph TB
    subgraph "Phase 2"
        Hook[Hook Manager]
        MCP[MCP Creator]
        Plugin[Plugin System]
    end

    subgraph "Existing"
        CLI[CLI]
        Terminal[Terminal]
        Context[Context]
    end

    CLI -.-> Hook
    CLI -.-> MCP
    CLI -.-> Plugin

    Hook -.-> Terminal
    MCP -.-> Context
```

**Planned Features:**
- Hook management system
- MCP server creation wizard
- Plugin architecture
- Remote terminal support
- Web UI

---

## Additional Diagrams

### Installation & Setup Flow

```mermaid
flowchart TD
    Start([User installs aiterm]) --> Install{Installation<br/>Method?}

    Install -->|Homebrew| Brew[brew install data-wise/tap/aiterm]
    Install -->|UV| UV[uv tool install git+...]
    Install -->|pipx| Pipx[pipx install git+...]

    Brew --> Verify
    UV --> Verify
    Pipx --> Verify

    Verify[aiterm doctor] --> Check{All checks<br/>passed?}

    Check -->|No| Fix[Fix issues]
    Fix --> Verify

    Check -->|Yes| Detect[aiterm detect]
    Detect --> Context{Context<br/>detected?}

    Context -->|Yes| Auto[Auto-switching enabled]
    Context -->|No| Manual[Manual profile selection]

    Auto --> ListProfiles[aiterm profile list]
    Manual --> ListProfiles

    ListProfiles --> SetApprovals[aiterm claude approvals set]
    SetApprovals --> Done([Setup Complete])

    style Start fill:#e1f5e1
    style Done fill:#e1f5e1
    style Check fill:#fff4e6
    style Context fill:#fff4e6
```

**User Journey:**
1. Install via preferred method (Homebrew/UV/pipx)
2. Run `aiterm doctor` to verify installation
3. Fix any issues identified
4. Test context detection with `aiterm detect`
5. Review available profiles
6. Set auto-approval presets for Claude Code
7. Begin using aiterm!

---

### Error Handling & Recovery Flow

```mermaid
flowchart TD
    Operation[User Operation] --> Try{Try<br/>Operation}

    Try -->|Success| Log[Log success]
    Try -->|Error| Catch[Catch Exception]

    Catch --> ErrorType{Error<br/>Type?}

    ErrorType -->|ProfileNotFound| PNF[Profile not found error]
    ErrorType -->|TerminalUnsupported| TU[Terminal unsupported]
    ErrorType -->|PermissionDenied| PD[Permission denied]
    ErrorType -->|ConfigError| CE[Config error]
    ErrorType -->|Other| OE[General error]

    PNF --> Recover1{Recovery<br/>Available?}
    TU --> Recover2{Fallback<br/>Available?}
    PD --> Recover3{Fix<br/>Permissions?}
    CE --> Recover4{Restore<br/>Backup?}
    OE --> Recover5{Retry?}

    Recover1 -->|Yes| DefaultProfile[Use default profile]
    Recover1 -->|No| UserError1[Show error to user]

    Recover2 -->|Yes| ReducedFeatures[Operate with reduced features]
    Recover2 -->|No| UserError2[Explain limitation]

    Recover3 -->|Yes| FixPerms[chmod 600 config files]
    Recover3 -->|No| UserError3[Guide user to fix]

    Recover4 -->|Yes| Rollback[Restore from backup]
    Recover4 -->|No| UserError4[Show validation errors]

    Recover5 -->|Yes| Retry[Retry operation]
    Recover5 -->|No| UserError5[Show error details]

    DefaultProfile --> Log
    ReducedFeatures --> Log
    FixPerms --> Retry
    Rollback --> Retry
    Retry --> Try

    UserError1 --> Exit
    UserError2 --> Exit
    UserError3 --> Exit
    UserError4 --> Exit
    UserError5 --> Exit

    Log --> Success([Operation Complete])

    Exit([Exit with error code])

    style Operation fill:#e1f5e1
    style Success fill:#e1f5e1
    style Exit fill:#ffe1e1
    style ErrorType fill:#fff4e6
```

**Error Handling Strategy:**
- **Graceful Degradation** - Fallback to reduced features when possible
- **Automatic Recovery** - Retry with defaults when sensible
- **Backup & Rollback** - All settings changes backed up
- **Clear Messaging** - User-friendly error messages with solutions
- **Exit Codes** - Consistent error codes for scripting

---

### Hook Management Architecture (Phase 2)

```mermaid
graph TB
    subgraph "Hook System"
        HookMgr[Hook Manager]
        HookRegistry[Hook Registry]
        HookExecutor[Hook Executor]
    end

    subgraph "Hook Types"
        PreCD[Pre-CD Hook<br/>Before directory change]
        PostCD[Post-CD Hook<br/>After directory change]
        PreSwitch[Pre-Switch Hook<br/>Before profile switch]
        PostSwitch[Post-Switch Hook<br/>After profile switch]
        PreApproval[Pre-Approval Hook<br/>Before setting approvals]
        PostApproval[Post-Approval Hook<br/>After setting approvals]
    end

    subgraph "Hook Templates"
        T1[Notification Hook]
        T2[Logging Hook]
        T3[Validation Hook]
        T4[Integration Hook]
    end

    subgraph "User Hooks"
        U1[~/.claude/hooks/pre-cd.sh]
        U2[~/.claude/hooks/post-cd.sh]
        U3[Custom Hook Scripts]
    end

    HookMgr --> HookRegistry
    HookMgr --> HookExecutor

    HookRegistry --> PreCD
    HookRegistry --> PostCD
    HookRegistry --> PreSwitch
    HookRegistry --> PostSwitch
    HookRegistry --> PreApproval
    HookRegistry --> PostApproval

    HookExecutor --> T1
    HookExecutor --> T2
    HookExecutor --> T3
    HookExecutor --> T4

    PreCD --> U1
    PostCD --> U2
    PostSwitch --> U3

    style HookMgr fill:#e3f2fd
    style HookExecutor fill:#e3f2fd
```

**Hook Capabilities (Phase 2):**
- **Event-Driven** - React to context changes
- **Template Library** - Pre-built common hooks
- **User Scripts** - Custom bash/python scripts
- **Validation** - Pre-execution validation
- **Error Handling** - Graceful failure handling

**Example Hooks:**
- Send Slack notification on production context
- Log all profile switches to audit file
- Validate Claude Code settings before applying
- Trigger git status on project context switch

---

### Command Template System (Phase 2)

```mermaid
graph TB
    subgraph "Template Engine"
        TEngine[Template Engine]
        TRegistry[Template Registry]
        TRenderer[Template Renderer]
    end

    subgraph "Built-in Templates"
        Git[Git Commands<br/>commit, status, log]
        Test[Test Commands<br/>pytest, R CMD check]
        Build[Build Commands<br/>quarto render, npm build]
        Deploy[Deploy Commands<br/>gh-pages, vercel]
        Claude[Claude Commands<br/>/done, /recap, /next]
    end

    subgraph "Template Variables"
        V1[{{project_name}}]
        V2[{{project_type}}]
        V3[{{git_branch}}]
        V4[{{current_profile}}]
        V5[{{context_metadata}}]
    end

    subgraph "User Templates"
        UT1[~/.claude/commands/my-workflow.md]
        UT2[~/.claude/commands/test-all.md]
        UT3[Custom Command Templates]
    end

    TEngine --> TRegistry
    TEngine --> TRenderer

    TRegistry --> Git
    TRegistry --> Test
    TRegistry --> Build
    TRegistry --> Deploy
    TRegistry --> Claude

    TRenderer --> V1
    TRenderer --> V2
    TRenderer --> V3
    TRenderer --> V4
    TRenderer --> V5

    Git --> UT1
    Test --> UT2
    Deploy --> UT3

    style TEngine fill:#fff3e0
    style TRenderer fill:#fff3e0
```

**Template Features (Phase 2):**
- **Context-Aware** - Auto-fill variables from current context
- **Composable** - Combine multiple templates
- **Validation** - Check template syntax before execution
- **History** - Track template usage

**Example Template:**
```markdown
---
name: test-workflow
description: Run all tests for {{project_type}} project
---

# Test Workflow for {{project_name}}

Based on project type: {{project_type}}

{{#if r-package}}
R CMD check --as-cran .
{{/if}}

{{#if python}}
pytest --cov={{project_name}}
{{/if}}

{{#if nodejs}}
npm test
{{/if}}
```

---

### MCP Server Creation Workflow (Phase 2)

```mermaid
flowchart TD
    Start([User: aiterm mcp create]) --> Choose{Choose<br/>Template}

    Choose -->|Server Type| Type[Statistical/Shell/Custom]
    Type --> Name[Enter server name]
    Name --> Tools{Include<br/>Tools?}

    Tools -->|Yes| AddTools[Add tool definitions]
    Tools -->|No| Skills

    AddTools --> Skills{Include<br/>Skills?}

    Skills -->|Yes| AddSkills[Add skill prompts]
    Skills -->|No| Config

    AddSkills --> Config[Generate config.json]
    Config --> Structure[Create directory structure]

    Structure --> Files{Generated<br/>Files}

    Files --> F1[mcp-server/config.json]
    Files --> F2[mcp-server/tools/]
    Files --> F3[mcp-server/skills/]
    Files --> F4[mcp-server/README.md]
    Files --> F5[mcp-server/tests/]

    F1 --> Validate[Validate structure]
    F2 --> Validate
    F3 --> Validate
    F4 --> Validate
    F5 --> Validate

    Validate --> Test{Run<br/>Tests?}

    Test -->|Yes| TestRun[aiterm mcp test server_name]
    Test -->|No| Register

    TestRun --> TestPass{Tests<br/>Pass?}
    TestPass -->|No| Fix[Fix issues]
    Fix --> TestRun
    TestPass -->|Yes| Register

    Register[Register in settings.json] --> Done([MCP Server Ready])

    style Start fill:#e1f5e1
    style Done fill:#e1f5e1
    style Choose fill:#fff4e6
    style Tools fill:#fff4e6
    style Skills fill:#fff4e6
    style Test fill:#fff4e6
    style TestPass fill:#fff4e6
```

**MCP Creation Features (Phase 2):**
- **Interactive Wizard** - Step-by-step guidance
- **Template Library** - Pre-built server templates
- **Tool Generator** - Auto-generate tool definitions
- **Skill Prompts** - Built-in skill templates
- **Validation** - Syntax and structure checks
- **Testing** - Automated testing before activation
- **Registration** - Auto-add to Claude Code settings

**Wizard Flow:**
1. Choose server type (statistical, shell, custom)
2. Enter server name and description
3. Add tools (interactive or from template)
4. Add skills (optional)
5. Generate directory structure
6. Validate configuration
7. Run tests
8. Register in Claude Code settings

---

## Next Steps

- See [API Documentation](../api/AITERM-API.md) for detailed API reference
- See [User Guide](../guides/AITERM-USER-GUIDE.md) for usage examples
- See [Integration Guide](../guides/AITERM-INTEGRATION.md) for custom integrations
- See [Troubleshooting Guide](../troubleshooting/AITERM-TROUBLESHOOTING.md) for common issues

---

**Last Updated:** 2025-12-24
**Maintained By:** aiterm Development Team
