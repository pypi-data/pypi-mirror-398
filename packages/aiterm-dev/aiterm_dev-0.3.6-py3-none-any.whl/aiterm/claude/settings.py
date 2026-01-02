"""Claude Code settings management.

Handles reading, writing, and managing Claude Code settings.json files.
"""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# Default settings file locations
GLOBAL_SETTINGS = Path.home() / ".claude" / "settings.json"
LOCAL_SETTINGS_NAME = ".claude/settings.local.json"


@dataclass
class ClaudeSettings:
    """Represents Claude Code settings."""

    path: Path
    permissions: dict = field(default_factory=dict)
    hooks: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)

    @property
    def allow_list(self) -> list[str]:
        """Get the list of allowed permissions."""
        return self.permissions.get("allow", [])

    @property
    def deny_list(self) -> list[str]:
        """Get the list of denied permissions."""
        return self.permissions.get("deny", [])


def find_settings_file(path: Optional[Path] = None) -> Optional[Path]:
    """Find the Claude settings file.

    Searches in order:
    1. Local project settings (.claude/settings.local.json)
    2. Global settings (~/.claude/settings.json)

    Args:
        path: Starting directory for local search. Defaults to cwd.

    Returns:
        Path to settings file, or None if not found.
    """
    start = path or Path.cwd()

    # Check for local settings
    local = start / LOCAL_SETTINGS_NAME
    if local.exists():
        return local

    # Check parent directories for local settings
    for parent in start.parents:
        local = parent / LOCAL_SETTINGS_NAME
        if local.exists():
            return local

    # Fall back to global settings
    if GLOBAL_SETTINGS.exists():
        return GLOBAL_SETTINGS

    return None


def load_settings(path: Optional[Path] = None) -> Optional[ClaudeSettings]:
    """Load Claude settings from a file.

    Args:
        path: Path to settings file. If None, searches for settings.

    Returns:
        ClaudeSettings object, or None if not found/invalid.
    """
    settings_path = path or find_settings_file()
    if not settings_path or not settings_path.exists():
        return None

    try:
        data = json.loads(settings_path.read_text())
        return ClaudeSettings(
            path=settings_path,
            permissions=data.get("permissions", {}),
            hooks=data.get("hooks", {}),
            raw=data,
        )
    except (json.JSONDecodeError, OSError):
        return None


def save_settings(settings: ClaudeSettings) -> bool:
    """Save settings to file.

    Args:
        settings: ClaudeSettings object to save.

    Returns:
        True if saved successfully.
    """
    try:
        # Update raw data with current values
        settings.raw["permissions"] = settings.permissions
        if settings.hooks:
            settings.raw["hooks"] = settings.hooks

        settings.path.parent.mkdir(parents=True, exist_ok=True)
        settings.path.write_text(json.dumps(settings.raw, indent=2) + "\n")
        return True
    except OSError:
        return False


def backup_settings(settings_path: Optional[Path] = None) -> Optional[Path]:
    """Create a backup of settings file.

    Args:
        settings_path: Path to settings file. If None, finds automatically.

    Returns:
        Path to backup file, or None if failed.
    """
    path = settings_path or find_settings_file()
    if not path or not path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_suffix(f".backup-{timestamp}.json")

    try:
        shutil.copy2(path, backup_path)
        return backup_path
    except OSError:
        return None


# ─── Auto-approval Presets ───────────────────────────────────────────────────


PRESETS: dict[str, dict[str, Any]] = {
    "safe-reads": {
        "description": "Safe read-only operations",
        "permissions": [
            "Bash(cat:*)",
            "Bash(ls:*)",
            "Bash(find:*)",
            "Bash(grep:*)",
            "Bash(head:*)",
            "Bash(tail:*)",
            "Bash(wc:*)",
            "Bash(tree:*)",
        ],
    },
    "git-ops": {
        "description": "Common git operations",
        "permissions": [
            "Bash(git status:*)",
            "Bash(git log:*)",
            "Bash(git diff:*)",
            "Bash(git branch:*)",
            "Bash(git add:*)",
            "Bash(git commit:*)",
            "Bash(git push:*)",
            "Bash(git pull:*)",
            "Bash(git fetch:*)",
            "Bash(git restore:*)",
        ],
    },
    "github-cli": {
        "description": "GitHub CLI operations",
        "permissions": [
            "Bash(gh *:*)",
            "Bash(gh pr:*)",
            "Bash(gh issue:*)",
            "Bash(gh repo:*)",
        ],
    },
    "python-dev": {
        "description": "Python development tools",
        "permissions": [
            "Bash(python:*)",
            "Bash(python3:*)",
            "Bash(pip:*)",
            "Bash(pip3:*)",
            "Bash(pytest:*)",
            "Bash(ruff:*)",
            "Bash(black:*)",
            "Bash(mypy:*)",
        ],
    },
    "node-dev": {
        "description": "Node.js development tools",
        "permissions": [
            "Bash(node:*)",
            "Bash(npm:*)",
            "Bash(npx:*)",
            "Bash(yarn:*)",
            "Bash(pnpm:*)",
        ],
    },
    "r-dev": {
        "description": "R development tools",
        "permissions": [
            "Bash(R:*)",
            "Bash(Rscript:*)",
        ],
    },
    "web-tools": {
        "description": "Web fetching and search",
        "permissions": [
            "Bash(curl:*)",
            "Bash(wget:*)",
            "WebSearch",
            "WebFetch",
        ],
    },
    "minimal": {
        "description": "Minimal safe defaults",
        "permissions": [
            "Bash(ls:*)",
            "Bash(cat:*)",
            "Bash(echo:*)",
        ],
    },
}


def get_preset(name: str) -> Optional[dict[str, Any]]:
    """Get a preset by name."""
    return PRESETS.get(name)


def list_presets() -> dict[str, dict[str, Any]]:
    """Get all available presets."""
    return PRESETS.copy()


def add_preset_to_settings(
    settings: ClaudeSettings,
    preset_name: str,
) -> tuple[bool, list[str]]:
    """Add a preset's permissions to settings.

    Args:
        settings: ClaudeSettings to modify.
        preset_name: Name of preset to add.

    Returns:
        Tuple of (success, list of added permissions).
    """
    preset = get_preset(preset_name)
    if not preset:
        return False, []

    current = set(settings.allow_list)
    to_add = preset["permissions"]
    added = []

    for perm in to_add:
        if perm not in current:
            current.add(perm)
            added.append(perm)

    if added:
        settings.permissions["allow"] = sorted(list(current))

    return True, added
