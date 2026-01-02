# aiterm Integration Guide

**Version:** 0.1.0-dev
**Last Updated:** 2025-12-21
**Audience:** Developers
**Difficulty:** Intermediate

---

## Table of Contents

1. [Using aiterm as a Library](#using-aiterm-as-a-library)
2. [Creating Custom Context Detectors](#creating-custom-context-detectors)
3. [Adding New Terminal Backends](#adding-new-terminal-backends)
4. [Integration Patterns](#integration-patterns)
5. [Testing Your Integration](#testing-your-integration)
6. [Best Practices](#best-practices)

---

## Using aiterm as a Library

### Basic Usage

aiterm can be used as a Python library in your own tools:

```python
from aiterm.terminal import get_terminal
from aiterm.context import detect_context

# Get terminal backend
terminal = get_terminal()
print(f"Using: {terminal.name}")

# Detect context
context = detect_context("/path/to/project")
if context:
    # Switch profile
    terminal.switch_profile(context.profile)

    # Set title
    terminal.set_title(context.title)

    # Set status bar variables
    terminal.set_status_var("project_type", context.type)
```

**Use cases:**
- Custom shell integrations
- IDE plugins
- Project management tools
- Build systems
- Deployment scripts

---

### Example: ZSH Integration

**File:** `~/.zshrc`

```bash
# aiterm integration for automatic context switching
function chpwd() {
    # Run on every directory change
    python3 -c "
from aiterm.terminal import get_terminal
from aiterm.context import detect_context
import os

path = os.getcwd()
context = detect_context(path)

if context:
    terminal = get_terminal()
    terminal.switch_profile(context.profile)
    terminal.set_title(context.title)
"
}
```

**What this does:**
- Automatically runs on every `cd`
- Detects context
- Switches profile
- Updates title

---

### Example: Project Switcher Tool

**File:** `project_switcher.py`

```python
#!/usr/bin/env python3
"""
Custom project switcher using aiterm
"""
from aiterm.terminal import get_terminal
from aiterm.context import detect_context
import os
import sys

PROJECTS = {
    "rmed": "~/projects/r-packages/RMediation",
    "api": "~/projects/python/api-server",
    "prod": "~/production/api-server"
}

def switch_project(name: str):
    """Switch to project by name"""
    if name not in PROJECTS:
        print(f"Unknown project: {name}")
        print(f"Available: {', '.join(PROJECTS.keys())}")
        return 1

    # Get project path
    path = os.path.expanduser(PROJECTS[name])

    # Change directory
    os.chdir(path)

    # Detect context
    context = detect_context(path)

    if context:
        # Get terminal
        terminal = get_terminal()

        # Switch profile
        terminal.switch_profile(context.profile)

        # Set title
        terminal.set_title(context.title)

        # Set status variables
        terminal.set_status_var("project", name)
        terminal.set_status_var("type", context.type)

        print(f"✅ Switched to {name}")
        print(f"📋 Profile: {context.profile}")
        print(f"📁 Path: {path}")
    else:
        print(f"⚠️  No context detected for {path}")

    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: project_switcher.py PROJECT_NAME")
        sys.exit(1)

    sys.exit(switch_project(sys.argv[1]))
```

**Usage:**
```bash
$ python project_switcher.py rmed
✅ Switched to rmed
📋 Profile: R-Dev
📁 Path: /Users/dt/projects/r-packages/RMediation
```

---

## Creating Custom Context Detectors

### Detector Base Class

All context detectors inherit from `ContextDetector`:

```python
from aiterm.context.base import ContextDetector, Context
from typing import Optional

class MyDetector(ContextDetector):
    """Detect my custom project type"""

    # Priority (1 = highest, 100 = lowest)
    priority = 10

    def detect(self, path: str) -> Optional[Context]:
        """
        Detect context from path

        Args:
            path: Absolute path to directory

        Returns:
            Context object if detected, None otherwise
        """
        # Your detection logic here
        if self._is_my_project(path):
            return Context(
                type="my-project",
                profile="My-Profile",
                title="My Project",
                path=path,
                metadata={}
            )
        return None

    def _is_my_project(self, path: str) -> bool:
        """Check if path is my project type"""
        # Example: check for marker file
        return self._has_file(path, ".myproject")
```

---

### Helper Methods

The `ContextDetector` base class provides helper methods:

```python
class ContextDetector:
    def _has_file(self, path: str, filename: str) -> bool:
        """Check if file exists in path"""

    def _has_directory(self, path: str, dirname: str) -> bool:
        """Check if directory exists in path"""

    def _read_file(self, path: str, filename: str) -> Optional[str]:
        """Read file content, return None if not exists"""

    def _parse_json(self, path: str, filename: str) -> Optional[dict]:
        """Read and parse JSON file"""

    def _parse_toml(self, path: str, filename: str) -> Optional[dict]:
        """Read and parse TOML file"""
```

---

### Example 1: Go Project Detector

```python
from aiterm.context.base import ContextDetector, Context
from typing import Optional

class GoDetector(ContextDetector):
    """Detect Go projects"""

    priority = 5  # Higher priority than default

    def detect(self, path: str) -> Optional[Context]:
        # Check for go.mod
        if not self._has_file(path, "go.mod"):
            return None

        # Read go.mod to get module name
        go_mod_content = self._read_file(path, "go.mod")
        if not go_mod_content:
            return None

        # Parse module name (first line: "module github.com/user/repo")
        lines = go_mod_content.strip().split("\n")
        if not lines:
            return None

        module_line = lines[0]
        if not module_line.startswith("module "):
            return None

        module_name = module_line[7:].strip()  # Remove "module "

        # Extract short name (last part after /)
        short_name = module_name.split("/")[-1]

        return Context(
            type="go-project",
            profile="Go-Dev",
            title=f"Go: {short_name}",
            path=path,
            metadata={
                "module": module_name,
                "short_name": short_name
            }
        )
```

**Register detector:**
```python
from aiterm.context import register_detector

register_detector(GoDetector())
```

---

### Example 2: Rust Project Detector

```python
from aiterm.context.base import ContextDetector, Context
from typing import Optional

class RustDetector(ContextDetector):
    """Detect Rust projects"""

    priority = 5

    def detect(self, path: str) -> Optional[Context]:
        # Check for Cargo.toml
        cargo_toml = self._parse_toml(path, "Cargo.toml")
        if not cargo_toml:
            return None

        # Get package name
        package = cargo_toml.get("package", {})
        name = package.get("name", "unknown")
        version = package.get("version", "")

        # Check if it's a workspace
        is_workspace = "workspace" in cargo_toml

        if is_workspace:
            title = f"Rust Workspace: {name}"
        else:
            title = f"Rust: {name} v{version}" if version else f"Rust: {name}"

        return Context(
            type="rust-project",
            profile="Rust-Dev",
            title=title,
            path=path,
            metadata={
                "name": name,
                "version": version,
                "is_workspace": is_workspace
            }
        )
```

---

### Example 3: Docker Project Detector

```python
from aiterm.context.base import ContextDetector, Context
from typing import Optional

class DockerDetector(ContextDetector):
    """Detect Docker projects"""

    priority = 6

    def detect(self, path: str) -> Optional[Context]:
        # Check for Dockerfile or docker-compose.yml
        has_dockerfile = self._has_file(path, "Dockerfile")
        has_compose = self._has_file(path, "docker-compose.yml")

        if not (has_dockerfile or has_compose):
            return None

        # Determine project type
        if has_compose:
            # Read docker-compose.yml to get services
            compose = self._parse_yaml(path, "docker-compose.yml")
            if compose:
                services = list(compose.get("services", {}).keys())
                service_count = len(services)
                title = f"Docker: {service_count} services"
            else:
                title = "Docker Compose"
        else:
            title = "Docker"

        return Context(
            type="docker-project",
            profile="Docker-Dev",
            title=title,
            path=path,
            metadata={
                "has_dockerfile": has_dockerfile,
                "has_compose": has_compose
            }
        )
```

---

### Example 4: Multi-Condition Detector

```python
from aiterm.context.base import ContextDetector, Context
from typing import Optional

class FullstackDetector(ContextDetector):
    """Detect fullstack projects (frontend + backend)"""

    priority = 7

    def detect(self, path: str) -> Optional[Context]:
        # Check for frontend (package.json)
        has_frontend = self._has_file(path, "package.json")

        # Check for backend (requirements.txt or Pipfile)
        has_backend = (
            self._has_file(path, "requirements.txt") or
            self._has_file(path, "Pipfile") or
            self._has_file(path, "pyproject.toml")
        )

        # Only detect if BOTH present
        if not (has_frontend and has_backend):
            return None

        # Read package.json for project name
        package_json = self._parse_json(path, "package.json")
        if package_json:
            name = package_json.get("name", "unknown")
        else:
            name = path.split("/")[-1]

        return Context(
            type="fullstack-project",
            profile="Fullstack-Dev",
            title=f"Fullstack: {name}",
            path=path,
            metadata={
                "has_frontend": has_frontend,
                "has_backend": has_backend,
                "name": name
            }
        )
```

---

### Registering Custom Detectors

**Method 1: Programmatic Registration**

```python
from aiterm.context import register_detector

# Register detector
register_detector(GoDetector())
register_detector(RustDetector())
register_detector(DockerDetector())
```

**Method 2: Configuration File** (Phase 2 - Planned)

```json
{
  "custom_detectors": [
    {
      "module": "my_detectors",
      "class": "GoDetector"
    },
    {
      "module": "my_detectors",
      "class": "RustDetector"
    }
  ]
}
```

---

## Adding New Terminal Backends

### Terminal Backend Base Class

All terminal backends inherit from `TerminalBackend`:

```python
from aiterm.terminal.base import TerminalBackend
from typing import Optional

class MyTerminal(TerminalBackend):
    """My custom terminal backend"""

    name = "MyTerminal"

    @classmethod
    def detect(cls) -> bool:
        """
        Detect if this is the current terminal

        Returns:
            True if this terminal is active
        """
        import os
        term_program = os.getenv("TERM_PROGRAM", "")
        return "MyTerminal" in term_program

    def switch_profile(self, profile_name: str) -> bool:
        """
        Switch to profile

        Args:
            profile_name: Name of profile

        Returns:
            True if successful
        """
        # Implementation specific to your terminal
        pass

    def set_title(self, title: str) -> bool:
        """
        Set tab/window title

        Args:
            title: Title text

        Returns:
            True if successful
        """
        # Implementation specific to your terminal
        pass

    def set_status_var(self, key: str, value: str) -> bool:
        """
        Set status bar user variable

        Args:
            key: Variable name
            value: Variable value

        Returns:
            True if successful
        """
        # Implementation specific to your terminal
        pass

    def get_current_profile(self) -> Optional[str]:
        """
        Get current active profile name

        Returns:
            Profile name or None
        """
        # Implementation specific to your terminal
        pass
```

---

### Example: Wezterm Backend

```python
from aiterm.terminal.base import TerminalBackend
from typing import Optional
import os
import subprocess

class WeztermTerminal(TerminalBackend):
    """Wezterm terminal backend"""

    name = "Wezterm"

    @classmethod
    def detect(cls) -> bool:
        """Detect Wezterm"""
        term_program = os.getenv("TERM_PROGRAM", "")
        return "WezTerm" in term_program

    def switch_profile(self, profile_name: str) -> bool:
        """Switch Wezterm color scheme"""
        try:
            # Wezterm uses CLI commands
            subprocess.run([
                "wezterm",
                "cli",
                "set-tab-color-scheme",
                profile_name
            ], check=True)
            return True
        except Exception:
            return False

    def set_title(self, title: str) -> bool:
        """Set tab title"""
        # Wezterm supports OSC sequences
        try:
            # OSC 0 - Set window/tab title
            print(f"\033]0;{title}\007", end="", flush=True)
            return True
        except Exception:
            return False

    def set_status_var(self, key: str, value: str) -> bool:
        """Set user variable (if supported)"""
        # Wezterm has custom escape sequences
        try:
            import base64
            encoded_value = base64.b64encode(value.encode()).decode()
            print(f"\033]1337;SetUserVar={key}={encoded_value}\007",
                  end="", flush=True)
            return True
        except Exception:
            return False

    def get_current_profile(self) -> Optional[str]:
        """Get current color scheme"""
        # Query via CLI
        try:
            result = subprocess.run([
                "wezterm",
                "cli",
                "get-tab-color-scheme"
            ], capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None
```

---

### Example: Alacritty Backend

```python
from aiterm.terminal.base import TerminalBackend
from typing import Optional
import os
import yaml

class AlacrittyTerminal(TerminalBackend):
    """Alacritty terminal backend"""

    name = "Alacritty"

    @classmethod
    def detect(cls) -> bool:
        """Detect Alacritty"""
        term_program = os.getenv("TERM_PROGRAM", "")
        term = os.getenv("TERM", "")
        return "alacritty" in term_program.lower() or "alacritty" in term.lower()

    def switch_profile(self, profile_name: str) -> bool:
        """Switch Alacritty theme"""
        # Alacritty uses config file
        config_path = os.path.expanduser("~/.config/alacritty/alacritty.yml")
        theme_path = os.path.expanduser(
            f"~/.config/alacritty/themes/{profile_name}.yml"
        )

        if not os.path.exists(theme_path):
            return False

        try:
            # Read current config
            with open(config_path) as f:
                config = yaml.safe_load(f)

            # Read theme
            with open(theme_path) as f:
                theme = yaml.safe_load(f)

            # Update colors
            config["colors"] = theme.get("colors", {})

            # Write back
            with open(config_path, "w") as f:
                yaml.dump(config, f)

            # Reload Alacritty (if running)
            subprocess.run(["pkill", "-USR1", "alacritty"])

            return True
        except Exception:
            return False

    def set_title(self, title: str) -> bool:
        """Set window title"""
        try:
            print(f"\033]0;{title}\007", end="", flush=True)
            return True
        except Exception:
            return False

    def set_status_var(self, key: str, value: str) -> bool:
        """Alacritty doesn't support status bar variables"""
        return False

    def get_current_profile(self) -> Optional[str]:
        """Get current theme name"""
        # Parse config file
        config_path = os.path.expanduser("~/.config/alacritty/alacritty.yml")
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            # Theme name is stored in custom field
            return config.get("theme_name")
        except Exception:
            return None
```

---

### Registering Custom Backend

**Method 1: Factory Function** (Recommended)

```python
# aiterm/terminal/__init__.py

def get_terminal() -> TerminalBackend:
    """Get appropriate terminal backend"""

    # Try custom backends first
    if WeztermTerminal.detect():
        return WeztermTerminal()

    if AlacrittyTerminal.detect():
        return AlacrittyTerminal()

    # Fall back to built-in
    if iTerm2Terminal.detect():
        return iTerm2Terminal()

    # Default fallback
    return DefaultTerminal()
```

**Method 2: Environment Variable**

```bash
export AITERM_TERMINAL=wezterm
```

Then in code:
```python
def get_terminal() -> TerminalBackend:
    forced = os.getenv("AITERM_TERMINAL")
    if forced == "wezterm":
        return WeztermTerminal()
    # ... auto-detect
```

---

## Integration Patterns

### Pattern 1: Shell Hook Integration

**Use case:** Automatic context switching on `cd`

**ZSH Example:**
```bash
# ~/.zshrc

# aiterm: Automatic context switching
autoload -U add-zsh-hook

function aiterm_chpwd() {
    python3 -c '
from aiterm.terminal import get_terminal
from aiterm.context import detect_context
import os

context = detect_context(os.getcwd())
if context:
    terminal = get_terminal()
    terminal.switch_profile(context.profile)
    terminal.set_title(context.title)
    '
}

add-zsh-hook chpwd aiterm_chpwd

# Run on shell start
aiterm_chpwd
```

**BASH Example:**
```bash
# ~/.bashrc

function aiterm_prompt_command() {
    python3 -c '
from aiterm.terminal import get_terminal
from aiterm.context import detect_context
import os

context = detect_context(os.getcwd())
if context:
    terminal = get_terminal()
    terminal.switch_profile(context.profile)
    terminal.set_title(context.title)
    '
}

PROMPT_COMMAND="aiterm_prompt_command${PROMPT_COMMAND:+; $PROMPT_COMMAND}"
```

---

### Pattern 2: IDE Plugin Integration

**Use case:** VS Code extension for context switching

**Python Backend (VS Code Extension):**
```python
# vscode_aiterm.py

from aiterm.terminal import get_terminal
from aiterm.context import detect_context
import json
import sys

def handle_workspace_change(workspace_path: str):
    """Handle VS Code workspace change"""

    # Detect context
    context = detect_context(workspace_path)

    if context:
        # Get terminal
        terminal = get_terminal()

        # Switch profile
        terminal.switch_profile(context.profile)

        # Return context info for VS Code
        return {
            "type": context.type,
            "profile": context.profile,
            "title": context.title
        }

    return None

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "."
    result = handle_workspace_change(workspace)
    print(json.dumps(result))
```

**VS Code Extension (TypeScript):**
```typescript
// extension.ts

import * as vscode from 'vscode';
import { exec } from 'child_process';

export function activate(context: vscode.ExtensionContext) {
    // Listen for workspace changes
    vscode.workspace.onDidChangeWorkspaceFolders(async (event) => {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) return;

        // Call aiterm Python backend
        exec(`python3 vscode_aiterm.py "${workspaceFolder.uri.fsPath}"`,
            (error, stdout, stderr) => {
                if (!error) {
                    const result = JSON.parse(stdout);
                    vscode.window.showInformationMessage(
                        `aiterm: Switched to ${result.profile}`
                    );
                }
            }
        );
    });
}
```

---

### Pattern 3: Build System Integration

**Use case:** Gradle/Maven/Make integration

**Gradle Example:**
```groovy
// build.gradle

task aitermSetup {
    doLast {
        exec {
            commandLine 'python3', '-c', '''
from aiterm.terminal import get_terminal
from aiterm.context import detect_context

context = detect_context(".")
if context:
    terminal = get_terminal()
    terminal.switch_profile("Java-Dev")
    terminal.set_title("Gradle: " + project.name)
            '''
        }
    }
}

// Run before any task
tasks.all { task ->
    task.dependsOn aitermSetup
}
```

---

### Pattern 4: Deployment Script Integration

**Use case:** Safety mode for production deployments

**Deployment Script:**
```bash
#!/bin/bash
# deploy.sh

set -e

# Enable production mode
python3 -c '
from aiterm.terminal import get_terminal

terminal = get_terminal()
terminal.switch_profile("Production")  # RED theme
terminal.set_title("⚠️ PRODUCTION DEPLOYMENT")
'

echo "⚠️  PRODUCTION MODE ACTIVE"
echo "Deploying to production..."

# Deployment commands...
kubectl apply -f k8s/
# ...

echo "✅ Deployment complete"

# Reset to default
python3 -c '
from aiterm.terminal import get_terminal
terminal = get_terminal()
terminal.switch_profile("Default")
'
```

---

## Testing Your Integration

### Unit Tests

**Test custom detector:**
```python
import pytest
from pathlib import Path
from your_module import GoDetector

def test_go_detector_detects_go_project(tmp_path):
    """Test Go detector finds go.mod"""
    # Create test structure
    (tmp_path / "go.mod").write_text("module github.com/user/myproject")

    # Test detection
    detector = GoDetector()
    context = detector.detect(str(tmp_path))

    # Assertions
    assert context is not None
    assert context.type == "go-project"
    assert context.profile == "Go-Dev"
    assert "myproject" in context.title

def test_go_detector_ignores_non_go_project(tmp_path):
    """Test Go detector returns None for non-Go projects"""
    detector = GoDetector()
    context = detector.detect(str(tmp_path))

    assert context is None
```

---

### Integration Tests

**Test terminal backend:**
```python
import pytest
from your_module import WeztermTerminal

@pytest.mark.skipif(
    not WeztermTerminal.detect(),
    reason="Wezterm not available"
)
def test_wezterm_profile_switching():
    """Test Wezterm profile switching"""
    terminal = WeztermTerminal()

    # Switch profile
    result = terminal.switch_profile("Test-Profile")
    assert result is True

    # Verify profile changed
    current = terminal.get_current_profile()
    assert current == "Test-Profile"
```

---

### Manual Testing

**Test full integration:**
```bash
# 1. Create test directory
mkdir -p /tmp/test-aiterm-go
cd /tmp/test-aiterm-go

# 2. Create go.mod
echo "module github.com/test/myproject" > go.mod

# 3. Test detection
aiterm detect
# Should show: Type: go-project, Profile: Go-Dev

# 4. Test profile switching
aiterm profile switch Go-Dev
# Should switch iTerm2 profile

# 5. Cleanup
cd ~
rm -rf /tmp/test-aiterm-go
```

---

## Best Practices

### 1. Detector Priority

**Rule:** Higher priority = checked first

```python
class ProductionDetector(ContextDetector):
    priority = 1  # Highest - safety first!

class ProjectTypeDetector(ContextDetector):
    priority = 5  # Normal

class DefaultDetector(ContextDetector):
    priority = 100  # Lowest - last resort
```

**Why:** Production should always override other detectors

---

### 2. Fail Fast

**Good:**
```python
def detect(self, path: str) -> Optional[Context]:
    # Check cheapest condition first
    if not self._has_file(path, "marker.txt"):
        return None  # Fast exit

    # Then expensive operations
    content = self._read_file(path, "config.json")
    # ...
```

**Bad:**
```python
def detect(self, path: str) -> Optional[Context]:
    # Expensive operation first
    content = self._read_file(path, "config.json")

    # Then cheap check
    if not self._has_file(path, "marker.txt"):
        return None  # Wasted work!
```

---

### 3. Error Handling

**Good:**
```python
def switch_profile(self, profile_name: str) -> bool:
    try:
        # Terminal operation
        result = subprocess.run([...], check=True)
        return True
    except subprocess.CalledProcessError:
        # Log error but don't crash
        logger.error(f"Failed to switch profile: {profile_name}")
        return False
    except Exception as e:
        # Catch unexpected errors
        logger.exception("Unexpected error in switch_profile")
        return False
```

---

### 4. Graceful Degradation

**Good:**
```python
def set_status_var(self, key: str, value: str) -> bool:
    if not self.supports_status_vars:
        return False  # Feature not supported, that's OK

    try:
        # Set variable
        return True
    except Exception:
        return False  # Failed, but don't crash
```

---

### 5. Documentation

**Always document:**
- What your detector detects
- Priority level and why
- Metadata structure
- Example usage

```python
class GoDetector(ContextDetector):
    """
    Detect Go projects by looking for go.mod file.

    Priority: 5 (normal)

    Detects:
        - go.mod file
        - Extracts module name
        - Determines workspace vs package

    Metadata:
        - module: Full module path (e.g., "github.com/user/repo")
        - short_name: Project name (last part of path)
        - is_workspace: Boolean, true if Go workspace

    Example:
        >>> detector = GoDetector()
        >>> context = detector.detect("/path/to/project")
        >>> if context:
        ...     print(context.metadata["module"])
    """
    priority = 5
    # ...
```

---

## Next Steps

- **[API Documentation](../api/AITERM-API.md)** - Full API reference
- **[Architecture](../architecture/AITERM-ARCHITECTURE.md)** - System design
- **[User Guide](AITERM-USER-GUIDE.md)** - End-user documentation
- **[Troubleshooting](../troubleshooting/AITERM-TROUBLESHOOTING.md)** - Common issues

---

**Last Updated:** 2025-12-21
**Maintained By:** aiterm Development Team
