"""Plugin management CLI for Claude Code.

Phase 2.5.4: Manage Claude Code plugins (bundles of commands, agents, skills, hooks).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

app = typer.Typer(
    help="Manage Claude Code plugins.",
    no_args_is_help=True,
)
console = Console()


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class Plugin:
    """Represents a Claude Code plugin."""

    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    commands: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)
    mcp_servers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "name": self.name,
            "version": self.version,
        }
        if self.description:
            result["description"] = self.description
        if self.author:
            result["author"] = self.author
        if self.commands:
            result["commands"] = self.commands
        if self.agents:
            result["agents"] = self.agents
        if self.skills:
            result["skills"] = self.skills
        if self.hooks:
            result["hooks"] = self.hooks
        if self.mcp_servers:
            result["mcp_servers"] = self.mcp_servers
        return result

    @property
    def component_count(self) -> int:
        """Total number of components in the plugin."""
        return (
            len(self.commands)
            + len(self.agents)
            + len(self.skills)
            + len(self.hooks)
            + len(self.mcp_servers)
        )


def get_plugins_dir() -> Path:
    """Get the plugins directory."""
    return Path.home() / ".claude" / "plugins"


def load_plugin(name: str) -> Plugin | None:
    """Load a plugin configuration."""
    plugins_dir = get_plugins_dir()
    plugin_dir = plugins_dir / name

    plugin_file = plugin_dir / "plugin.json"
    if not plugin_file.exists():
        return None

    try:
        data = json.loads(plugin_file.read_text())
        return Plugin(
            name=data.get("name", name),
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            commands=data.get("commands", []),
            agents=data.get("agents", []),
            skills=data.get("skills", []),
            hooks=data.get("hooks", []),
            mcp_servers=data.get("mcp_servers", []),
        )
    except (json.JSONDecodeError, OSError):
        return None


def save_plugin(plugin: Plugin) -> bool:
    """Save a plugin configuration."""
    plugins_dir = get_plugins_dir()
    plugin_dir = plugins_dir / plugin.name
    plugin_dir.mkdir(parents=True, exist_ok=True)

    plugin_file = plugin_dir / "plugin.json"
    try:
        plugin_file.write_text(json.dumps(plugin.to_dict(), indent=2))
        return True
    except OSError:
        return False


def list_plugins() -> list[Plugin]:
    """List all installed plugins."""
    plugins_dir = get_plugins_dir()
    if not plugins_dir.exists():
        return []

    plugins = []
    for plugin_dir in plugins_dir.iterdir():
        if plugin_dir.is_dir():
            plugin = load_plugin(plugin_dir.name)
            if plugin:
                plugins.append(plugin)

    return sorted(plugins, key=lambda p: p.name)


# =============================================================================
# CLI Commands
# =============================================================================


@app.command("list")
def plugins_list() -> None:
    """List installed plugins."""
    plugins = list_plugins()

    if not plugins:
        console.print("[yellow]No plugins installed.[/]")
        console.print("\nUse 'ait plugins create <name>' to create one.")
        return

    table = Table(title="Installed Plugins", border_style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Version")
    table.add_column("Components", justify="right")
    table.add_column("Description")

    for plugin in plugins:
        table.add_row(
            plugin.name,
            plugin.version,
            str(plugin.component_count),
            plugin.description[:40] + "..." if len(plugin.description) > 40 else plugin.description,
        )

    console.print(table)


@app.command("show")
def plugins_show(
    name: str = typer.Argument(..., help="Plugin name to show."),
) -> None:
    """Show detailed plugin information."""
    plugin = load_plugin(name)
    if not plugin:
        console.print(f"[red]Plugin '{name}' not found.[/]")
        raise typer.Exit(1)

    # Build tree of components
    tree = Tree(f"[bold cyan]{plugin.name}[/] v{plugin.version}")

    if plugin.description:
        tree.add(f"[dim]{plugin.description}[/]")

    if plugin.commands:
        cmd_branch = tree.add("[bold]Commands[/]")
        for cmd in plugin.commands:
            cmd_branch.add(f"/{cmd}")

    if plugin.agents:
        agent_branch = tree.add("[bold]Agents[/]")
        for agent in plugin.agents:
            agent_branch.add(agent)

    if plugin.skills:
        skill_branch = tree.add("[bold]Skills[/]")
        for skill in plugin.skills:
            skill_branch.add(skill)

    if plugin.hooks:
        hook_branch = tree.add("[bold]Hooks[/]")
        for hook in plugin.hooks:
            hook_branch.add(hook)

    if plugin.mcp_servers:
        mcp_branch = tree.add("[bold]MCP Servers[/]")
        for server in plugin.mcp_servers:
            mcp_branch.add(server)

    console.print(tree)
    console.print(f"\n[dim]Location: {get_plugins_dir() / name}[/]")


@app.command("create")
def plugins_create(
    name: str = typer.Argument(..., help="Plugin name."),
    description: str = typer.Option("", "--desc", "-d", help="Plugin description."),
    author: str = typer.Option("", "--author", "-a", help="Plugin author."),
) -> None:
    """Create a new plugin."""
    plugins_dir = get_plugins_dir()
    plugin_dir = plugins_dir / name

    if plugin_dir.exists():
        console.print(f"[yellow]Plugin '{name}' already exists.[/]")
        return

    # Create plugin structure
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "commands").mkdir()
    (plugin_dir / "agents").mkdir()
    (plugin_dir / "skills").mkdir()
    (plugin_dir / "hooks").mkdir()

    # Create plugin.json
    plugin = Plugin(
        name=name,
        description=description,
        author=author,
    )
    save_plugin(plugin)

    # Create README
    readme = f"""# {name}

