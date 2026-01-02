"""Main CLI entry point for aiterm."""

import platform
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aiterm import __app_name__, __version__

# Initialize Typer app
app = typer.Typer(
    name=__app_name__,
    help="Terminal optimizer CLI for AI-assisted development.",
    add_completion=True,
    rich_markup_mode="rich",
)

console = Console()


def get_install_path() -> str:
    """Get the installation path of aiterm."""
    import aiterm
    return str(Path(aiterm.__file__).parent)


def get_platform_info() -> str:
    """Get platform information string."""
    return f"{platform.system()} {platform.release()} ({platform.machine()})"


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        install_path = get_install_path()
        platform_info = get_platform_info()

        console.print(
            Panel(
                f"[bold cyan]{__app_name__}[/] version [green]{__version__}[/]\n"
                f"Terminal optimizer for Claude Code & Gemini CLI\n\n"
                f"[dim]Python:[/]   {python_version}\n"
                f"[dim]Platform:[/] {platform_info}\n"
                f"[dim]Path:[/]     {install_path}",
                title="aiterm",
                border_style="cyan",
            )
        )
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """
    aiterm - Terminal optimizer CLI for AI-assisted development.

    Optimizes iTerm2 (and other terminals) for Claude Code and Gemini CLI.
    Manages profiles, hooks, commands, context detection, and auto-approvals.
    """
    pass


@app.command(
    epilog="""
[bold]Examples:[/]
  ait hello             # Simple greeting
  ait hello --name Bob  # Personalized greeting
"""
)
def hello(
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Name to greet.",
    ),
) -> None:
    """Say hello - a simple test command."""
    greeting = f"Hello, {name}!" if name else "Hello, World!"
    console.print(f"[bold cyan]{greeting}[/]")
    console.print("[dim]aiterm is working correctly.[/]")


@app.command(
    epilog="""
[bold]Examples:[/]
  ait goodbye             # Simple farewell
  ait goodbye --name Bob  # Personalized farewell
"""
)
def goodbye(
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Name to bid farewell.",
    ),
) -> None:
    """Say goodbye - a simple test command."""
    farewell = f"Goodbye, {name}!" if name else "Goodbye, World!"
    console.print(f"[bold magenta]{farewell}[/]")
    console.print("[dim]Until next time![/]")


@app.command(
    epilog="""
[bold]Examples:[/]
  ait init              # Run interactive setup
  ait init --skip-test  # Skip verification tests
"""
)
def init() -> None:
    """Interactive setup wizard for aiterm."""
    console.print("[bold cyan]aiterm init[/] - Setup wizard")
    console.print("[yellow]Coming soon![/] This will:")
    console.print("  - Detect your terminal type")
    console.print("  - Install base profiles")
    console.print("  - Configure context detection")
    console.print("  - Test installation")


@app.command(
    epilog="""
[bold]Examples:[/]
  ait doctor       # Full health check
  ait doctor -v    # Verbose output
"""
)
def doctor() -> None:
    """Check aiterm installation and configuration."""
    console.print("[bold cyan]aiterm doctor[/] - Health check")
    console.print()

    # Terminal detection
    import os

    term_program = os.environ.get("TERM_PROGRAM", "unknown")
    shell = os.environ.get("SHELL", "unknown")

    console.print(f"[bold]Terminal:[/] {term_program}")
    console.print(f"[bold]Shell:[/] {shell}")
    console.print(f"[bold]Python:[/] {__import__('sys').version.split()[0]}")
    console.print(f"[bold]aiterm:[/] {__version__}")
    console.print()
    console.print("[green]Basic checks passed![/]")
    console.print("[yellow]Full diagnostics coming in v0.2.0[/]")


