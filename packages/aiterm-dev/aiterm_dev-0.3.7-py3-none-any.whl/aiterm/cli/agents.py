"""Subagent management CLI for Claude Code.

Phase 2.5.1: Manage Claude Code subagents - create, test, validate.
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

app = typer.Typer(
    help="Manage Claude Code subagents.",
    no_args_is_help=True,
)
console = Console()


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class SubagentConfig:
    """Represents a Claude Code subagent configuration."""

    name: str
    description: str = ""
    model: str = ""
    tools: list[str] = field(default_factory=list)
    prompt: str = ""
    color: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {}
        if self.description:
            result["description"] = self.description
        if self.model:
            result["model"] = self.model
        if self.tools:
            result["tools"] = self.tools
        if self.prompt:
            result["prompt"] = self.prompt
        if self.color:
            result["color"] = self.color
        return result

    def is_valid(self) -> tuple[bool, list[str]]:
        """Validate the subagent configuration."""
        errors = []
        if not self.name:
            errors.append("Agent name is required")
        if self.model and "/" not in self.model:
            errors.append(f"Model should be in format 'provider/model': {self.model}")
        return len(errors) == 0, errors


# Default subagent templates
SUBAGENT_TEMPLATES = {
    "research": {
        "description": "Research and analysis agent with web access",
        "model": "anthropic/claude-sonnet-4-5",
        "tools": ["Read", "WebFetch", "WebSearch", "Grep", "Glob"],
        "prompt": "Focus on thorough research and analysis. Cite sources when possible.",
    },
    "coding": {
        "description": "Full-featured coding agent with all tools",
        "model": "anthropic/claude-sonnet-4-5",
        "tools": ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
        "prompt": "Focus on clean, well-tested code. Follow project conventions.",
    },
    "review": {
        "description": "Code review agent (read-only)",
        "model": "anthropic/claude-sonnet-4-5",
        "tools": ["Read", "Grep", "Glob"],
        "prompt": "Review code for bugs, security issues, and best practices.",
    },
    "quick": {
        "description": "Fast responses for simple questions",
        "model": "anthropic/claude-haiku-4-5",
        "tools": ["Read", "Grep", "Glob"],
        "prompt": "Provide concise, direct answers.",
    },
    "statistical": {
        "description": "Statistical analysis and R development",
        "model": "anthropic/claude-sonnet-4-5",
        "tools": ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
        "prompt": "Focus on statistical methods, R code, and data analysis.",
    },
}


def get_agents_dir() -> Path:
    """Get the Claude Code agents directory."""
    return Path.home() / ".claude" / "agents"


def load_agent(name: str) -> SubagentConfig | None:
    """Load a subagent configuration."""
    agents_dir = get_agents_dir()
    agent_file = agents_dir / f"{name}.json"

    if not agent_file.exists():
        return None

    try:
        data = json.loads(agent_file.read_text())
        return SubagentConfig(
            name=name,
            description=data.get("description", ""),
            model=data.get("model", ""),
            tools=data.get("tools", []),
            prompt=data.get("prompt", ""),
            color=data.get("color", ""),
        )
    except (json.JSONDecodeError, OSError):
        return None


def save_agent(agent: SubagentConfig) -> bool:
    """Save a subagent configuration."""
    agents_dir = get_agents_dir()
    agents_dir.mkdir(parents=True, exist_ok=True)

    agent_file = agents_dir / f"{agent.name}.json"
    try:
        agent_file.write_text(json.dumps(agent.to_dict(), indent=2))
        return True
    except OSError:
        return False


def list_agents() -> list[SubagentConfig]:
    """List all configured subagents."""
    agents_dir = get_agents_dir()
    if not agents_dir.exists():
        return []

    agents = []
    for agent_file in agents_dir.glob("*.json"):
        agent = load_agent(agent_file.stem)
        if agent:
            agents.append(agent)

    return sorted(agents, key=lambda a: a.name)


# =============================================================================
# CLI Commands
# =============================================================================


@app.command("list")
def agents_list() -> None:
    """List configured subagents."""
    agents = list_agents()

    if not agents:
        console.print("[yellow]No subagents configured.[/]")
        console.print("\nUse 'ait agents create <name>' to create one.")
        console.print("Or 'ait agents templates' to see available templates.")
        return

    table = Table(title="Configured Subagents", border_style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Model")
    table.add_column("Tools", justify="right")
    table.add_column("Description")

    for agent in agents:
        model_display = agent.model.split("/")[-1] if agent.model else "default"
        table.add_row(
            agent.name,
            model_display,
            str(len(agent.tools)),
            agent.description[:40] + "..." if len(agent.description) > 40 else agent.description,
        )

    console.print(table)


@app.command("templates")
def agents_templates() -> None:
    """List available subagent templates."""
    table = Table(title="Subagent Templates", border_style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Model")
    table.add_column("Tools", justify="right")
    table.add_column("Description")

    for name, template in SUBAGENT_TEMPLATES.items():
        model_display = template["model"].split("/")[-1]
        table.add_row(
            name,
            model_display,
            str(len(template["tools"])),
            template["description"],
        )

    console.print(table)
    console.print("\n[dim]Use 'ait agents create <name> --template <template>' to create from template.[/]")


@app.command("create")
def agents_create(
    name: str = typer.Argument(..., help="Name for the new subagent."),
    template: str = typer.Option(None, "--template", "-t", help="Template to use."),
    description: str = typer.Option("", "--desc", "-d", help="Agent description."),
    model: str = typer.Option("", "--model", "-m", help="Model to use (e.g., anthropic/claude-sonnet-4-5)."),
) -> None:
    """Create a new subagent configuration."""
    # Check if already exists
    existing = load_agent(name)
    if existing:
        console.print(f"[red]Agent '{name}' already exists.[/]")
        console.print("Use 'ait agents remove' first, or choose a different name.")
        raise typer.Exit(1)

    # Start from template or blank
    if template:
        if template not in SUBAGENT_TEMPLATES:
            console.print(f"[red]Unknown template: {template}[/]")
            console.print("Use 'ait agents templates' to see available templates.")
            raise typer.Exit(1)

        tmpl = SUBAGENT_TEMPLATES[template]
        agent = SubagentConfig(
            name=name,
            description=description or tmpl["description"],
            model=model or tmpl["model"],
            tools=tmpl["tools"],
            prompt=tmpl.get("prompt", ""),
        )
    else:
        agent = SubagentConfig(
            name=name,
            description=description,
            model=model,
        )

    # Validate
    valid, errors = agent.is_valid()
    if not valid:
        for err in errors:
            console.print(f"[red]Error:[/] {err}")
        raise typer.Exit(1)

    # Save
    if save_agent(agent):
        console.print(f"[green]Created agent '{name}'[/]")
        console.print(f"  Location: {get_agents_dir() / f'{name}.json'}")
        if agent.model:
            console.print(f"  Model: {agent.model}")
        if agent.tools:
            console.print(f"  Tools: {', '.join(agent.tools)}")
    else:
        console.print("[red]Failed to save agent configuration.[/]")
        raise typer.Exit(1)


@app.command("show")
def agents_show(
    name: str = typer.Argument(..., help="Name of agent to show."),
) -> None:
    """Show detailed agent configuration."""
    agent = load_agent(name)
    if not agent:
        console.print(f"[red]Agent '{name}' not found.[/]")
        raise typer.Exit(1)

    panel_content = []
    if agent.description:
        panel_content.append(f"[bold]Description:[/] {agent.description}")
    if agent.model:
        panel_content.append(f"[bold]Model:[/] {agent.model}")
    if agent.tools:
        panel_content.append(f"[bold]Tools:[/] {', '.join(agent.tools)}")
    if agent.prompt:
        panel_content.append(f"[bold]Prompt:[/] {agent.prompt}")
    if agent.color:
        panel_content.append(f"[bold]Color:[/] {agent.color}")

    panel_content.append(f"\n[dim]File: {get_agents_dir() / f'{name}.json'}[/]")

    console.print(Panel(
        "\n".join(panel_content),
        title=f"Agent: {name}",
        border_style="cyan",
    ))


@app.command("remove")
def agents_remove(
    name: str = typer.Argument(..., help="Name of agent to remove."),
) -> None:
    """Remove a subagent configuration."""
    agent_file = get_agents_dir() / f"{name}.json"
    if not agent_file.exists():
        console.print(f"[red]Agent '{name}' not found.[/]")
        raise typer.Exit(1)

    try:
        agent_file.unlink()
        console.print(f"[green]Removed agent '{name}'[/]")
    except OSError as e:
        console.print(f"[red]Failed to remove agent: {e}[/]")
        raise typer.Exit(1)


@app.command("validate")
def agents_validate(
    name: str = typer.Argument(None, help="Agent to validate (or all if not specified)."),
) -> None:
    """Validate subagent configurations."""
    if name:
        agents = [load_agent(name)]
        if not agents[0]:
            console.print(f"[red]Agent '{name}' not found.[/]")
            raise typer.Exit(1)
    else:
        agents = list_agents()

    if not agents:
        console.print("[yellow]No agents to validate.[/]")
        return

    all_valid = True
    for agent in agents:
        if not agent:
            continue
        valid, errors = agent.is_valid()
        if valid:
            console.print(f"[green]✓[/] {agent.name}: Valid")
        else:
            all_valid = False
            console.print(f"[red]✗[/] {agent.name}: Invalid")
            for err in errors:
                console.print(f"    {err}")

    if all_valid:
        console.print(f"\n[green]All {len(agents)} agent(s) valid.[/]")
    else:
        raise typer.Exit(1)


@app.command("test")
def agents_test(
    name: str = typer.Argument(..., help="Agent to test."),
) -> None:
    """Test a subagent configuration (dry run)."""
    agent = load_agent(name)
    if not agent:
        console.print(f"[red]Agent '{name}' not found.[/]")
        raise typer.Exit(1)

    console.print(f"[bold cyan]Testing agent: {name}[/]\n")

    # Validate
    valid, errors = agent.is_valid()
    if not valid:
        console.print("[red]✗ Validation failed:[/]")
        for err in errors:
            console.print(f"  {err}")
        raise typer.Exit(1)
    console.print("[green]✓[/] Configuration valid")

    # Check model availability
    if agent.model:
        if "anthropic/" in agent.model:
            console.print(f"[green]✓[/] Model '{agent.model}' recognized")
        else:
            console.print(f"[yellow]⚠[/] Model '{agent.model}' not a known Anthropic model")

    # Check tools
    known_tools = {"Read", "Write", "Edit", "Bash", "Grep", "Glob", "WebFetch", "WebSearch", "Task"}
    unknown_tools = set(agent.tools) - known_tools
    if unknown_tools:
        console.print(f"[yellow]⚠[/] Unknown tools: {', '.join(unknown_tools)}")
    else:
        console.print(f"[green]✓[/] All {len(agent.tools)} tools recognized")

    console.print(f"\n[green]Agent '{name}' ready for use.[/]")