{description or 'A Claude Code plugin.'}

## Installation

This plugin is installed at `~/.claude/plugins/{name}/`

## Components

Add your components to the appropriate directories:
- `commands/` - Slash commands
- `agents/` - Subagent configurations
- `skills/` - Skills (SKILL.md files)
- `hooks/` - Hook scripts

## Usage

After adding components, update `plugin.json` to register them.
"""
    (plugin_dir / "README.md").write_text(readme)

    console.print(f"[green]Created plugin '{name}'[/]")
    console.print(f"  Location: {plugin_dir}")
    console.print("\n[dim]Add components to the subdirectories, then update plugin.json[/]")


@app.command("validate")
def plugins_validate(
    name: str = typer.Argument(None, help="Plugin to validate (or all if not specified)."),
) -> None:
    """Validate plugin configurations."""
    if name:
        plugins = [load_plugin(name)]
        if not plugins[0]:
            console.print(f"[red]Plugin '{name}' not found.[/]")
            raise typer.Exit(1)
    else:
        plugins = list_plugins()

    if not plugins:
        console.print("[yellow]No plugins to validate.[/]")
        return

    all_valid = True
    for plugin in plugins:
        if not plugin:
            continue

        issues = []
        plugin_dir = get_plugins_dir() / plugin.name

        # Check commands exist
        for cmd in plugin.commands:
            cmd_file = plugin_dir / "commands" / f"{cmd}.md"
            if not cmd_file.exists():
                issues.append(f"Command not found: {cmd}")

        # Check agents exist
        for agent in plugin.agents:
            agent_file = plugin_dir / "agents" / f"{agent}.json"
            if not agent_file.exists():
                issues.append(f"Agent not found: {agent}")

        # Check skills exist
        for skill in plugin.skills:
            skill_file = plugin_dir / "skills" / f"{skill}.md"
            if not skill_file.exists():
                issues.append(f"Skill not found: {skill}")

        # Check hooks exist
        for hook in plugin.hooks:
            hook_file = plugin_dir / "hooks" / f"{hook}.sh"
            if not hook_file.exists():
                hook_file = plugin_dir / "hooks" / f"{hook}.py"
                if not hook_file.exists():
                    issues.append(f"Hook not found: {hook}")

        if issues:
            all_valid = False
            console.print(f"[red]✗[/] {plugin.name}:")
            for issue in issues:
                console.print(f"    {issue}")
        else:
            console.print(f"[green]✓[/] {plugin.name}: Valid ({plugin.component_count} components)")

    if not all_valid:
        raise typer.Exit(1)


@app.command("remove")
def plugins_remove(
    name: str = typer.Argument(..., help="Plugin to remove."),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation."),
) -> None:
    """Remove a plugin."""
    plugin_dir = get_plugins_dir() / name
    if not plugin_dir.exists():
        console.print(f"[red]Plugin '{name}' not found.[/]")
        raise typer.Exit(1)

    plugin = load_plugin(name)
    if plugin and not force:
        console.print(f"[yellow]This will remove plugin '{name}' with {plugin.component_count} components.[/]")
        console.print("Use --force to skip this confirmation.")
        return

    import shutil
    try:
        shutil.rmtree(plugin_dir)
        console.print(f"[green]Removed plugin '{name}'[/]")
    except OSError as e:
        console.print(f"[red]Failed to remove plugin: {e}[/]")
        raise typer.Exit(1)


@app.command("package")
def plugins_package(
    name: str = typer.Argument(..., help="Plugin to package."),
    output: Path = typer.Option(None, "--output", "-o", help="Output directory."),
) -> None:
    """Package a plugin for distribution."""
    plugin = load_plugin(name)
    if not plugin:
        console.print(f"[red]Plugin '{name}' not found.[/]")
        raise typer.Exit(1)

    plugin_dir = get_plugins_dir() / name
    output_dir = output or Path.cwd()
    output_file = output_dir / f"{name}-{plugin.version}.tar.gz"

    import tarfile
    try:
        with tarfile.open(output_file, "w:gz") as tar:
            tar.add(plugin_dir, arcname=name)
        console.print(f"[green]Packaged plugin to:[/] {output_file}")
    except OSError as e:
        console.print(f"[red]Failed to package: {e}[/]")
        raise typer.Exit(1)


@app.command("import")
def plugins_import(
    file: Path = typer.Argument(..., help="Plugin package to import."),
) -> None:
    """Import a plugin from a package."""
    if not file.exists():
        console.print(f"[red]File not found: {file}[/]")
        raise typer.Exit(1)

    import tarfile
    try:
        with tarfile.open(file, "r:gz") as tar:
            # Get plugin name from archive
            names = tar.getnames()
            if not names:
                console.print("[red]Empty archive.[/]")
                raise typer.Exit(1)

            plugin_name = names[0].split("/")[0]
            plugins_dir = get_plugins_dir()

            if (plugins_dir / plugin_name).exists():
                console.print(f"[yellow]Plugin '{plugin_name}' already exists.[/]")
                console.print("Remove it first or use a different name.")
                raise typer.Exit(1)

            tar.extractall(plugins_dir)
            console.print(f"[green]Imported plugin '{plugin_name}'[/]")
    except tarfile.TarError as e:
        console.print(f"[red]Failed to import: {e}[/]")
        raise typer.Exit(1)
