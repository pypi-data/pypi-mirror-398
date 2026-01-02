"""Status bar builder and management CLI.

Phase 3.2: Build and customize status bars for Claude Code, OpenCode, and terminals.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

app = typer.Typer(
    help="Build and customize status bars.",
    no_args_is_help=True,
)
console = Console()


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class StatusBarConfig:
    """Represents a status bar configuration."""

    name: str
    type: str = "command"  # command, static
    command: str = ""
    static_text: str = ""
    update_interval: int = 300  # milliseconds
    components: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to Claude Code settings format."""
        if self.type == "command":
            return {
                "type": "command",
                "command": self.command,
            }
        return {
            "type": "static",
            "text": self.static_text,
        }


# Built-in status bar templates
STATUSBAR_TEMPLATES = {
    "minimal": {
        "description": "Simple model and time display",
        "components": ["model", "time"],
        "script": """#!/bin/bash
MODEL="${CLAUDE_MODEL:-sonnet}"
echo "$MODEL | $(date +%H:%M)"
""",
    },
    "powerlevel10k": {
        "description": "Full-featured p10k style status bar",
        "components": ["project", "git", "model", "time", "duration", "changes"],
        "script": """#!/bin/bash
# Powerlevel10k style status bar for Claude Code
# See: ~/.claude/statusline-p10k.sh for full implementation
PROJECT=$(basename "$PWD")
BRANCH=$(git branch --show-current 2>/dev/null || echo "")
MODEL="${CLAUDE_MODEL:-sonnet}"
TIME=$(date +%H:%M)

if [ -n "$BRANCH" ]; then
    echo "$PROJECT  $BRANCH | $MODEL | $TIME"
else
    echo "$PROJECT | $MODEL | $TIME"
fi
""",
    },
    "developer": {
        "description": "Developer-focused with git and project info",
        "components": ["project", "git", "model", "duration"],
        "script": """#!/bin/bash
PROJECT=$(basename "$PWD")
BRANCH=$(git branch --show-current 2>/dev/null)
DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
MODEL="${CLAUDE_MODEL:-sonnet}"

STATUS="$PROJECT"
[ -n "$BRANCH" ] && STATUS="$STATUS  $BRANCH"
[ "$DIRTY" -gt 0 ] && STATUS="$STATUS *"
echo "$STATUS | $MODEL"
""",
    },
    "stats": {
        "description": "Statistics and metrics focused",
        "components": ["model", "lines_changed", "cost", "duration"],
        "script": """#!/bin/bash
MODEL="${CLAUDE_MODEL:-sonnet}"
ADDED="${CLAUDE_LINES_ADDED:-0}"
REMOVED="${CLAUDE_LINES_REMOVED:-0}"
COST="${CLAUDE_TOTAL_COST:-0.00}"
echo "$MODEL | +$ADDED/-$REMOVED | \\$$COST"
""",
    },
}


def get_statusbar_dir() -> Path:
    """Get the status bar scripts directory."""
    return Path.home() / ".claude" / "statusbars"


def get_claude_settings_path() -> Path:
    """Get Claude Code settings path."""
    return Path.home() / ".claude" / "settings.json"


def load_current_statusbar() -> dict[str, Any] | None:
    """Load current status bar config from Claude Code settings."""
    settings_path = get_claude_settings_path()
    if not settings_path.exists():
        return None

    try:
        data = json.loads(settings_path.read_text())
        return data.get("statusLine")
    except (json.JSONDecodeError, OSError):
        return None


def save_statusbar_to_settings(config: StatusBarConfig) -> bool:
    """Save status bar config to Claude Code settings."""
    settings_path = get_claude_settings_path()

    try:
        if settings_path.exists():
            data = json.loads(settings_path.read_text())
        else:
            data = {}

        data["statusLine"] = config.to_dict()
        settings_path.write_text(json.dumps(data, indent=2))
        return True
    except (json.JSONDecodeError, OSError):
        return False


def save_script(name: str, script: str) -> Path:
    """Save a status bar script."""
    statusbar_dir = get_statusbar_dir()
    statusbar_dir.mkdir(parents=True, exist_ok=True)

    script_path = statusbar_dir / f"{name}.sh"
    script_path.write_text(script)
    script_path.chmod(0o755)
    return script_path


def list_saved_scripts() -> list[str]:
    """List saved status bar scripts."""
    statusbar_dir = get_statusbar_dir()
    if not statusbar_dir.exists():
        return []
    return [f.stem for f in statusbar_dir.glob("*.sh")]


