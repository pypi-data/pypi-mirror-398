"""IDE integration management for aiterm.

Phase 4.1: Support for Positron, Zed, VS Code, and other IDEs.
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

app = typer.Typer(
    help="Manage IDE integrations.",
    no_args_is_help=True,
)
console = Console()


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class IDEConfig:
    """Represents an IDE configuration."""

    name: str
    display_name: str
    config_path: Path
    supported_features: list[str] = field(default_factory=list)
    installed: bool = False
    extensions: dict[str, Any] = field(default_factory=dict)


# IDE Definitions
IDE_CONFIGS = {
    "vscode": IDEConfig(
        name="vscode",
        display_name="Visual Studio Code",
        config_path=Path.home() / ".vscode" / "settings.json",
        supported_features=["terminal", "extensions", "keybindings", "tasks"],
    ),
    "positron": IDEConfig(
        name="positron",
        display_name="Positron",
        config_path=Path.home() / ".positron" / "settings.json",
        supported_features=["terminal", "extensions", "r-support", "python-support"],
    ),
    "zed": IDEConfig(
        name="zed",
        display_name="Zed",
        config_path=Path.home() / ".config" / "zed" / "settings.json",
        supported_features=["terminal", "themes", "keybindings"],
    ),
    "cursor": IDEConfig(
        name="cursor",
        display_name="Cursor",
        config_path=Path.home() / ".cursor" / "settings.json",
        supported_features=["terminal", "ai-features", "extensions"],
    ),
    "windsurf": IDEConfig(
        name="windsurf",
        display_name="Windsurf",
        config_path=Path.home() / ".windsurf" / "settings.json",
        supported_features=["terminal", "ai-features", "extensions"],
    ),
}

# Recommended extensions for AI development
AI_DEV_EXTENSIONS = {
    "vscode": [
        {"id": "continue.continue", "name": "Continue", "desc": "AI code assistant"},
        {"id": "saoudrizwan.claude-dev", "name": "Claude Dev", "desc": "Claude Code in VS Code"},
        {"id": "github.copilot", "name": "GitHub Copilot", "desc": "AI pair programmer"},
    ],
    "positron": [
        {"id": "positron.r", "name": "R Language", "desc": "R language support"},
        {"id": "positron.python", "name": "Python", "desc": "Python support"},
    ],
    "zed": [
        {"id": "zed-assistant", "name": "Zed Assistant", "desc": "Built-in AI assistant"},
    ],
}


def check_ide_installed(ide_name: str) -> bool:
    """Check if an IDE is installed."""
    import shutil

    commands = {
        "vscode": "code",
        "positron": "positron",
        "zed": "zed",
        "cursor": "cursor",
        "windsurf": "windsurf",
    }
    cmd = commands.get(ide_name)
    return shutil.which(cmd) is not None if cmd else False


def get_ide_config(ide_name: str) -> IDEConfig | None:
    """Get IDE configuration."""
    config = IDE_CONFIGS.get(ide_name)
    if config:
        config.installed = check_ide_installed(ide_name)
    return config


def load_ide_settings(ide_name: str) -> dict[str, Any]:
    """Load IDE settings file."""
    config = get_ide_config(ide_name)
    if not config or not config.config_path.exists():
        return {}

    try:
        return json.loads(config.config_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_ide_settings(ide_name: str, settings: dict[str, Any]) -> bool:
    """Save IDE settings file."""
    config = get_ide_config(ide_name)
    if not config:
        return False

    try:
        config.config_path.parent.mkdir(parents=True, exist_ok=True)
        config.config_path.write_text(json.dumps(settings, indent=2))
        return True
    except OSError:
        return False


# =============================================================================
# CLI Commands
# =============================================================================


@app.command("list")
def ide_list() -> None:
    """List supported IDEs and their status."""
    table = Table(title="Supported IDEs", border_style="cyan")
    table.add_column("IDE", style="bold")
    table.add_column("Installed", justify="center")
    table.add_column("Config Exists", justify="center")
    table.add_column("Features")

    for name, config in IDE_CONFIGS.items():
        installed = check_ide_installed(name)
        config_exists = config.config_path.exists()

        table.add_row(
            config.display_name,
            "[green]✓[/]" if installed else "[dim]✗[/]",
            "[green]✓[/]" if config_exists else "[dim]✗[/]",
            ", ".join(config.supported_features[:3]),
        )

    console.print(table)


@app.command("status")
def ide_status(
    ide: str = typer.Argument(..., help="IDE name (vscode, positron, zed, cursor, windsurf)."),
) -> None:
    """Show detailed status for a specific IDE."""
    config = get_ide_config(ide)
    if not config:
        console.print(f"[red]Unknown IDE: {ide}[/]")
        console.print(f"Supported: {', '.join(IDE_CONFIGS.keys())}")
        raise typer.Exit(1)

    content = []
    content.append(f"[bold]Name:[/] {config.display_name}")
    content.append(f"[bold]Installed:[/] {'Yes' if config.installed else 'No'}")
    content.append(f"[bold]Config Path:[/] {config.config_path}")
    content.append(f"[bold]Config Exists:[/] {'Yes' if config.config_path.exists() else 'No'}")
    content.append(f"[bold]Features:[/] {', '.join(config.supported_features)}")

    # Check settings
    settings = load_ide_settings(ide)
    if settings:
        content.append(f"[bold]Settings Keys:[/] {len(settings)}")

    console.print(Panel(
        "\n".join(content),
        title=f"{config.display_name} Status",
        border_style="cyan",
    ))


@app.command("extensions")
def ide_extensions(
    ide: str = typer.Argument(..., help="IDE name."),
) -> None:
    """List recommended AI development extensions for an IDE."""
    extensions = AI_DEV_EXTENSIONS.get(ide, [])

    if not extensions:
        console.print(f"[yellow]No extension recommendations for {ide}.[/]")
        return

    table = Table(title=f"Recommended Extensions for {ide}", border_style="cyan")
    table.add_column("Extension", style="bold")
    table.add_column("ID")
    table.add_column("Description")

    for ext in extensions:
        table.add_row(ext["name"], ext["id"], ext["desc"])

    console.print(table)


@app.command("configure")
def ide_configure(
    ide: str = typer.Argument(..., help="IDE name."),
    terminal_font: str = typer.Option(None, "--font", help="Terminal font family."),
    terminal_size: int = typer.Option(None, "--size", help="Terminal font size."),
    enable_ai: bool = typer.Option(None, "--ai/--no-ai", help="Enable AI features."),
) -> None:
    """Configure IDE settings for AI development."""
    config = get_ide_config(ide)
    if not config:
        console.print(f"[red]Unknown IDE: {ide}[/]")
        raise typer.Exit(1)

    settings = load_ide_settings(ide)
    changes = []

    # Terminal settings
    if terminal_font:
        if ide in ("vscode", "cursor", "windsurf"):
            settings["terminal.integrated.fontFamily"] = terminal_font
        elif ide == "zed":
            if "terminal" not in settings:
                settings["terminal"] = {}
            settings["terminal"]["font_family"] = terminal_font
        changes.append(f"terminal font → {terminal_font}")

    if terminal_size:
        if ide in ("vscode", "cursor", "windsurf"):
            settings["terminal.integrated.fontSize"] = terminal_size
        elif ide == "zed":
            if "terminal" not in settings:
                settings["terminal"] = {}
            settings["terminal"]["font_size"] = terminal_size
        changes.append(f"terminal size → {terminal_size}")

    if enable_ai is not None:
        # IDE-specific AI settings
        if ide == "zed":
            if "assistant" not in settings:
                settings["assistant"] = {}
            settings["assistant"]["enabled"] = enable_ai
        elif ide in ("vscode", "cursor", "windsurf"):
            settings["editor.inlineSuggest.enabled"] = enable_ai
        changes.append(f"AI features → {'enabled' if enable_ai else 'disabled'}")

    if not changes:
        console.print("[yellow]No changes specified.[/]")
        console.print("Use --font, --size, or --ai to configure.")
        return

    if save_ide_settings(ide, settings):
        console.print(f"[green]Updated {config.display_name} settings:[/]")
        for change in changes:
            console.print(f"  {change}")
    else:
        console.print("[red]Failed to save settings.[/]")
        raise typer.Exit(1)


@app.command("terminal-profile")
def ide_terminal_profile(
    ide: str = typer.Argument(..., help="IDE name."),
    profile_name: str = typer.Option("aiterm", "--name", help="Profile name."),
) -> None:
    """Add an aiterm-optimized terminal profile to an IDE."""
    config = get_ide_config(ide)
    if not config:
        console.print(f"[red]Unknown IDE: {ide}[/]")
        raise typer.Exit(1)

    if "terminal" not in config.supported_features:
        console.print(f"[yellow]{config.display_name} doesn't support custom terminal profiles.[/]")
        return

    settings = load_ide_settings(ide)

    # Add terminal profile
    if ide in ("vscode", "cursor", "windsurf"):
        if "terminal.integrated.profiles.osx" not in settings:
            settings["terminal.integrated.profiles.osx"] = {}

        settings["terminal.integrated.profiles.osx"][profile_name] = {
            "path": "/bin/zsh",
            "args": ["-l"],
            "env": {
                "AITERM": "1",
                "TERM_PROGRAM": "vscode",
            },
        }
        console.print(f"[green]Added terminal profile '{profile_name}'[/]")

    elif ide == "zed":
        if "terminal" not in settings:
            settings["terminal"] = {}

        settings["terminal"]["shell"] = {
            "program": "/bin/zsh",
            "args": ["-l"],
        }
        settings["terminal"]["env"] = {
            "AITERM": "1",
        }
        console.print(f"[green]Configured Zed terminal for aiterm[/]")

    if save_ide_settings(ide, settings):
        console.print(f"[dim]Restart {config.display_name} to apply changes.[/]")
    else:
        console.print("[red]Failed to save settings.[/]")
        raise typer.Exit(1)


@app.command("sync-theme")
def ide_sync_theme(
    ide: str = typer.Argument(..., help="IDE name."),
    theme: str = typer.Option("dark", "--theme", "-t", help="Theme (dark, light, solarized)."),
) -> None:
    """Sync terminal theme settings with aiterm profiles."""
    config = get_ide_config(ide)
    if not config:
        console.print(f"[red]Unknown IDE: {ide}[/]")
        raise typer.Exit(1)

    # Theme mappings
    theme_mappings = {
        "vscode": {
            "dark": "Default Dark+",
            "light": "Default Light+",
            "solarized": "Solarized Dark",
        },
        "zed": {
            "dark": "One Dark",
            "light": "One Light",
            "solarized": "Solarized Dark",
        },
        "positron": {
            "dark": "Default Dark",
            "light": "Default Light",
            "solarized": "Solarized Dark",
        },
    }

    ide_themes = theme_mappings.get(ide, {})
    target_theme = ide_themes.get(theme)

    if not target_theme:
        console.print(f"[yellow]No theme mapping for {ide} + {theme}[/]")
        return

    settings = load_ide_settings(ide)

    if ide in ("vscode", "cursor", "windsurf"):
        settings["workbench.colorTheme"] = target_theme
    elif ide == "zed":
        settings["theme"] = target_theme
    elif ide == "positron":
        settings["workbench.colorTheme"] = target_theme

    if save_ide_settings(ide, settings):
        console.print(f"[green]Set {config.display_name} theme to {target_theme}[/]")
    else:
        console.print("[red]Failed to save settings.[/]")
        raise typer.Exit(1)


@app.command("open")
def ide_open(
    ide: str = typer.Argument(..., help="IDE name."),
    path: Path = typer.Argument(None, help="Path to open."),
) -> None:
    """Open a path in the specified IDE."""
    import subprocess

    config = get_ide_config(ide)
    if not config:
        console.print(f"[red]Unknown IDE: {ide}[/]")
        raise typer.Exit(1)

    if not config.installed:
        console.print(f"[red]{config.display_name} is not installed.[/]")
        raise typer.Exit(1)

    commands = {
        "vscode": "code",
        "positron": "positron",
        "zed": "zed",
        "cursor": "cursor",
        "windsurf": "windsurf",
    }
    cmd = commands.get(ide)
    target = str(path or Path.cwd())

    try:
        subprocess.run([cmd, target], check=True)
        console.print(f"[green]Opened in {config.display_name}[/]")
    except subprocess.CalledProcessError:
        console.print(f"[red]Failed to open {config.display_name}[/]")
        raise typer.Exit(1)


@app.command("compare")
def ide_compare() -> None:
    """Compare configurations across installed IDEs."""
    console.print("[bold cyan]IDE Configuration Comparison[/]\n")

    installed = []
    for name, config in IDE_CONFIGS.items():
        if check_ide_installed(name):
            installed.append((name, config))

    if not installed:
        console.print("[yellow]No supported IDEs installed.[/]")
        return

    table = Table(border_style="dim")
    table.add_column("Setting", style="bold")
    for name, config in installed:
        table.add_column(config.display_name)

    # Compare key settings
    settings_to_compare = [
        ("Config exists", lambda s: "Yes" if s else "No", lambda n: load_ide_settings(n)),
        ("Terminal font", lambda s: s.get("terminal.integrated.fontFamily", "default"), lambda n: load_ide_settings(n)),
        ("AI enabled", lambda s: "Yes" if s.get("editor.inlineSuggest.enabled", True) else "No", lambda n: load_ide_settings(n)),
    ]

    for label, extract, loader in settings_to_compare:
        row = [label]
        for name, config in installed:
            try:
                settings = loader(name)
                row.append(extract(settings))
            except Exception:
                row.append("[dim]N/A[/]")
        table.add_row(*row)

    console.print(table)
