"""Hook management for Claude Code.

Provides discovery, installation, validation, and testing of Claude Code hooks.
"""

import os
import stat
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Hook:
    """Represents an installed Claude Code hook."""

    name: str
    path: Path
    executable: bool
    size: int

    @property
    def is_valid(self) -> bool:
        """Check if hook is valid (exists and is executable)."""
        return self.path.exists() and self.executable


@dataclass
class HookTemplate:
    """Represents an available hook template."""

    name: str
    path: Path
    description: str
    hook_type: str  # SessionStart, UserPromptSubmit, PreToolUse, etc.

    @property
    def template_content(self) -> str:
        """Read template content."""
        return self.path.read_text()


class HookManager:
    """Manage Claude Code hooks."""

    # Claude Code hook directory
    HOOK_DIR = Path.home() / ".claude" / "hooks"

    # Hook types available in Claude Code
    HOOK_TYPES = [
        "SessionStart",
        "SessionEnd",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "SubagentStop",
        "Stop",
        "PreCompact",
        "Notification",
    ]

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize hook manager.

        Args:
            template_dir: Directory containing hook templates.
                         Defaults to package templates/hooks/.
        """
        if template_dir is None:
            # Default to package templates directory
            pkg_root = Path(__file__).parent.parent.parent.parent
            template_dir = pkg_root / "templates" / "hooks"

        self.template_dir = template_dir

        # Ensure hook directory exists
        self.HOOK_DIR.mkdir(parents=True, exist_ok=True)

    def list_installed(self) -> List[Hook]:
        """List all installed hooks.

        Returns:
            List of installed Hook objects.
        """
        hooks = []

        if not self.HOOK_DIR.exists():
            return hooks

        for hook_file in self.HOOK_DIR.iterdir():
            if hook_file.is_file() and not hook_file.name.startswith('.'):
                # Check if executable
                is_executable = os.access(hook_file, os.X_OK)

                hooks.append(Hook(
                    name=hook_file.name,
                    path=hook_file,
                    executable=is_executable,
                    size=hook_file.stat().st_size
                ))

        return sorted(hooks, key=lambda h: h.name)

    def list_available(self) -> List[HookTemplate]:
        """List all available hook templates.

        Returns:
            List of available HookTemplate objects.
        """
        templates = []

        if not self.template_dir.exists():
            return templates

        for template_file in self.template_dir.glob("*.sh"):
            # Extract metadata from template
            description = self._extract_description(template_file)
            hook_type = self._extract_hook_type(template_file)

            templates.append(HookTemplate(
                name=template_file.stem,  # Without .sh extension
                path=template_file,
                description=description,
                hook_type=hook_type
            ))

        return sorted(templates, key=lambda t: t.name)

    def install(self, template_name: str, force: bool = False) -> bool:
        """Install a hook from template.

        Args:
            template_name: Name of the template to install (without .sh).
            force: If True, overwrite existing hook.

        Returns:
            True if installation successful, False otherwise.

        Raises:
            FileNotFoundError: If template doesn't exist.
            FileExistsError: If hook already exists and force=False.
        """
        # Find template
        template_path = self.template_dir / f"{template_name}.sh"

        if not template_path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found")

        # Determine target path
        target_path = self.HOOK_DIR / f"{template_name}.sh"

        # Check if already exists
        if target_path.exists() and not force:
            raise FileExistsError(
                f"Hook '{template_name}' already exists. Use force=True to overwrite."
            )

        # Copy template
        target_path.write_text(template_path.read_text())

        # Make executable
        self._make_executable(target_path)

        return True

    def validate(self, hook_name: Optional[str] = None) -> Dict[str, Any]:
        """Validate hook(s).

        Args:
            hook_name: Specific hook to validate, or None for all.

        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "hooks": [
                    {
                        "name": str,
                        "valid": bool,
                        "issues": List[str]
                    }
                ]
            }
        """
        hooks = self.list_installed()

        if hook_name:
            hooks = [h for h in hooks if h.name == hook_name or h.name == f"{hook_name}.sh"]

        results = {
            "valid": True,
            "hooks": []
        }

        for hook in hooks:
            issues = []

            # Check exists
            if not hook.path.exists():
                issues.append("File does not exist")

            # Check executable
            if not hook.executable:
                issues.append("Not executable (run: chmod +x)")

            # Check size (warn if empty)
            if hook.size == 0:
                issues.append("Empty file")

            # Check shebang
            if hook.path.exists():
                first_line = hook.path.read_text().split('\n')[0]
                if not first_line.startswith('#!'):
                    issues.append("Missing shebang (#!/bin/bash)")

            is_valid = len(issues) == 0

            results["hooks"].append({
                "name": hook.name,
                "valid": is_valid,
                "issues": issues
            })

            if not is_valid:
                results["valid"] = False

        return results

    def test(self, hook_name: str) -> Dict[str, Any]:
        """Test a hook by executing it.

        Args:
            hook_name: Name of hook to test.

        Returns:
            Dictionary with test results:
            {
                "success": bool,
                "exit_code": int,
                "stdout": str,
                "stderr": str,
                "duration_ms": float
            }
        """
        hook_path = self.HOOK_DIR / hook_name
        if not hook_path.exists():
            hook_path = self.HOOK_DIR / f"{hook_name}.sh"

        if not hook_path.exists():
            raise FileNotFoundError(f"Hook '{hook_name}' not found")

        import time
        start = time.time()

        try:
            result = subprocess.run(
                [str(hook_path)],
                capture_output=True,
                text=True,
                timeout=5.0  # 5 second timeout
            )

            duration_ms = (time.time() - start) * 1000

            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration_ms": duration_ms
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Hook execution timed out (>5s)",
                "duration_ms": 5000.0
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "duration_ms": 0.0
            }

    def uninstall(self, hook_name: str) -> bool:
        """Uninstall a hook.

        Args:
            hook_name: Name of hook to uninstall.

        Returns:
            True if uninstalled, False if didn't exist.
        """
        hook_path = self.HOOK_DIR / hook_name
        if not hook_path.exists():
            hook_path = self.HOOK_DIR / f"{hook_name}.sh"

        if not hook_path.exists():
            return False

        hook_path.unlink()
        return True

    # Helper methods

    def _make_executable(self, path: Path) -> None:
        """Make a file executable."""
        current = path.stat().st_mode
        path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def _extract_description(self, template_path: Path) -> str:
        """Extract description from template comments.

        Looks for lines like:
        # Description: This hook does X
        """
        content = template_path.read_text()
        for line in content.split('\n')[:10]:  # Check first 10 lines
            if line.startswith('# Description:'):
                return line.replace('# Description:', '').strip()
            # Also accept just second line after shebang
            if line.startswith('# ') and 'hook' in line.lower():
                return line[2:].strip()

        return "No description available"

    def _extract_hook_type(self, template_path: Path) -> str:
        """Extract hook type from template comments.

        Looks for lines like:
        # Hook Type: SessionStart
        """
        content = template_path.read_text()
        for line in content.split('\n')[:10]:
            if line.startswith('# Hook Type:'):
                return line.replace('# Hook Type:', '').strip()
            # Also check filename patterns
            for hook_type in self.HOOK_TYPES:
                if hook_type.lower() in template_path.stem.lower():
                    return hook_type

        return "Unknown"