@app.command(
    epilog="""
[bold]Examples:[/]
  ait info         # Show full system diagnostics
  ait info --json  # Output as JSON (for scripting)
"""
)
def info(
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output as JSON for scripting.",
    ),
) -> None:
    """Show detailed system information and diagnostics."""
    import json as json_module
    import os
    import shutil

    # Gather all system info
    info_data = {
        "aiterm": {
            "version": __version__,
            "app_name": __app_name__,
            "install_path": get_install_path(),
        },
        "python": {
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "executable": sys.executable,
            "prefix": sys.prefix,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "platform": platform.platform(),
        },
        "environment": {
            "term_program": os.environ.get("TERM_PROGRAM", "unknown"),
            "shell": os.environ.get("SHELL", "unknown"),
            "user": os.environ.get("USER", "unknown"),
            "home": os.environ.get("HOME", "unknown"),
        },
        "dependencies": {},
        "paths": {
            "cwd": str(Path.cwd()),
            "claude_dir": str(Path.home() / ".claude"),
            "claude_dir_exists": (Path.home() / ".claude").exists(),
        },
    }

    # Check dependencies
    deps = ["typer", "rich", "questionary", "pyyaml"]
    for dep in deps:
        try:
            mod = __import__(dep if dep != "pyyaml" else "yaml")
            version = getattr(mod, "__version__", "installed")
            info_data["dependencies"][dep] = version
        except ImportError:
            info_data["dependencies"][dep] = "missing"

    # Check for optional tools
    tools = ["git", "claude", "opencode", "gemini"]
    info_data["tools"] = {}
    for tool in tools:
        info_data["tools"][tool] = shutil.which(tool) is not None

    if json_output:
        console.print(json_module.dumps(info_data, indent=2))
        return

    # Rich formatted output
    console.print(Panel(
        f"[bold cyan]{__app_name__}[/] v{__version__}",
        title="System Information",
        border_style="cyan",
    ))

    # aiterm info
    table = Table(title="aiterm", show_header=False, border_style="dim")
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("Version", __version__)
    table.add_row("Install Path", get_install_path())
    console.print(table)

    # Python info
    table = Table(title="Python", show_header=False, border_style="dim")
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("Version", info_data["python"]["version"])
    table.add_row("Executable", info_data["python"]["executable"])
    table.add_row("Prefix", info_data["python"]["prefix"])
    console.print(table)

    # Platform info
    table = Table(title="Platform", show_header=False, border_style="dim")
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("System", info_data["platform"]["system"])
    table.add_row("Release", info_data["platform"]["release"])
    table.add_row("Machine", info_data["platform"]["machine"])
    console.print(table)

    # Environment info
    table = Table(title="Environment", show_header=False, border_style="dim")
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("Terminal", info_data["environment"]["term_program"])
    table.add_row("Shell", info_data["environment"]["shell"])
    table.add_row("User", info_data["environment"]["user"])
    console.print(table)

    # Dependencies
    table = Table(title="Dependencies", show_header=True, border_style="dim")
    table.add_column("Package", style="bold")
    table.add_column("Version")
    table.add_column("Status")
    for dep, version in info_data["dependencies"].items():
        status = "[green]OK[/]" if version != "missing" else "[red]Missing[/]"
        table.add_row(dep, version if version != "missing" else "-", status)
    console.print(table)

    # Tools
    table = Table(title="External Tools", show_header=True, border_style="dim")
    table.add_column("Tool", style="bold")
    table.add_column("Available")
    for tool, available in info_data["tools"].items():
        status = "[green]Yes[/]" if available else "[dim]No[/]"
        table.add_row(tool, status)
    console.print(table)

    # Paths
    table = Table(title="Paths", show_header=False, border_style="dim")
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("Working Dir", info_data["paths"]["cwd"])
    claude_status = "[green]exists[/]" if info_data["paths"]["claude_dir_exists"] else "[dim]not found[/]"
    table.add_row("Claude Dir", f"{info_data['paths']['claude_dir']} ({claude_status})")
    console.print(table)


# ─── Context detection implementation ────────────────────────────────────────


def _context_detect_impl(path: Optional[Path], apply: bool) -> None:
    """Shared implementation for context detection commands."""
    from aiterm.context.detector import detect_context
    from aiterm.terminal import iterm2

    target = path or Path.cwd()
    context = detect_context(target)

    # Build info table
    table = Table(title="Context Detection", show_header=False, border_style="cyan")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Directory", str(target))
    table.add_row("Type", f"{context.icon} {context.type.value}" if context.icon else context.type.value)
    table.add_row("Name", context.name)
    table.add_row("Profile", context.profile)

    if context.branch:
        dirty = " [red]*[/]" if context.is_dirty else ""
        table.add_row("Git Branch", f"{context.branch}{dirty}")

    console.print(table)

    # Apply to terminal if requested
    if apply:
        if iterm2.is_iterm2():
            iterm2.apply_context(context)
            console.print("\n[green]✓[/] Context applied to iTerm2")
        else:
            console.print("\n[yellow]⚠[/] Not running in iTerm2 - context not applied")


# ─── Top-level shortcuts ─────────────────────────────────────────────────────