# =============================================================================
# CLI Commands
# =============================================================================


@app.command("status")
def statusbar_status() -> None:
    """Show current status bar configuration."""
    console.print("[bold cyan]Status Bar Configuration[/]\n")

    current = load_current_statusbar()
    if not current:
        console.print("[yellow]No status bar configured.[/]")
        console.print("\nUse 'ait statusbar set <template>' to configure one.")
        return

    if current.get("type") == "command":
        console.print("[green]✓[/] Type: Command-based")
        console.print(f"[green]✓[/] Command: {current.get('command', 'unknown')}")
    else:
        console.print("[green]✓[/] Type: Static")
        console.print(f"[green]✓[/] Text: {current.get('text', 'unknown')}")

    # Check if script exists
    if current.get("type") == "command":
        cmd = current.get("command", "")
        if "/bin/bash" in cmd:
            script_path = cmd.split()[-1] if cmd.split() else ""
            if script_path and Path(script_path).exists():
                console.print(f"[green]✓[/] Script exists: {script_path}")
            else:
                console.print(f"[red]✗[/] Script not found: {script_path}")


@app.command("templates")
def statusbar_templates() -> None:
    """List available status bar templates."""
    table = Table(title="Status Bar Templates", border_style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Components")
    table.add_column("Description")

    for name, template in STATUSBAR_TEMPLATES.items():
        table.add_row(
            name,
            ", ".join(template["components"]),
            template["description"],
        )

    console.print(table)
    console.print("\n[dim]Use 'ait statusbar preview <template>' to see the script.[/]")


@app.command("preview")
def statusbar_preview(
    template: str = typer.Argument(..., help="Template name to preview."),
) -> None:
    """Preview a status bar template script."""
    if template not in STATUSBAR_TEMPLATES:
        console.print(f"[red]Unknown template: {template}[/]")
        console.print("Use 'ait statusbar templates' to see available templates.")
        raise typer.Exit(1)

    tmpl = STATUSBAR_TEMPLATES[template]
    console.print(f"[bold cyan]Template: {template}[/]")
    console.print(f"[dim]{tmpl['description']}[/]\n")

    syntax = Syntax(tmpl["script"], "bash", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"{template}.sh", border_style="cyan"))


@app.command("set")
def statusbar_set(
    template: str = typer.Argument(..., help="Template name or script path."),
    save_as: str = typer.Option(None, "--save", "-s", help="Save script with this name."),
) -> None:
    """Set the active status bar."""
    # Check if it's a template
    if template in STATUSBAR_TEMPLATES:
        tmpl = STATUSBAR_TEMPLATES[template]
        script = tmpl["script"]

        # Save script
        script_name = save_as or template
        script_path = save_script(script_name, script)
        console.print(f"[green]✓[/] Saved script: {script_path}")

        # Create config
        config = StatusBarConfig(
            name=script_name,
            type="command",
            command=f"/bin/bash {script_path}",
        )
    elif Path(template).exists():
        # It's a path to an existing script
        script_path = Path(template).resolve()
        config = StatusBarConfig(
            name=script_path.stem,
            type="command",
            command=f"/bin/bash {script_path}",
        )
    else:
        console.print(f"[red]Template or script not found: {template}[/]")
        raise typer.Exit(1)

    # Save to settings
    if save_statusbar_to_settings(config):
        console.print(f"[green]✓[/] Set status bar: {config.name}")
        console.print(f"  Command: {config.command}")
        console.print("\n[dim]Restart Claude Code to see changes.[/]")
    else:
        console.print("[red]Failed to update settings.[/]")
        raise typer.Exit(1)


