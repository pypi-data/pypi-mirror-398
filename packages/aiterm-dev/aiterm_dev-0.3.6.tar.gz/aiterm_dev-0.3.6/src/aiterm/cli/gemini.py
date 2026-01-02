"""Gemini CLI integration management.

Phase 3.1: Manage Gemini CLI configuration and workflows.
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
    help="Manage Gemini CLI integration.",
    no_args_is_help=True,
)
console = Console()


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class GeminiConfig:
    """Represents Gemini CLI configuration."""

    model: str = "gemini-2.0-flash"
    sandbox: bool = True
    auto_run_tools: bool = False
    theme: str = "default"
    yolo: bool = False
    check_in_interval: int = 0
    max_tokens: int = 0
    custom_instructions: str = ""
    allowed_dirs: list[str] = field(default_factory=list)
    mcp_servers: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {}
        if self.model != "gemini-2.0-flash":
            result["model"] = self.model
        if not self.sandbox:
            result["sandbox"] = self.sandbox
        if self.auto_run_tools:
            result["autoRunTools"] = self.auto_run_tools
        if self.theme != "default":
            result["theme"] = self.theme
        if self.yolo:
            result["yolo"] = self.yolo
        if self.check_in_interval > 0:
            result["checkInInterval"] = self.check_in_interval
        if self.max_tokens > 0:
            result["maxTokens"] = self.max_tokens
        if self.custom_instructions:
            result["customInstructions"] = self.custom_instructions
        if self.allowed_dirs:
            result["allowedDirs"] = self.allowed_dirs
        if self.mcp_servers:
            result["mcpServers"] = self.mcp_servers
        return result


# Available models
GEMINI_MODELS = {
    "gemini-2.0-flash": "Fast, efficient model (default)",
    "gemini-2.0-flash-exp": "Experimental flash model",
    "gemini-1.5-pro": "Most capable model",
    "gemini-1.5-flash": "Fast 1.5 model",
}

# Theme options
GEMINI_THEMES = {
    "default": "Standard dark theme",
    "light": "Light theme",
    "dark": "Dark theme",
    "solarized": "Solarized color scheme",
}


def get_gemini_config_path() -> Path:
    """Get the Gemini CLI config path."""
    # Check for GEMINI_CONFIG_DIR env var
    config_dir = os.environ.get("GEMINI_CONFIG_DIR")
    if config_dir:
        return Path(config_dir) / "settings.json"
    return Path.home() / ".gemini" / "settings.json"


def load_gemini_config() -> GeminiConfig:
    """Load Gemini CLI configuration."""
    config_path = get_gemini_config_path()
    if not config_path.exists():
        return GeminiConfig()

    try:
        data = json.loads(config_path.read_text())
        return GeminiConfig(
            model=data.get("model", "gemini-2.0-flash"),
            sandbox=data.get("sandbox", True),
            auto_run_tools=data.get("autoRunTools", False),
            theme=data.get("theme", "default"),
            yolo=data.get("yolo", False),
            check_in_interval=data.get("checkInInterval", 0),
            max_tokens=data.get("maxTokens", 0),
            custom_instructions=data.get("customInstructions", ""),
            allowed_dirs=data.get("allowedDirs", []),
            mcp_servers=data.get("mcpServers", {}),
        )
    except (json.JSONDecodeError, OSError):
        return GeminiConfig()


def save_gemini_config(config: GeminiConfig) -> bool:
    """Save Gemini CLI configuration."""
    config_path = get_gemini_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load existing to preserve unknown fields
        existing = {}
        if config_path.exists():
            existing = json.loads(config_path.read_text())

        # Update with our config
        existing.update(config.to_dict())
        config_path.write_text(json.dumps(existing, indent=2))
        return True
    except OSError:
        return False


def is_gemini_installed() -> bool:
    """Check if Gemini CLI is installed."""
    import shutil
    return shutil.which("gemini") is not None


# =============================================================================
# CLI Commands
# =============================================================================


@app.command("status")
def gemini_status() -> None:
    """Show Gemini CLI status and configuration."""
    console.print("[bold cyan]Gemini CLI Status[/]\n")

    # Check installation
    if is_gemini_installed():
        console.print("[green]✓[/] Gemini CLI installed")
    else:
        console.print("[red]✗[/] Gemini CLI not found")
        console.print("\n[dim]Install: npm install -g @anthropic-ai/gemini-cli[/]")
        return

    # Load config
    config = load_gemini_config()
    config_path = get_gemini_config_path()

    console.print(f"[green]✓[/] Config: {config_path}")
    if config_path.exists():
        console.print(f"[green]✓[/] Model: {config.model}")
    else:
        console.print("[yellow]⚠[/] No config file (using defaults)")

    # Show key settings
    console.print(f"\n[bold]Settings:[/]")
    console.print(f"  Sandbox: {'enabled' if config.sandbox else 'disabled'}")
    console.print(f"  Auto-run tools: {'yes' if config.auto_run_tools else 'no'}")
    console.print(f"  YOLO mode: {'enabled' if config.yolo else 'disabled'}")
    console.print(f"  Theme: {config.theme}")

    if config.mcp_servers:
        console.print(f"  MCP servers: {len(config.mcp_servers)}")


@app.command("settings")
def gemini_settings() -> None:
    """Show Gemini CLI settings."""
    config = load_gemini_config()
    config_path = get_gemini_config_path()

    if not config_path.exists():
        console.print("[yellow]No Gemini config found.[/]")
        console.print(f"Expected at: {config_path}")
        console.print("\nUse 'ait gemini init' to create one.")
        return

    content = []
    content.append(f"[bold]Model:[/] {config.model}")
    content.append(f"[bold]Sandbox:[/] {'enabled' if config.sandbox else 'disabled'}")
    content.append(f"[bold]Auto-run tools:[/] {'yes' if config.auto_run_tools else 'no'}")
    content.append(f"[bold]YOLO mode:[/] {'enabled' if config.yolo else 'disabled'}")
    content.append(f"[bold]Theme:[/] {config.theme}")

    if config.check_in_interval > 0:
        content.append(f"[bold]Check-in interval:[/] {config.check_in_interval}s")
    if config.max_tokens > 0:
        content.append(f"[bold]Max tokens:[/] {config.max_tokens}")
    if config.custom_instructions:
        content.append(f"[bold]Custom instructions:[/] {len(config.custom_instructions)} chars")
    if config.allowed_dirs:
        content.append(f"[bold]Allowed dirs:[/] {len(config.allowed_dirs)}")
    if config.mcp_servers:
        content.append(f"[bold]MCP servers:[/] {', '.join(config.mcp_servers.keys())}")

    content.append(f"\n[dim]File: {config_path}[/]")

    console.print(Panel(
        "\n".join(content),
        title="Gemini CLI Settings",
        border_style="cyan",
    ))


@app.command("init")
def gemini_init(
    model: str = typer.Option("gemini-2.0-flash", "--model", "-m", help="Default model."),
    yolo: bool = typer.Option(False, "--yolo", help="Enable YOLO mode (auto-approve all)."),
) -> None:
    """Initialize Gemini CLI configuration."""
    config_path = get_gemini_config_path()

    if config_path.exists():
        console.print(f"[yellow]Config already exists at {config_path}[/]")
        console.print("Use 'ait gemini set' to modify settings.")
        return

    config = GeminiConfig(
        model=model,
        yolo=yolo,
    )

    if save_gemini_config(config):
        console.print(f"[green]Created Gemini config at {config_path}[/]")
        console.print(f"  Model: {model}")
        if yolo:
            console.print("  [yellow]YOLO mode enabled - all tools auto-approved![/]")
    else:
        console.print("[red]Failed to create config.[/]")
        raise typer.Exit(1)


@app.command("models")
def gemini_models() -> None:
    """List available Gemini models."""
    config = load_gemini_config()

    table = Table(title="Gemini Models", border_style="cyan")
    table.add_column("Model", style="bold")
    table.add_column("Description")
    table.add_column("Active", justify="center")

    for model_id, description in GEMINI_MODELS.items():
        is_active = "●" if model_id == config.model else ""
        table.add_row(
            model_id,
            description,
            f"[green]{is_active}[/]" if is_active else "",
        )

    console.print(table)
    console.print(f"\n[dim]Current model: {config.model}[/]")


@app.command("set")
def gemini_set(
    model: str = typer.Option(None, "--model", "-m", help="Set default model."),
    sandbox: bool = typer.Option(None, "--sandbox/--no-sandbox", help="Enable/disable sandbox."),
    yolo: bool = typer.Option(None, "--yolo/--no-yolo", help="Enable/disable YOLO mode."),
    theme: str = typer.Option(None, "--theme", "-t", help="Set theme."),
) -> None:
    """Update Gemini CLI settings."""
    config = load_gemini_config()
    changes = []

    if model is not None:
        if model not in GEMINI_MODELS:
            console.print(f"[yellow]Warning: '{model}' is not a known model[/]")
        config.model = model
        changes.append(f"model → {model}")

    if sandbox is not None:
        config.sandbox = sandbox
        changes.append(f"sandbox → {'enabled' if sandbox else 'disabled'}")

    if yolo is not None:
        config.yolo = yolo
        changes.append(f"yolo → {'enabled' if yolo else 'disabled'}")

    if theme is not None:
        if theme not in GEMINI_THEMES:
            console.print(f"[yellow]Warning: '{theme}' is not a known theme[/]")
        config.theme = theme
        changes.append(f"theme → {theme}")

    if not changes:
        console.print("[yellow]No changes specified.[/]")
        console.print("Use --model, --sandbox, --yolo, or --theme to update settings.")
        return

    if save_gemini_config(config):
        console.print("[green]Updated settings:[/]")
        for change in changes:
            console.print(f"  {change}")
    else:
        console.print("[red]Failed to save settings.[/]")
        raise typer.Exit(1)


@app.command("mcp")
def gemini_mcp() -> None:
    """Show MCP servers configured for Gemini."""
    config = load_gemini_config()

    if not config.mcp_servers:
        console.print("[yellow]No MCP servers configured for Gemini.[/]")
        console.print("\nAdd servers to ~/.gemini/settings.json under 'mcpServers'")
        return

    table = Table(title="Gemini MCP Servers", border_style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Command/URL")
    table.add_column("Type")

    for name, server in config.mcp_servers.items():
        if isinstance(server, dict):
            cmd = server.get("command", server.get("url", "unknown"))
            server_type = "stdio" if "command" in server else "sse"
        else:
            cmd = str(server)
            server_type = "unknown"

        table.add_row(name, str(cmd)[:50], server_type)

    console.print(table)


@app.command("compare")
def gemini_compare() -> None:
    """Compare Gemini and Claude Code configurations."""
    from aiterm.cli.claude import get_settings_path, load_settings

    console.print("[bold cyan]Configuration Comparison[/]\n")

    # Gemini
    gemini_config = load_gemini_config()
    gemini_path = get_gemini_config_path()

    # Claude
    claude_settings = load_settings()
    claude_path = get_settings_path()

    table = Table(border_style="dim")
    table.add_column("Setting", style="bold")
    table.add_column("Gemini CLI")
    table.add_column("Claude Code")

    # Compare key settings
    table.add_row(
        "Config path",
        str(gemini_path) if gemini_path.exists() else "[dim]not found[/]",
        str(claude_path) if claude_path.exists() else "[dim]not found[/]",
    )
    table.add_row(
        "Model",
        gemini_config.model,
        claude_settings.get("model", "default"),
    )
    table.add_row(
        "Auto-approve",
        "YOLO" if gemini_config.yolo else "manual",
        f"{len(claude_settings.get('permissions', {}).get('allow', []))} rules",
    )
    table.add_row(
        "MCP servers",
        str(len(gemini_config.mcp_servers)),
        str(len(claude_settings.get("mcpServers", {}))),
    )

    console.print(table)


@app.command("sync-mcp")
def gemini_sync_mcp(
    from_claude: bool = typer.Option(False, "--from-claude", help="Copy MCP servers from Claude Code."),
) -> None:
    """Sync MCP servers between Gemini and Claude Code."""
    if not from_claude:
        console.print("[yellow]Specify --from-claude to sync MCP servers.[/]")
        console.print("\nThis will copy MCP server configs from Claude Code to Gemini.")
        return

    from aiterm.cli.claude import load_settings

    claude_settings = load_settings()
    claude_mcp = claude_settings.get("mcpServers", {})

    if not claude_mcp:
        console.print("[yellow]No MCP servers found in Claude Code settings.[/]")
        return

    gemini_config = load_gemini_config()
    original_count = len(gemini_config.mcp_servers)
    gemini_config.mcp_servers.update(claude_mcp)
    new_count = len(gemini_config.mcp_servers)

    if save_gemini_config(gemini_config):
        added = new_count - original_count
        console.print(f"[green]Synced MCP servers from Claude Code.[/]")
        console.print(f"  Added: {added} servers")
        console.print(f"  Total: {new_count} servers")
    else:
        console.print("[red]Failed to save config.[/]")
        raise typer.Exit(1)