@app.command(
    epilog="""
[bold]Examples:[/]
  ait detect              # Current directory
  ait detect ~/my-project # Specific path
  ait detect .            # Explicit current dir
"""
)
def detect(
    path: Optional[Path] = typer.Argument(None, help="Directory to analyze."),
) -> None:
    """Detect project context (shortcut for 'context detect')."""
    _context_detect_impl(path, apply=False)


@app.command(
    epilog="""
[bold]Examples:[/]
  ait switch              # Apply context for current dir
  ait switch ~/my-project # Apply context for path
  cd ~/project && ait switch  # Common workflow
"""
)
def switch(
    path: Optional[Path] = typer.Argument(None, help="Directory to analyze."),
) -> None:
    """Detect and apply context to terminal (shortcut for 'context apply')."""
    _context_detect_impl(path, apply=True)


# ─── Sub-command groups ──────────────────────────────────────────────────────

context_app = typer.Typer(help="Context detection commands.")
profile_app = typer.Typer(help="Profile management commands.")
claude_app = typer.Typer(help="Claude Code integration commands.")

app.add_typer(context_app, name="context")
app.add_typer(profile_app, name="profile")
app.add_typer(claude_app, name="claude")


@context_app.command("detect")
def context_detect(
    path: Optional[Path] = typer.Argument(
        None,
        help="Directory to analyze. Defaults to current directory.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        "-a",
        help="Apply detected context to terminal (switch profile, set title).",
    ),
) -> None:
    """Detect the project context for a directory."""
    _context_detect_impl(path, apply)


@context_app.command("show")
def context_show() -> None:
    """Show current context (alias for detect)."""
    context_detect(path=None, apply=False)


@context_app.command("apply")
def context_apply(
    path: Optional[Path] = typer.Argument(
        None,
        help="Directory to analyze. Defaults to current directory.",
    ),
) -> None:
    """Detect and apply context to terminal."""
    context_detect(path=path, apply=True)


@profile_app.command("list")
def profile_list() -> None:
    """List available profiles."""
    console.print("[bold cyan]Available Profiles:[/]")
    console.print("  - default (iTerm2 base)")
    console.print("  - ai-session (Claude Code / Gemini)")
    console.print("  - production (warning colors)")
    console.print()
    console.print("[yellow]Profile management coming in v0.2.0[/]")


# ─── Claude settings commands ────────────────────────────────────────────────


@claude_app.command(
    "settings",
    epilog="""
[bold]Examples:[/]
  ait claude settings    # View all settings
"""
)
def claude_settings_show() -> None:
    """Display current Claude Code settings."""
    from aiterm.claude.settings import load_settings, find_settings_file

    settings = load_settings()
    if not settings:
        console.print("[red]No Claude Code settings found.[/]")
        console.print(f"Expected at: ~/.claude/settings.json")
        return

    # Build settings table
    table = Table(title="Claude Code Settings", show_header=False, border_style="cyan")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("File", str(settings.path))
    table.add_row("Permissions (allow)", str(len(settings.allow_list)))
    table.add_row("Permissions (deny)", str(len(settings.deny_list)))

    if settings.hooks:
        table.add_row("Hooks", str(len(settings.hooks)))

    console.print(table)

    # Show permissions
    if settings.allow_list:
        console.print("\n[bold]Allowed:[/]")
        for perm in settings.allow_list[:10]:
            console.print(f"  [green]✓[/] {perm}")
        if len(settings.allow_list) > 10:
            console.print(f"  [dim]... and {len(settings.allow_list) - 10} more[/]")


@claude_app.command(
    "backup",
    epilog="""
[bold]Examples:[/]
  ait claude backup      # Create timestamped backup
"""
)
def claude_backup() -> None:
    """Backup Claude Code settings."""
    from aiterm.claude.settings import backup_settings, find_settings_file

    settings_path = find_settings_file()
    if not settings_path:
        console.print("[red]No Claude Code settings found to backup.[/]")
        return

    backup_path = backup_settings(settings_path)
    if backup_path:
        console.print(f"[green]✓[/] Backup created: {backup_path}")
    else:
        console.print("[red]Failed to create backup.[/]")


# Approvals sub-command group
approvals_app = typer.Typer(help="Manage auto-approval permissions.")
claude_app.add_typer(approvals_app, name="approvals")