@app.command("list")
def statusbar_list() -> None:
    """List saved status bar scripts."""
    scripts = list_saved_scripts()

    if not scripts:
        console.print("[yellow]No saved status bar scripts.[/]")
        console.print("\nUse 'ait statusbar set <template>' to create one.")
        return

    current = load_current_statusbar()
    current_script = ""
    if current and current.get("type") == "command":
        cmd = current.get("command", "")
        if cmd:
            current_script = Path(cmd.split()[-1]).stem if cmd.split() else ""

    table = Table(title="Saved Status Bars", border_style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Path")
    table.add_column("Active", justify="center")

    statusbar_dir = get_statusbar_dir()
    for script in sorted(scripts):
        is_active = "●" if script == current_script else ""
        script_path = statusbar_dir / f"{script}.sh"
        table.add_row(
            script,
            str(script_path),
            f"[green]{is_active}[/]" if is_active else "",
        )

    console.print(table)


@app.command("create")
def statusbar_create(
    name: str = typer.Argument(..., help="Name for the new status bar."),
    template: str = typer.Option("minimal", "--template", "-t", help="Template to start from."),
) -> None:
    """Create a custom status bar script."""
    if template not in STATUSBAR_TEMPLATES:
        console.print(f"[red]Unknown template: {template}[/]")
        raise typer.Exit(1)

    # Check if already exists
    statusbar_dir = get_statusbar_dir()
    script_path = statusbar_dir / f"{name}.sh"
    if script_path.exists():
        console.print(f"[yellow]Script '{name}' already exists.[/]")
        console.print(f"  Location: {script_path}")
        return

    # Create from template
    tmpl = STATUSBAR_TEMPLATES[template]
    script = f"""#!/bin/bash
# Custom status bar: {name}
# Based on: {template} template
# Edit this script to customize your status bar

{tmpl['script'].strip()}
"""

    script_path = save_script(name, script)
    console.print(f"[green]Created status bar script:[/] {script_path}")
    console.print("\n[dim]Edit the script, then run 'ait statusbar set <name>' to activate.[/]")


@app.command("test")
def statusbar_test(
    name: str = typer.Argument(None, help="Script name to test (or current if not specified)."),
) -> None:
    """Test a status bar script."""
    import subprocess

    if name:
        script_path = get_statusbar_dir() / f"{name}.sh"
        if not script_path.exists():
            console.print(f"[red]Script not found: {name}[/]")
            raise typer.Exit(1)
        command = f"/bin/bash {script_path}"
    else:
        current = load_current_statusbar()
        if not current or current.get("type") != "command":
            console.print("[yellow]No command-based status bar configured.[/]")
            return
        command = current.get("command", "")

    console.print(f"[bold cyan]Testing:[/] {command}\n")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            console.print(f"[green]Output:[/] {result.stdout.strip()}")
        else:
            console.print(f"[red]Error (exit {result.returncode}):[/]")
            if result.stderr:
                console.print(result.stderr)
    except subprocess.TimeoutExpired:
        console.print("[red]Timeout: Script took too long (>5s)[/]")
    except Exception as e:
        console.print(f"[red]Failed: {e}[/]")


@app.command("components")
def statusbar_components() -> None:
    """List available status bar components."""
    components = {
        "model": {
            "description": "Current Claude model",
            "variable": "CLAUDE_MODEL",
            "example": "sonnet",
        },
        "time": {
            "description": "Current time",
            "variable": "-",
            "example": "14:30",
        },
        "project": {
            "description": "Project/directory name",
            "variable": "PWD",
            "example": "aiterm",
        },
        "git": {
            "description": "Git branch and status",
            "variable": "-",
            "example": " main *",
        },
        "duration": {
            "description": "Session duration",
            "variable": "CLAUDE_DURATION",
            "example": "5m",
        },
        "lines_changed": {
            "description": "Lines added/removed",
            "variable": "CLAUDE_LINES_ADDED/REMOVED",
            "example": "+50/-10",
        },
        "cost": {
            "description": "Session cost",
            "variable": "CLAUDE_TOTAL_COST",
            "example": "$0.15",
        },
        "workspace": {
            "description": "Workspace path",
            "variable": "CLAUDE_WORKSPACE",
            "example": "/Users/dt/project",
        },
    }

    table = Table(title="Status Bar Components", border_style="cyan")
    table.add_column("Component", style="bold")
    table.add_column("Description")
    table.add_column("Variable")
    table.add_column("Example")

    for name, info in components.items():
        table.add_row(
            name,
            info["description"],
            info["variable"],
            info["example"],
        )

    console.print(table)
    console.print("\n[dim]Use these components in your status bar scripts.[/]")


@app.command("disable")
def statusbar_disable() -> None:
    """Disable the status bar."""
    settings_path = get_claude_settings_path()

    try:
        if settings_path.exists():
            data = json.loads(settings_path.read_text())
            if "statusLine" in data:
                del data["statusLine"]
                settings_path.write_text(json.dumps(data, indent=2))
                console.print("[green]Status bar disabled.[/]")
            else:
                console.print("[yellow]No status bar configured.[/]")
        else:
            console.print("[yellow]No settings file found.[/]")
    except (json.JSONDecodeError, OSError) as e:
        console.print(f"[red]Failed: {e}[/]")
        raise typer.Exit(1)
