"""Command template library management.

Provides discovery, installation, and validation of Claude Code command templates.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Command:
    """Represents an installed Claude Code command."""

    name: str
    path: Path
    category: str
    size: int

    @property
    def full_name(self) -> str:
        """Get full command name (category:name)."""
        return f"{self.category}:{self.name}" if self.category else self.name


@dataclass
class CommandTemplate:
    """Represents an available command template."""

    name: str
    path: Path
    category: str
    description: str
    frontmatter: Dict[str, Any]

    @property
    def full_name(self) -> str:
        """Get full command name (category:name)."""
        return f"{self.category}:{self.name}" if self.category else self.name

    @property
    def template_content(self) -> str:
        """Read template content."""
        return self.path.read_text()


class CommandLibrary:
    """Manage Claude Code command templates."""

    # Claude Code commands directory
    COMMANDS_DIR = Path.home() / ".claude" / "commands"

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize command library.

        Args:
            template_dir: Directory containing command templates.
                         Defaults to package templates/commands/.
        """
        if template_dir is None:
            # Default to package templates directory
            pkg_root = Path(__file__).parent.parent.parent.parent
            template_dir = pkg_root / "templates" / "commands"

        self.template_dir = template_dir

        # Ensure commands directory exists
        self.COMMANDS_DIR.mkdir(parents=True, exist_ok=True)

    def list_installed(self, category: Optional[str] = None) -> List[Command]:
        """List installed commands.

        Args:
            category: Filter by category (optional).

        Returns:
            List of installed Command objects.
        """
        commands = []

        if not self.COMMANDS_DIR.exists():
            return commands

        # Walk through commands directory
        for cmd_file in self.COMMANDS_DIR.rglob("*.md"):
            # Skip backup files
            if cmd_file.name.startswith('.'):
                continue

            # Determine category from path
            relative = cmd_file.relative_to(self.COMMANDS_DIR)
            if len(relative.parts) > 1:
                cmd_category = relative.parts[0]
                cmd_name = relative.stem
            else:
                cmd_category = ""
                cmd_name = relative.stem

            # Filter by category if specified
            if category and cmd_category != category:
                continue

            commands.append(Command(
                name=cmd_name,
                path=cmd_file,
                category=cmd_category,
                size=cmd_file.stat().st_size
            ))

        return sorted(commands, key=lambda c: (c.category, c.name))

    def list_available(self, category: Optional[str] = None) -> List[CommandTemplate]:
        """List available command templates.

        Args:
            category: Filter by category (optional).

        Returns:
            List of available CommandTemplate objects.
        """
        templates = []

        if not self.template_dir.exists():
            return templates

        # Walk through template directory
        for template_file in self.template_dir.rglob("*.md"):
            # Determine category from path
            relative = template_file.relative_to(self.template_dir)
            if len(relative.parts) > 1:
                template_category = relative.parts[0]
                template_name = relative.stem
            else:
                template_category = ""
                template_name = relative.stem

            # Filter by category if specified
            if category and template_category != category:
                continue

            # Extract metadata
            frontmatter = self._extract_frontmatter(template_file)
            description = frontmatter.get('description', 'No description')

            templates.append(CommandTemplate(
                name=template_name,
                path=template_file,
                category=template_category,
                description=description,
                frontmatter=frontmatter
            ))

        return sorted(templates, key=lambda t: (t.category, t.name))

    def browse_by_category(self) -> Dict[str, List[CommandTemplate]]:
        """Browse templates organized by category.

        Returns:
            Dictionary mapping category names to lists of templates.
        """
        templates = self.list_available()
        categories: Dict[str, List[CommandTemplate]] = {}

        for template in templates:
            category = template.category or "general"
            if category not in categories:
                categories[category] = []
            categories[category].append(template)

        return categories

    def install(self, template_name: str, force: bool = False) -> bool:
        """Install a command from template.

        Args:
            template_name: Template name (category:name or just name).
            force: If True, overwrite existing command.

        Returns:
            True if installation successful.

        Raises:
            FileNotFoundError: If template doesn't exist.
            FileExistsError: If command already exists and force=False.
        """
        # Parse template name (could be "category:name" or just "name")
        if ':' in template_name:
            category, name = template_name.split(':', 1)
        else:
            category = None
            name = template_name

        # Find template
        template = self._find_template(name, category)
        if not template:
            raise FileNotFoundError(f"Template '{template_name}' not found")

        # Determine target path
        if template.category:
            target_dir = self.COMMANDS_DIR / template.category
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / f"{template.name}.md"
        else:
            target_path = self.COMMANDS_DIR / f"{template.name}.md"

        # Check if already exists
        if target_path.exists() and not force:
            raise FileExistsError(
                f"Command '{template.full_name}' already exists. "
                "Use force=True to overwrite."
            )

        # Copy template
        target_path.write_text(template.template_content)

        return True

    def validate(self, command_name: Optional[str] = None) -> Dict[str, Any]:
        """Validate command(s).

        Args:
            command_name: Specific command to validate, or None for all.

        Returns:
            Dictionary with validation results.
        """
        commands = self.list_installed()

        if command_name:
            # Parse command name
            if ':' in command_name:
                category, name = command_name.split(':', 1)
                commands = [c for c in commands if c.name == name and c.category == category]
            else:
                commands = [c for c in commands if c.name == command_name]

        results = {
            "valid": True,
            "commands": []
        }

        for cmd in commands:
            issues = []

            # Check file exists
            if not cmd.path.exists():
                issues.append("File does not exist")

            # Check not empty
            if cmd.size == 0:
                issues.append("Empty file")

            # Check has frontmatter
            if cmd.path.exists():
                content = cmd.path.read_text()
                if not content.startswith('---'):
                    issues.append("Missing YAML frontmatter")
                else:
                    # Validate frontmatter
                    fm_issues = self._validate_frontmatter(content)
                    issues.extend(fm_issues)

            is_valid = len(issues) == 0

            results["commands"].append({
                "name": cmd.full_name,
                "valid": is_valid,
                "issues": issues
            })

            if not is_valid:
                results["valid"] = False

        return results

    def uninstall(self, command_name: str) -> bool:
        """Uninstall a command.

        Args:
            command_name: Command to uninstall (category:name or name).

        Returns:
            True if uninstalled, False if didn't exist.
        """
        # Parse command name
        if ':' in command_name:
            category, name = command_name.split(':', 1)
            target_path = self.COMMANDS_DIR / category / f"{name}.md"
        else:
            # Try to find in any category
            commands = self.list_installed()
            matching = [c for c in commands if c.name == command_name]
            if not matching:
                return False
            target_path = matching[0].path

        if not target_path.exists():
            return False

        target_path.unlink()
        return True

    # Helper methods

    def _find_template(self, name: str, category: Optional[str]) -> Optional[CommandTemplate]:
        """Find a template by name and optional category."""
        templates = self.list_available(category=category)
        for template in templates:
            if template.name == name:
                return template
        return None

    def _extract_frontmatter(self, template_path: Path) -> Dict[str, Any]:
        """Extract YAML frontmatter from template."""
        content = template_path.read_text()

        # Match frontmatter between --- markers
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return {}

        frontmatter_text = match.group(1)
        frontmatter = {}

        # Simple YAML parsing (just key: value pairs)
        for line in frontmatter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip()

        return frontmatter

    def _validate_frontmatter(self, content: str) -> List[str]:
        """Validate frontmatter has required fields."""
        issues = []

        # Extract frontmatter
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return ["Invalid frontmatter format"]

        frontmatter_text = match.group(1)

        # Check for required fields
        required_fields = ['description']
        for field in required_fields:
            if f"{field}:" not in frontmatter_text:
                issues.append(f"Missing required field: {field}")

        return issues
