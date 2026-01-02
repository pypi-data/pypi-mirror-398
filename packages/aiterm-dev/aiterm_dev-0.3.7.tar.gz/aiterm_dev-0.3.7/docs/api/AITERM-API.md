# aiterm API Documentation

**Version:** 0.1.0-dev
**Last Updated:** 2025-12-21

---

## Table of Contents

1. [CLI Commands](#cli-commands)
   - [Core Commands](#core-commands)
   - [Profile Management](#profile-management)
   - [Context Detection](#context-detection)
   - [Claude Code Integration](#claude-code-integration)
   - [MCP Tools - Phase 2](#mcp-tools-phase-2)
2. [Python API](#python-api)
   - [Terminal Backends](#terminal-backends)
   - [Context Detection](#context-detection-api)
   - [Settings Management](#settings-management)
3. [Configuration](#configuration)
   - [Settings File](#settings-file)
   - [Environment Variables](#environment-variables)
4. [Return Types & Errors](#return-types-errors)

---

## CLI Commands

### Command Overview

```bash
aiterm --help                 # Show help
aiterm --version              # Show version
aiterm doctor                 # Check installation
aiterm detect                 # Detect current context
aiterm profile list           # List available profiles
aiterm profile switch PROFILE # Switch to profile
aiterm claude approvals list  # List auto-approval presets
aiterm claude approvals set   # Set auto-approvals
aiterm claude settings show   # Show Claude Code settings
```

---

## Core Commands

### `aiterm doctor`

**Purpose:** Check aiterm installation and environment

**Usage:**
```bash
aiterm doctor
```

**Output:**
```
╔════════════════════════════════════════════════════╗
║  aiterm Installation Check                         ║
╚════════════════════════════════════════════════════╝

✅ Python: 3.11.5
✅ Terminal: iTerm2 (Build 3.5.0)
✅ Claude Code: 0.2.0 (~/.claude/)
✅ Settings: ~/.aiterm/config.json

System Status: All checks passed!
```

**Exit Codes:**
- `0` - All checks passed
- `1` - One or more checks failed

**What It Checks:**
- Python version (≥ 3.10)
- Terminal type and version
- Claude Code installation
- Configuration file presence
- Write permissions for config directories

**Example - All Checks Passed:**
```bash
$ aiterm doctor
✅ Python: 3.11.5
✅ Terminal: iTerm2 (Build 3.5.0)
✅ Claude Code: 0.2.0
✅ Settings: ~/.aiterm/config.json

System Status: All checks passed!
```

**Example - Failed Check:**
```bash
$ aiterm doctor
✅ Python: 3.11.5
❌ Terminal: Unsupported (Terminal.app)
   → iTerm2 3.4.0+ required for full features
✅ Claude Code: 0.2.0
✅ Settings: ~/.aiterm/config.json

System Status: 1 check failed
```

---

### `aiterm detect`

**Purpose:** Detect current project context

**Usage:**
```bash
aiterm detect [PATH]
```

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| PATH | string | No | `pwd` | Directory to analyze |

**Output:**
```
╔════════════════════════════════════════════════════╗
║  Context Detection                                 ║
╚════════════════════════════════════════════════════╝

📁 Path: /Users/dt/projects/r-packages/RMediation
🎯 Type: R Package
📦 Package: RMediation
📋 Profile: R-Dev
🎨 Title: RMediation v1.0.0

Detected: R package development environment
```

**Detection Logic:**

aiterm detects context by checking for specific files and path patterns:

| Context Type | Detection Pattern | Profile | Priority |
|-------------|-------------------|---------|----------|
| Production | `*/production/*` or `*/prod/*` | Production | 1 (highest) |
| AI Session | `*/claude-sessions/*` or `*/gemini-sessions/*` | AI-Session | 2 |
| R Package | `DESCRIPTION` + `R/` directory | R-Dev | 3 |
| Python | `pyproject.toml` or `setup.py` | Python-Dev | 4 |
| Node.js | `package.json` | Node-Dev | 5 |
| Quarto | `_quarto.yml` | R-Dev | 6 |
| MCP Server | `mcp-server/` directory | AI-Session | 7 |
| Dev Tools | `.git/` + `scripts/` directory | Dev-Tools | 8 |
| Default | (no matches) | Default | 9 (lowest) |

**Example - R Package Detected:**
```bash
$ cd ~/projects/r-packages/RMediation
$ aiterm detect

📁 Path: /Users/dt/projects/r-packages/RMediation
🎯 Type: R Package
📦 Package: RMediation
📋 Profile: R-Dev
🎨 Title: RMediation v1.0.0
```

**Example - Production Path:**
```bash
$ cd ~/production/api-server
$ aiterm detect

📁 Path: /Users/dt/production/api-server
🎯 Type: Production
⚠️  Profile: Production (safe mode)
🎨 Title: PROD: api-server
```

**Example - No Context:**
```bash
$ cd ~/Downloads
$ aiterm detect

📁 Path: /Users/dt/Downloads
🎯 Type: Unknown
📋 Profile: Default
🎨 Title: Downloads
```

**Return Type:**
```json
{
  "type": "r-package",
  "profile": "R-Dev",
  "title": "RMediation v1.0.0",
  "path": "/Users/dt/projects/r-packages/RMediation",
  "metadata": {
    "package": "RMediation",
    "version": "1.0.0"
  }
}
```

---

## Profile Management

### `aiterm profile list`

**Purpose:** List all available iTerm2 profiles

**Usage:**
```bash
aiterm profile list
```

**Output:**
```
╔════════════════════════════════════════════════════╗
║  Available Profiles                                ║
╚════════════════════════════════════════════════════╝

📋 R-Dev
   → For R package development
   🎨 Blue theme, white text
   🔧 Optimized for ESS/Claude Code

📋 Python-Dev
   → For Python projects
   🎨 Green theme, white text
   🔧 Optimized for pytest/Claude Code

📋 Production
   → For production deployments (SAFE MODE)
   🎨 Red theme, black text
   ⚠️  Read-only, extra confirmations

📋 AI-Session
   → For Claude Code/Gemini sessions
   🎨 Purple theme, white text
   🔧 Optimized for AI coding workflows

📋 Default
   → Standard profile
   🎨 Default iTerm2 theme
```

**Options:**
```bash
aiterm profile list --json     # JSON output
aiterm profile list --verbose  # Show full details
```

**JSON Output:**
```json
{
  "profiles": [
    {
      "name": "R-Dev",
      "description": "For R package development",
      "theme": {
        "background": "#1a1f29",
        "foreground": "#ffffff",
        "accent": "#61afef"
      },
      "triggers": ["DESCRIPTION", "R/"],
      "context_types": ["r-package", "quarto"]
    },
    ...
  ]
}
```

---

### `aiterm profile switch`

**Purpose:** Manually switch to a specific profile

**Usage:**
```bash
aiterm profile switch PROFILE_NAME
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| PROFILE_NAME | string | Yes | Name of profile to switch to |

**Example:**
```bash
$ aiterm profile switch R-Dev

✅ Switched to profile: R-Dev
🎨 Theme: Cool Blues
📋 Context: R Package Development
```

**Options:**
```bash
aiterm profile switch PROFILE --no-title   # Don't update tab title
aiterm profile switch PROFILE --title TEXT # Set custom title
```

**Errors:**
| Error | Exit Code | Description |
|-------|-----------|-------------|
| `ProfileNotFound` | 2 | Profile doesn't exist |
| `TerminalUnsupported` | 3 | Terminal doesn't support profiles |
| `PermissionDenied` | 4 | Can't write iTerm2 settings |

---

## Context Detection

### Automatic Context Switching

**How It Works:**

When you `cd` into a directory, aiterm automatically:

1. Detects project type
2. Selects appropriate profile
3. Switches iTerm2 profile
4. Updates tab title
5. Sets status bar variables

**Example Flow:**
```bash
$ cd ~/projects/r-packages/RMediation
# aiterm detects R package
# → Switches to R-Dev profile
# → Sets title: "RMediation v1.0.0"
# → Updates status bar: "R PKG | RMediation"

$ cd ~/production/api-server
# aiterm detects production path
# → Switches to Production profile (red, safe mode)
# → Sets title: "PROD: api-server"
# → Updates status bar: "⚠️ PRODUCTION"
```

**Disabling Auto-Switching:**
```bash
export AITERM_AUTO_SWITCH=0  # Disable automatic switching
```

---

## Claude Code Integration

### `aiterm claude approvals list`

**Purpose:** List available auto-approval presets

**Usage:**
```bash
aiterm claude approvals list
```

**Output:**
```
╔════════════════════════════════════════════════════╗
║  Auto-Approval Presets                             ║
╚════════════════════════════════════════════════════╝

⚡ minimal
   → Essential operations only
   📋 Bash(git status), Read, Glob, Grep
   ✅ 15 tools approved

🚀 development
   → Full development workflow
   📋 All read operations, git, testing
   ✅ 45 tools approved

🔒 production
   → Production-safe operations
   📋 Read-only, no destructive commands
   ✅ 20 tools approved

🎯 r-package
   → R package development
   📋 R execution, testing, documentation
   ✅ 35 tools approved

...
```

**Available Presets:**

| Preset | Tools | Use Case |
|--------|-------|----------|
| `minimal` | 15 | Essential read operations only |
| `development` | 45 | Full development workflow |
| `production` | 20 | Production-safe (read-only) |
| `r-package` | 35 | R package development |
| `python-dev` | 40 | Python development |
| `teaching` | 30 | Teaching/course development |
| `research` | 35 | Research/manuscript writing |
| `ai-session` | 50 | AI coding sessions |

---

### `aiterm claude approvals set`

**Purpose:** Set auto-approval preset for current profile

**Usage:**
```bash
aiterm claude approvals set PRESET
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| PRESET | string | Yes | Name of preset (see list) |

**Example:**
```bash
$ aiterm claude approvals set r-package

✅ Applied preset: r-package
📋 Approved tools: 35
📝 Updated: ~/.claude/settings.json

Auto-approvals:
  ✅ Bash(git *)
  ✅ Bash(R CMD *)
  ✅ Bash(pytest *)
  ✅ Read(**)
  ✅ Write(**)
  ... (30 more)
```

**Options:**
```bash
aiterm claude approvals set PRESET --dry-run  # Show changes without applying
aiterm claude approvals set PRESET --merge    # Merge with existing approvals
```

**What It Does:**

1. Reads `~/.claude/settings.json`
2. Merges preset auto-approvals
3. Backs up original settings
4. Writes updated settings
5. Validates JSON structure

**Backup Location:**
```
~/.claude/settings.json.backup.TIMESTAMP
```

---

### `aiterm claude settings show`

**Purpose:** Show current Claude Code settings

**Usage:**
```bash
aiterm claude settings show
```

**Output:**
```
╔════════════════════════════════════════════════════╗
║  Claude Code Settings                              ║
╚════════════════════════════════════════════════════╝

📁 Settings: ~/.claude/settings.json
📊 File size: 2.4 KB
🕐 Modified: 2025-12-21 10:30:45

Auto-Approvals:
  ✅ 35 tools approved
  📋 Active preset: r-package

Status Line:
  ✅ Configured: /bin/bash ~/.claude/statusline-p10k.sh
  ⏱️  Update interval: 300ms

MCP Servers:
  ✅ statistical-research (14 tools)
  ✅ shell (5 tools)
  ✅ project-refactor (4 tools)
```

**Options:**
```bash
aiterm claude settings show --json      # JSON output
aiterm claude settings show --validate  # Validate settings structure
```

---

## MCP Tools - Phase 2

### `aiterm mcp list`

**Purpose:** List configured MCP servers

**Usage:**
```bash
aiterm mcp list
```

**Status:** 🚧 Planned for Phase 2

**Expected Output:**
```
╔════════════════════════════════════════════════════╗
║  MCP Servers                                       ║
╚════════════════════════════════════════════════════╝

✅ statistical-research
   📋 14 tools, 17 skills
   📁 ~/projects/dev-tools/mcp-servers/statistical-research

✅ shell
   📋 5 tools
   📁 ~/projects/dev-tools/mcp-servers/shell

✅ project-refactor
   📋 4 tools
   📁 ~/projects/dev-tools/mcp-servers/project-refactor
```

---

### `aiterm mcp test`

**Purpose:** Test MCP server functionality

**Status:** 🚧 Planned for Phase 2

**Usage:**
```bash
aiterm mcp test SERVER_NAME
```

---

### `aiterm mcp validate`

**Purpose:** Validate MCP server configuration

**Status:** 🚧 Planned for Phase 2

**Usage:**
```bash
aiterm mcp validate [SERVER_NAME]
```

---

## Python API

### Terminal Backends

#### `get_terminal()`

**Purpose:** Get current terminal backend

**Usage:**
```python
from aiterm.terminal import get_terminal

terminal = get_terminal()
print(f"Using: {terminal.name}")
```

**Returns:** `Terminal` instance (iTerm2Terminal, etc.)

**Example:**
```python
from aiterm.terminal import get_terminal

terminal = get_terminal()

if terminal.name == "iTerm2":
    print(f"iTerm2 version: {terminal.version}")
else:
    print(f"Unsupported terminal: {terminal.name}")
```

---

#### `iTerm2Terminal`

**Purpose:** iTerm2-specific terminal backend

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `switch_profile(name)` | `name: str` | `bool` | Switch to profile |
| `set_title(text)` | `text: str` | `bool` | Set tab title |
| `set_status_var(key, value)` | `key: str, value: str` | `bool` | Set status bar variable |
| `get_current_profile()` | - | `str` | Get active profile name |

**Example:**
```python
from aiterm.terminal.iterm2 import iTerm2Terminal

terminal = iTerm2Terminal()

# Switch profile
terminal.switch_profile("R-Dev")

# Set tab title
terminal.set_title("RMediation v1.0.0")

# Set status bar variable
terminal.set_status_var("project_type", "R PKG")
terminal.set_status_var("package_name", "RMediation")
```

**Escape Sequences Used:**

```python
# Switch profile
ESC ]1337;SetProfile=PROFILE_NAME BEL

# Set title
ESC ]0;TITLE_TEXT BEL

# Set user variable (status bar)
ESC ]1337;SetUserVar=KEY=VALUE_BASE64 BEL
```

---

### Context Detection API

#### `detect_context()`

**Purpose:** Detect project context from path

**Usage:**
```python
from aiterm.context import detect_context

context = detect_context("/path/to/project")
if context:
    print(f"Type: {context.type}")
    print(f"Profile: {context.profile}")
```

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| path | str | No | `pwd` | Path to analyze |

**Returns:** `Context | None`

**Context Object:**
```python
@dataclass
class Context:
    type: str              # "r-package", "python", etc.
    profile: str           # "R-Dev", "Python-Dev", etc.
    title: str            # Tab title text
    path: str             # Full path
    metadata: dict        # Type-specific metadata
```

**Example:**
```python
from aiterm.context import detect_context

# Detect R package
context = detect_context("/Users/dt/projects/RMediation")

if context:
    print(f"Type: {context.type}")         # "r-package"
    print(f"Profile: {context.profile}")   # "R-Dev"
    print(f"Title: {context.title}")       # "RMediation v1.0.0"
    print(f"Package: {context.metadata['package']}")  # "RMediation"
```

---

#### `ContextDetector` (Base Class)

**Purpose:** Abstract base class for context detectors

**Usage:**
```python
from aiterm.context.detector import ContextDetector, Context

class MyDetector(ContextDetector):
    def detect(self, path: str) -> Context | None:
        if self._is_my_project(path):
            return Context(
                type="my-project",
                profile="My-Profile",
                title="My Project",
                path=path,
                metadata={}
            )
        return None
```

**Abstract Methods:**
| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `detect()` | `path: str` | `Context \| None` | Detect context |

**Helper Methods:**
| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `_has_file(path, filename)` | `path: str, filename: str` | `bool` | Check if file exists |
| `_has_directory(path, dirname)` | `path: str, dirname: str` | `bool` | Check if directory exists |
| `_read_file(path, filename)` | `path: str, filename: str` | `str \| None` | Read file content |

**Example - Custom Detector:**
```python
from aiterm.context.detector import ContextDetector, Context

class GoDetector(ContextDetector):
    """Detect Go projects"""

    def detect(self, path: str) -> Context | None:
        if not self._has_file(path, "go.mod"):
            return None

        # Read module name
        go_mod = self._read_file(path, "go.mod")
        if go_mod:
            # Extract module name from first line
            module = go_mod.split("\n")[0].replace("module ", "").strip()

            return Context(
                type="go-project",
                profile="Go-Dev",
                title=f"Go: {module}",
                path=path,
                metadata={"module": module}
            )

        return None

# Register detector
from aiterm.context import register_detector
register_detector(GoDetector())
```

---

### Settings Management

#### `read_claude_settings()`

**Purpose:** Read Claude Code settings file

**Usage:**
```python
from aiterm.claude.settings import read_claude_settings

settings = read_claude_settings()
print(settings["autoApprovals"])
```

**Returns:** `dict` - Parsed settings.json

**Example:**
```python
from aiterm.claude.settings import read_claude_settings

settings = read_claude_settings()

# Check auto-approvals
approvals = settings.get("autoApprovals", [])
print(f"Auto-approved tools: {len(approvals)}")

# Check status line
statusline = settings.get("statusLine", {})
if statusline:
    print(f"Status line: {statusline['command']}")
```

---

#### `write_claude_settings()`

**Purpose:** Write Claude Code settings file

**Usage:**
```python
from aiterm.claude.settings import write_claude_settings

settings = {...}
write_claude_settings(settings, backup=True)
```

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| settings | dict | Yes | - | Settings object |
| backup | bool | No | `True` | Create backup before writing |

**Example:**
```python
from aiterm.claude.settings import (
    read_claude_settings,
    write_claude_settings
)

# Read current settings
settings = read_claude_settings()

# Add auto-approval
settings["autoApprovals"].append("Bash(npm test:*)")

# Write back (creates backup automatically)
write_claude_settings(settings)
```

---

#### `apply_approval_preset()`

**Purpose:** Apply auto-approval preset to settings

**Usage:**
```python
from aiterm.claude.settings import apply_approval_preset

apply_approval_preset("r-package")
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| preset_name | str | Yes | Name of preset |
| merge | bool | No | Merge with existing approvals (default: False) |

**Available Presets:**
- `minimal` - Essential operations (15 tools)
- `development` - Full dev workflow (45 tools)
- `production` - Production-safe (20 tools)
- `r-package` - R package development (35 tools)
- `python-dev` - Python development (40 tools)
- `teaching` - Teaching/courses (30 tools)
- `research` - Research/manuscripts (35 tools)
- `ai-session` - AI coding sessions (50 tools)

**Example:**
```python
from aiterm.claude.settings import apply_approval_preset

# Apply R package preset
apply_approval_preset("r-package")

# Apply and merge with existing
apply_approval_preset("development", merge=True)
```

---

## Configuration

### Settings File

**Location:** `~/.aiterm/config.json`

**Structure:**
```json
{
  "version": "0.2.0",
  "terminal": {
    "type": "iterm2",
    "auto_switch": true,
    "default_profile": "Default"
  },
  "context_detection": {
    "enabled": true,
    "priority_order": [
      "production",
      "ai-session",
      "r-package",
      "python",
      "nodejs",
      "quarto",
      "mcp-server",
      "dev-tools"
    ]
  },
  "profiles": {
    "R-Dev": {
      "theme": "cool-blues",
      "triggers": ["DESCRIPTION", "R/"]
    },
    "Python-Dev": {
      "theme": "forest-greens",
      "triggers": ["pyproject.toml", "setup.py"]
    }
  }
}
```

**Example - Reading Config:**
```python
from aiterm.utils.config import read_config

config = read_config()
print(config["terminal"]["type"])  # "iterm2"
```

---

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AITERM_AUTO_SWITCH` | bool | `1` | Enable automatic profile switching |
| `AITERM_CONFIG` | string | `~/.aiterm/config.json` | Config file path |
| `AITERM_DEBUG` | bool | `0` | Enable debug logging |
| `AITERM_TERMINAL` | string | (auto) | Force terminal type |

**Example:**
```bash
# Disable auto-switching
export AITERM_AUTO_SWITCH=0

# Use custom config
export AITERM_CONFIG=~/my-aiterm-config.json

# Enable debug mode
export AITERM_DEBUG=1
```

---

## Return Types & Errors

### Error Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | Success | Operation completed successfully |
| 1 | GeneralError | General error |
| 2 | NotFound | Profile/resource not found |
| 3 | Unsupported | Terminal/feature unsupported |
| 4 | PermissionDenied | Permission error |
| 5 | InvalidConfig | Invalid configuration |
| 6 | ValidationError | Validation failed |

---

### Exception Types

```python
from aiterm.exceptions import (
    AitermError,           # Base exception
    ProfileNotFoundError,
    TerminalUnsupportedError,
    ConfigError,
    SettingsError
)
```

**Example - Error Handling:**
```python
from aiterm.terminal import get_terminal
from aiterm.exceptions import TerminalUnsupportedError

try:
    terminal = get_terminal()
    terminal.switch_profile("R-Dev")
except TerminalUnsupportedError:
    print("iTerm2 required for profile switching")
except ProfileNotFoundError:
    print("Profile 'R-Dev' not found")
```

---

## Performance Specifications

### Target Performance

| Operation | Target | Description |
|-----------|--------|-------------|
| Context detection | < 50ms | Detect project type |
| Profile switching | < 150ms | Switch iTerm2 profile |
| Settings read | < 10ms | Read Claude settings |
| Settings write | < 50ms | Write Claude settings |
| Auto-approval application | < 100ms | Apply preset to settings |

---

## Versioning

**API Version:** 0.1.0-dev

**Stability:** Development (breaking changes possible)

**Stable Release:** Planned for v1.0.0

---

## Next Steps

- See [Architecture Documentation](../architecture/AITERM-ARCHITECTURE.md) for system design
- See [User Guide](../guides/AITERM-USER-GUIDE.md) for usage examples
- See [Integration Guide](../guides/AITERM-INTEGRATION.md) for custom integrations
- See [Troubleshooting Guide](../troubleshooting/AITERM-TROUBLESHOOTING.md) for common issues

---

**Last Updated:** 2025-12-21
**Maintained By:** aiterm Development Team