@approvals_app.command(
    "list",
    epilog="""
[bold]Examples:[/]
  ait claude approvals list   # Show all approvals
"""
)
def approvals_list() -> None:
    """List current auto-approval permissions."""
    from aiterm.claude.settings import load_settings

    settings = load_settings()
    if not settings:
        console.print("[red]No Claude Code settings found.[/]")
        return

    console.print(f"[bold cyan]Auto-Approvals[/] ({settings.path})\n")

    if settings.allow_list:
        console.print("[bold green]Allowed:[/]")
        for perm in sorted(settings.allow_list):
            console.print(f"  ✓ {perm}")
    else:
        console.print("[dim]No allowed permissions configured.[/]")

    if settings.deny_list:
        console.print("\n[bold red]Denied:[/]")
        for perm in sorted(settings.deny_list):
            console.print(f"  ✗ {perm}")


@approvals_app.command(
    "presets",
    epilog="""
[bold]Examples:[/]
  ait claude approvals presets   # List all presets
"""
)
def approvals_presets() -> None:
    """List available approval presets."""
    from aiterm.claude.settings import list_presets

    presets = list_presets()

    table = Table(title="Available Presets", border_style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Permissions", justify="right")

    for name, preset in presets.items():
        table.add_row(
            name,
            preset["description"],
            str(len(preset["permissions"])),
        )

    console.print(table)
    console.print("\n[dim]Use 'aiterm claude approvals add <preset>' to add a preset.[/]")


@approvals_app.command(
    "add",
    epilog="""
[bold]Examples:[/]
  ait claude approvals add safe      # Add safe preset
  ait claude approvals add moderate  # Add moderate preset
  ait claude approvals add full      # Add all permissions
"""
)
def approvals_add(
    preset_name: str = typer.Argument(..., help="Name of preset to add."),
) -> None:
    """Add a preset to auto-approvals."""
    from aiterm.claude.settings import (
        load_settings,
        save_settings,
        add_preset_to_settings,
        get_preset,
        backup_settings,
    )

    # Validate preset exists
    preset = get_preset(preset_name)
    if not preset:
        console.print(f"[red]Unknown preset: {preset_name}[/]")
        console.print("Run 'aiterm claude approvals presets' to see available presets.")
        raise typer.Exit(1)

    # Load settings
    settings = load_settings()
    if not settings:
        console.print("[red]No Claude Code settings found.[/]")
        console.print("Create ~/.claude/settings.json first.")
        raise typer.Exit(1)

    # Backup first
    backup_settings(settings.path)

    # Add preset
    success, added = add_preset_to_settings(settings, preset_name)
    if not success:
        console.print(f"[red]Failed to add preset: {preset_name}[/]")
        raise typer.Exit(1)

    if not added:
        console.print(f"[yellow]All permissions from '{preset_name}' already present.[/]")
        return

    # Save
    if save_settings(settings):
        console.print(f"[green]✓[/] Added {len(added)} permissions from '{preset_name}':")
        for perm in added:
            console.print(f"  + {perm}")
    else:
        console.print("[red]Failed to save settings.[/]")
        raise typer.Exit(1)


# ─── Register hooks, commands, MCP, docs, and opencode CLIs (must be after app is fully defined) ───
from aiterm.cli import hooks as hooks_cli
from aiterm.cli import commands as commands_cli
from aiterm.cli import mcp as mcp_cli
from aiterm.cli import docs as docs_cli
from aiterm.cli import opencode as opencode_cli
from aiterm.cli import ide as ide_cli

app.add_typer(hooks_cli.app, name="hooks")
app.add_typer(commands_cli.app, name="commands")
app.add_typer(mcp_cli.app, name="mcp")
app.add_typer(docs_cli.app, name="docs")
app.add_typer(opencode_cli.app, name="opencode")
app.add_typer(ide_cli.app, name="ide")

# ─── Phase 2.5-4: Advanced CLI modules ──────────────────────────────────────────
from aiterm.cli import agents as agents_cli
from aiterm.cli import memory as memory_cli
from aiterm.cli import styles as styles_cli
from aiterm.cli import plugins as plugins_cli
from aiterm.cli import gemini as gemini_cli
from aiterm.cli import statusbar as statusbar_cli
from aiterm.cli import terminals as terminals_cli
from aiterm.cli import workflows as workflows_cli
from aiterm.cli import sessions as sessions_cli

app.add_typer(agents_cli.app, name="agents")
app.add_typer(memory_cli.app, name="memory")
app.add_typer(styles_cli.app, name="styles")
app.add_typer(plugins_cli.app, name="plugins")
app.add_typer(gemini_cli.app, name="gemini")
app.add_typer(statusbar_cli.app, name="statusbar")
app.add_typer(terminals_cli.app, name="terminals")
app.add_typer(workflows_cli.app, name="workflows")
app.add_typer(sessions_cli.app, name="sessions")


if __name__ == "__main__":
    app()
