"""Workflow templates CLI.

Phase 4.2: Pre-configured workflow templates for different development contexts.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

app = typer.Typer(
    help="Manage workflow templates for different contexts.",
    no_args_is_help=True,
)
console = Console()


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class WorkflowTemplate:
    """Represents a workflow template configuration."""

    name: str
    description: str = ""
    context_type: str = ""  # r, python, node, research, teaching, etc.
    auto_approvals: list[str] = field(default_factory=list)
    claude_commands: list[str] = field(default_factory=list)
    environment_vars: dict[str, str] = field(default_factory=dict)
    shell_aliases: dict[str, str] = field(default_factory=dict)
    status_bar: str = ""
    hooks: list[str] = field(default_factory=list)
    init_commands: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "name": self.name,
        }
        if self.description:
            result["description"] = self.description
        if self.context_type:
            result["context_type"] = self.context_type
        if self.auto_approvals:
            result["auto_approvals"] = self.auto_approvals
        if self.claude_commands:
            result["claude_commands"] = self.claude_commands
        if self.environment_vars:
            result["environment_vars"] = self.environment_vars
        if self.shell_aliases:
            result["shell_aliases"] = self.shell_aliases
        if self.status_bar:
            result["status_bar"] = self.status_bar
        if self.hooks:
            result["hooks"] = self.hooks
        if self.init_commands:
            result["init_commands"] = self.init_commands
        return result


# Built-in workflow templates
WORKFLOW_TEMPLATES = {
    "r-development": WorkflowTemplate(
        name="r-development",
        description="R package development workflow",
        context_type="r",
        auto_approvals=[
            "Bash(Rscript:*)",
            "Bash(R CMD:*)",
            "Bash(R:*)",
            "Bash(devtools::*)",
            "Bash(testthat::*)",
        ],
        claude_commands=["research:sim-design", "math:derive", "research:cite"],
        environment_vars={
            "R_PROFILE_USER": "~/.Rprofile",
            "R_LIBS_USER": "~/R/library",
        },
        shell_aliases={
            "rb": "Rscript -e 'devtools::build()'",
            "rt": "Rscript -e 'devtools::test()'",
            "rc": "Rscript -e 'devtools::check()'",
            "rd": "Rscript -e 'devtools::document()'",
        },
        status_bar="developer",
        init_commands=["Rscript -e 'devtools::load_all()'"],
    ),
    "python-development": WorkflowTemplate(
        name="python-development",
        description="Python package/app development workflow",
        context_type="python",
        auto_approvals=[
            "Bash(python:*)",
            "Bash(python3:*)",
            "Bash(pytest:*)",
            "Bash(pip:*)",
            "Bash(pip3:*)",
            "Bash(uv:*)",
        ],
        environment_vars={
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
        },
        shell_aliases={
            "pt": "pytest",
            "ptv": "pytest -v",
            "ptc": "pytest --cov",
            "pi": "pip install -e .",
        },
        status_bar="developer",
        init_commands=["source .venv/bin/activate 2>/dev/null || true"],
    ),
    "node-development": WorkflowTemplate(
        name="node-development",
        description="Node.js/TypeScript development workflow",
        context_type="node",
        auto_approvals=[
            "Bash(npm:*)",
            "Bash(npx:*)",
            "Bash(bun:*)",
            "Bash(node:*)",
        ],
        shell_aliases={
            "nt": "npm test",
            "nr": "npm run",
            "ni": "npm install",
            "nb": "npm run build",
        },
        status_bar="developer",
    ),
    "research": WorkflowTemplate(
        name="research",
        description="Academic research and writing workflow",
        context_type="research",
        auto_approvals=[
            "Bash(quarto:*)",
            "Bash(Rscript:*)",
            "Bash(pandoc:*)",
            "Bash(bibtex:*)",
        ],
        claude_commands=[
            "research:cite",
            "research:manuscript",
            "write:abstract",
            "write:edit",
        ],
        shell_aliases={
            "qr": "quarto render",
            "qp": "quarto preview",
            "qpdf": "quarto render --to pdf",
        },
        status_bar="stats",
        hooks=["prompt-optimizer"],
    ),
    "teaching": WorkflowTemplate(
        name="teaching",
        description="Course development and teaching workflow",
        context_type="teaching",
        auto_approvals=[
            "Bash(quarto:*)",
            "Bash(Rscript:*)",
        ],
        claude_commands=[
            "teach:exam",
            "teach:homework",
            "teach:rubric",
            "teach:solution",
            "teach:lecture",
        ],
        shell_aliases={
            "tlec": "quarto preview lectures/",
            "tpub": "quarto publish gh-pages",
        },
        status_bar="minimal",
    ),
    "mcp-development": WorkflowTemplate(
        name="mcp-development",
        description="MCP server development workflow",
        context_type="mcp",
        auto_approvals=[
            "Bash(npm:*)",
            "Bash(npx:*)",
            "Bash(node:*)",
        ],
        shell_aliases={
            "mcp-test": "npm run test",
            "mcp-build": "npm run build",
            "mcp-dev": "npm run dev",
        },
        status_bar="developer",
        init_commands=["npm install"],
    ),
    "documentation": WorkflowTemplate(
        name="documentation",
        description="Documentation writing workflow",
        context_type="docs",
        auto_approvals=[
            "Bash(mkdocs:*)",
            "Bash(quarto:*)",
        ],
        claude_commands=[
            "write:draft",
            "write:edit",
        ],
        shell_aliases={
            "docs-serve": "mkdocs serve",
            "docs-build": "mkdocs build",
            "docs-deploy": "mkdocs gh-deploy",
        },
        status_bar="minimal",
    ),
    "adhd-friendly": WorkflowTemplate(
        name="adhd-friendly",
        description="ADHD-optimized workflow with reduced distractions",
        context_type="adhd",
        claude_commands=[
            "workflow",
            "help",
        ],
        shell_aliases={
            "focus": "work",
            "done": "finish",
            "next": "echo 'Check your todo list'",
        },
        status_bar="minimal",
        hooks=["prompt-optimizer"],
    ),
}


def get_workflows_dir() -> Path:
    """Get the workflows directory."""
    return Path.home() / ".claude" / "workflows"


def load_workflow(name: str) -> WorkflowTemplate | None:
    """Load a workflow template."""
    # Check built-ins first
    if name in WORKFLOW_TEMPLATES:
        return WORKFLOW_TEMPLATES[name]

    # Check custom workflows
    workflows_dir = get_workflows_dir()
    workflow_file = workflows_dir / f"{name}.json"

    if not workflow_file.exists():
        return None

    try:
        data = json.loads(workflow_file.read_text())
        return WorkflowTemplate(
            name=data.get("name", name),
            description=data.get("description", ""),
            context_type=data.get("context_type", ""),
            auto_approvals=data.get("auto_approvals", []),
            claude_commands=data.get("claude_commands", []),
            environment_vars=data.get("environment_vars", {}),
            shell_aliases=data.get("shell_aliases", {}),
            status_bar=data.get("status_bar", ""),
            hooks=data.get("hooks", []),
            init_commands=data.get("init_commands", []),
        )
    except (json.JSONDecodeError, OSError):
        return None


def save_workflow(workflow: WorkflowTemplate) -> bool:
    """Save a custom workflow template."""
    workflows_dir = get_workflows_dir()
    workflows_dir.mkdir(parents=True, exist_ok=True)

    workflow_file = workflows_dir / f"{workflow.name}.json"
    try:
        workflow_file.write_text(json.dumps(workflow.to_dict(), indent=2))
        return True
    except OSError:
        return False


def list_all_workflows() -> list[WorkflowTemplate]:
    """List all available workflows (built-in + custom)."""
    workflows = list(WORKFLOW_TEMPLATES.values())

    # Add custom workflows
    workflows_dir = get_workflows_dir()
    if workflows_dir.exists():
        for wf_file in workflows_dir.glob("*.json"):
            if wf_file.stem not in WORKFLOW_TEMPLATES:
                wf = load_workflow(wf_file.stem)
                if wf:
                    workflows.append(wf)

    return sorted(workflows, key=lambda w: w.name)


def get_active_workflow() -> str | None:
    """Get the currently active workflow."""
    state_file = get_workflows_dir() / ".active"
    if state_file.exists():
        return state_file.read_text().strip()
    return None


def set_active_workflow(name: str) -> bool:
    """Set the active workflow."""
    workflows_dir = get_workflows_dir()
    workflows_dir.mkdir(parents=True, exist_ok=True)

    state_file = workflows_dir / ".active"
    try:
        state_file.write_text(name)
        return True
    except OSError:
        return False


# =============================================================================
# CLI Commands
# =============================================================================


@app.command("list")
def workflows_list() -> None:
    """List available workflow templates."""
    workflows = list_all_workflows()
    active = get_active_workflow()

    table = Table(title="Workflow Templates", border_style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Context")
    table.add_column("Auto-approvals", justify="right")
    table.add_column("Description")
    table.add_column("Active", justify="center")

    for wf in workflows:
        is_active = "●" if wf.name == active else ""
        is_builtin = wf.name in WORKFLOW_TEMPLATES
        name_display = wf.name + (" [dim](built-in)[/]" if is_builtin else "")

        table.add_row(
            name_display,
            wf.context_type or "-",
            str(len(wf.auto_approvals)),
            wf.description[:35] + "..." if len(wf.description) > 35 else wf.description,
            f"[green]{is_active}[/]" if is_active else "",
        )

    console.print(table)
    console.print(f"\n[dim]Active workflow: {active or 'none'}[/]")


@app.command("show")
def workflows_show(
    name: str = typer.Argument(..., help="Workflow name to show."),
) -> None:
    """Show detailed workflow configuration."""
    workflow = load_workflow(name)
    if not workflow:
        console.print(f"[red]Workflow '{name}' not found.[/]")
        raise typer.Exit(1)

    tree = Tree(f"[bold cyan]{workflow.name}[/]")

    if workflow.description:
        tree.add(f"[dim]{workflow.description}[/]")

    if workflow.context_type:
        tree.add(f"[bold]Context:[/] {workflow.context_type}")

    if workflow.auto_approvals:
        approvals = tree.add("[bold]Auto-approvals[/]")
        for approval in workflow.auto_approvals[:5]:
            approvals.add(approval)
        if len(workflow.auto_approvals) > 5:
            approvals.add(f"[dim]... and {len(workflow.auto_approvals) - 5} more[/]")

    if workflow.claude_commands:
        commands = tree.add("[bold]Claude Commands[/]")
        for cmd in workflow.claude_commands:
            commands.add(f"/{cmd}")

    if workflow.shell_aliases:
        aliases = tree.add("[bold]Shell Aliases[/]")
        for alias, cmd in list(workflow.shell_aliases.items())[:5]:
            aliases.add(f"{alias} → {cmd}")

    if workflow.status_bar:
        tree.add(f"[bold]Status Bar:[/] {workflow.status_bar}")

    if workflow.hooks:
        hooks = tree.add("[bold]Hooks[/]")
        for hook in workflow.hooks:
            hooks.add(hook)

    console.print(tree)

    is_builtin = name in WORKFLOW_TEMPLATES
    console.print(f"\n[dim]Type: {'Built-in' if is_builtin else 'Custom'}[/]")


@app.command("apply")
def workflows_apply(
    name: str = typer.Argument(..., help="Workflow to apply."),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be applied."),
) -> None:
    """Apply a workflow template."""
    workflow = load_workflow(name)
    if not workflow:
        console.print(f"[red]Workflow '{name}' not found.[/]")
        raise typer.Exit(1)

    console.print(f"[bold cyan]Applying workflow: {name}[/]\n")

    # Show what will be applied
    if workflow.auto_approvals:
        console.print(f"[bold]Auto-approvals:[/] {len(workflow.auto_approvals)} rules")
        if dry_run:
            for rule in workflow.auto_approvals[:3]:
                console.print(f"  + {rule}")

    if workflow.shell_aliases:
        console.print(f"[bold]Shell aliases:[/] {len(workflow.shell_aliases)}")
        if dry_run:
            for alias in list(workflow.shell_aliases.keys())[:3]:
                console.print(f"  + {alias}")

    if workflow.status_bar:
        console.print(f"[bold]Status bar:[/] {workflow.status_bar}")

    if workflow.hooks:
        console.print(f"[bold]Hooks:[/] {', '.join(workflow.hooks)}")

    if dry_run:
        console.print("\n[yellow]Dry run - no changes made.[/]")
        return

    # Apply the workflow
    actions = []

    # Set as active
    if set_active_workflow(name):
        actions.append("Set as active workflow")

    # Apply auto-approvals to Claude Code settings
    if workflow.auto_approvals:
        settings_path = Path.home() / ".claude" / "settings.json"
        try:
            if settings_path.exists():
                data = json.loads(settings_path.read_text())
            else:
                data = {}

            permissions = data.setdefault("permissions", {})
            allow = set(permissions.get("allow", []))
            allow.update(workflow.auto_approvals)
            permissions["allow"] = sorted(allow)

            settings_path.write_text(json.dumps(data, indent=2))
            actions.append(f"Added {len(workflow.auto_approvals)} auto-approvals")
        except (json.JSONDecodeError, OSError) as e:
            console.print(f"[yellow]Warning: Could not update auto-approvals: {e}[/]")

    # Set environment variables
    if workflow.environment_vars:
        for key, value in workflow.environment_vars.items():
            os.environ[key] = os.path.expanduser(value)
        actions.append(f"Set {len(workflow.environment_vars)} environment variables")

    # Run init commands
    if workflow.init_commands:
        import subprocess
        for cmd in workflow.init_commands:
            try:
                subprocess.run(cmd, shell=True, check=False, capture_output=True)
            except Exception:
                pass
        actions.append(f"Ran {len(workflow.init_commands)} init commands")

    console.print(f"\n[green]Applied workflow '{name}':[/]")
    for action in actions:
        console.print(f"  [green]✓[/] {action}")


@app.command("create")
def workflows_create(
    name: str = typer.Argument(..., help="Name for the new workflow."),
    based_on: str = typer.Option(None, "--based-on", "-b", help="Base on existing workflow."),
    description: str = typer.Option("", "--desc", "-d", help="Workflow description."),
    context: str = typer.Option("", "--context", "-c", help="Context type."),
) -> None:
    """Create a custom workflow template."""
    if name in WORKFLOW_TEMPLATES:
        console.print(f"[red]Cannot override built-in workflow '{name}'.[/]")
        raise typer.Exit(1)

    # Start from base or blank
    if based_on:
        base = load_workflow(based_on)
        if not base:
            console.print(f"[red]Base workflow '{based_on}' not found.[/]")
            raise typer.Exit(1)
        workflow = WorkflowTemplate(
            name=name,
            description=description or base.description,
            context_type=context or base.context_type,
            auto_approvals=base.auto_approvals.copy(),
            claude_commands=base.claude_commands.copy(),
            environment_vars=base.environment_vars.copy(),
            shell_aliases=base.shell_aliases.copy(),
            status_bar=base.status_bar,
            hooks=base.hooks.copy(),
            init_commands=base.init_commands.copy(),
        )
    else:
        workflow = WorkflowTemplate(
            name=name,
            description=description,
            context_type=context,
        )

    if save_workflow(workflow):
        console.print(f"[green]Created workflow '{name}'[/]")
        console.print(f"  Location: {get_workflows_dir() / f'{name}.json'}")
        console.print("\n[dim]Edit the JSON file to customize, then apply with 'ait workflows apply'.[/]")
    else:
        console.print("[red]Failed to save workflow.[/]")
        raise typer.Exit(1)


@app.command("remove")
def workflows_remove(
    name: str = typer.Argument(..., help="Workflow to remove."),
) -> None:
    """Remove a custom workflow."""
    if name in WORKFLOW_TEMPLATES:
        console.print(f"[red]Cannot remove built-in workflow '{name}'.[/]")
        raise typer.Exit(1)

    workflow_file = get_workflows_dir() / f"{name}.json"
    if not workflow_file.exists():
        console.print(f"[red]Custom workflow '{name}' not found.[/]")
        raise typer.Exit(1)

    try:
        workflow_file.unlink()
        console.print(f"[green]Removed workflow '{name}'[/]")

        # Clear active if this was it
        if get_active_workflow() == name:
            (get_workflows_dir() / ".active").unlink(missing_ok=True)
            console.print("[dim]Cleared active workflow.[/]")
    except OSError as e:
        console.print(f"[red]Failed to remove: {e}[/]")
        raise typer.Exit(1)


@app.command("detect")
def workflows_detect() -> None:
    """Suggest a workflow based on current project."""
    from aiterm.context.detector import detect_project_type

    cwd = Path.cwd()
    project_type = detect_project_type(cwd)

    console.print("[bold cyan]Workflow Detection[/]\n")
    console.print(f"Project: {cwd.name}")
    console.print(f"Detected type: {project_type or 'unknown'}")

    # Map project types to workflows
    type_to_workflow = {
        "r": "r-development",
        "python": "python-development",
        "node": "node-development",
        "quarto": "research",
        "mcp": "mcp-development",
    }

    suggested = type_to_workflow.get(project_type)
    if suggested:
        console.print(f"\n[green]Suggested workflow:[/] {suggested}")
        console.print(f"\nApply with: ait workflows apply {suggested}")
    else:
        console.print("\n[yellow]No specific workflow suggested.[/]")
        console.print("Use 'ait workflows list' to see all available workflows.")


@app.command("export")
def workflows_export(
    name: str = typer.Argument(..., help="Workflow to export."),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path."),
) -> None:
    """Export a workflow to a JSON file."""
    workflow = load_workflow(name)
    if not workflow:
        console.print(f"[red]Workflow '{name}' not found.[/]")
        raise typer.Exit(1)

    output_path = output or Path.cwd() / f"{name}-workflow.json"

    try:
        output_path.write_text(json.dumps(workflow.to_dict(), indent=2))
        console.print(f"[green]Exported workflow to:[/] {output_path}")
    except OSError as e:
        console.print(f"[red]Failed to export: {e}[/]")
        raise typer.Exit(1)


@app.command("import")
def workflows_import(
    file: Path = typer.Argument(..., help="JSON file to import."),
    name: str = typer.Option(None, "--name", "-n", help="Override workflow name."),
) -> None:
    """Import a workflow from a JSON file."""
    if not file.exists():
        console.print(f"[red]File not found: {file}[/]")
        raise typer.Exit(1)

    try:
        data = json.loads(file.read_text())
        workflow_name = name or data.get("name", file.stem)

        if workflow_name in WORKFLOW_TEMPLATES:
            console.print(f"[red]Cannot import over built-in workflow '{workflow_name}'.[/]")
            raise typer.Exit(1)

        workflow = WorkflowTemplate(
            name=workflow_name,
            description=data.get("description", ""),
            context_type=data.get("context_type", ""),
            auto_approvals=data.get("auto_approvals", []),
            claude_commands=data.get("claude_commands", []),
            environment_vars=data.get("environment_vars", {}),
            shell_aliases=data.get("shell_aliases", {}),
            status_bar=data.get("status_bar", ""),
            hooks=data.get("hooks", []),
            init_commands=data.get("init_commands", []),
        )

        if save_workflow(workflow):
            console.print(f"[green]Imported workflow '{workflow_name}'[/]")
        else:
            console.print("[red]Failed to save imported workflow.[/]")
            raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/]")
        raise typer.Exit(1)
