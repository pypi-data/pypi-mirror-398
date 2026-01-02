"""Memory system management CLI for Claude Code.

Phase 2.5.2: Manage CLAUDE.md files and memory hierarchy.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

app = typer.Typer(
    help="Manage Claude Code memory system (CLAUDE.md files).",
    no_args_is_help=True,
)
console = Console()


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class MemoryFile:
    """Represents a CLAUDE.md file in the memory hierarchy."""

    path: Path
    level: str  # "global", "project", "rules"
    exists: bool
    size: int = 0
    modified: datetime | None = None
    lines: int = 0

    @property
    def age_days(self) -> int | None:
        """Calculate age in days since last modification."""
        if not self.modified:
            return None
        delta = datetime.now() - self.modified
        return delta.days


def get_memory_hierarchy(project_path: Path | None = None) -> list[MemoryFile]:
    """Get the complete memory hierarchy for a project."""
    hierarchy = []

    # Global CLAUDE.md
    global_path = Path.home() / ".claude" / "CLAUDE.md"
    hierarchy.append(_create_memory_file(global_path, "global"))

    # Project CLAUDE.md
    if project_path:
        project_claude = project_path / "CLAUDE.md"
        hierarchy.append(_create_memory_file(project_claude, "project"))

        # Project rules
        rules_dir = project_path / ".claude" / "rules"
        if rules_dir.exists():
            for rule_file in sorted(rules_dir.glob("*.md")):
                hierarchy.append(_create_memory_file(rule_file, "rules"))

    return hierarchy


def _create_memory_file(path: Path, level: str) -> MemoryFile:
    """Create a MemoryFile from a path."""
    if path.exists():
        stat = path.stat()
        content = path.read_text()
        return MemoryFile(
            path=path,
            level=level,
            exists=True,
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime),
            lines=len(content.splitlines()),
        )
    return MemoryFile(path=path, level=level, exists=False)


# =============================================================================
# CLI Commands
# =============================================================================


@app.command("hierarchy")
def memory_hierarchy(
    path: Path = typer.Argument(None, help="Project directory (default: current)."),
) -> None:
    """Show the memory hierarchy and precedence order."""
    project_path = path or Path.cwd()

    console.print("[bold cyan]Claude Code Memory Hierarchy[/]\n")
    console.print("[dim]Higher in list = lower priority (overridden by items below)[/]\n")

    hierarchy = get_memory_hierarchy(project_path)

    tree = Tree("[bold]Memory Sources[/] (precedence: bottom wins)")

    for mem in hierarchy:
        if mem.exists:
            age_str = f" ({mem.age_days}d ago)" if mem.age_days else ""
            status = f"[green]✓[/] {mem.path} ({mem.lines} lines){age_str}"
        else:
            status = f"[dim]○ {mem.path} (not found)[/]"

        if mem.level == "global":
            tree.add(f"[blue]Global:[/] {status}")
        elif mem.level == "project":
            tree.add(f"[green]Project:[/] {status}")
        elif mem.level == "rules":
            tree.add(f"[yellow]Rule:[/] {status}")

    console.print(tree)

    # Summary
    existing = [m for m in hierarchy if m.exists]
    console.print(f"\n[bold]Active memory files:[/] {len(existing)}/{len(hierarchy)}")

    # Check for stale files
    stale = [m for m in existing if m.age_days and m.age_days > 14]
    if stale:
        console.print(f"[yellow]⚠ {len(stale)} file(s) older than 14 days - consider updating[/]")


@app.command("validate")
def memory_validate(
    path: Path = typer.Argument(None, help="Project directory (default: current)."),
) -> None:
    """Validate CLAUDE.md files for common issues."""
    project_path = path or Path.cwd()
    hierarchy = get_memory_hierarchy(project_path)
    existing = [m for m in hierarchy if m.exists]

    if not existing:
        console.print("[yellow]No CLAUDE.md files found.[/]")
        console.print("Use 'ait memory create' to create one.")
        return

    issues = []
    warnings = []

    for mem in existing:
        content = mem.path.read_text()

        # Check for common issues
        if mem.lines == 0:
            issues.append(f"{mem.path}: Empty file")
        elif mem.lines < 10:
            warnings.append(f"{mem.path}: Very short ({mem.lines} lines)")

        # Check for stale content
        if mem.age_days and mem.age_days > 30:
            warnings.append(f"{mem.path}: Stale content ({mem.age_days} days old)")

        # Check for basic structure
        if mem.level == "project":
            if "# " not in content:
                warnings.append(f"{mem.path}: Missing main heading")
            if "## " not in content:
                warnings.append(f"{mem.path}: Missing section headings")

    # Report
    console.print("[bold cyan]Memory Validation Results[/]\n")

    if issues:
        console.print("[red]Issues:[/]")
        for issue in issues:
            console.print(f"  [red]✗[/] {issue}")

    if warnings:
        console.print("[yellow]Warnings:[/]")
        for warning in warnings:
            console.print(f"  [yellow]⚠[/] {warning}")

    if not issues and not warnings:
        console.print(f"[green]✓ All {len(existing)} file(s) valid[/]")
    elif issues:
        raise typer.Exit(1)


@app.command("create")
def memory_create(
    level: str = typer.Argument(..., help="Level: 'global', 'project', or 'rule'."),
    name: str = typer.Option(None, "--name", "-n", help="Rule name (for rule level only)."),
    template: str = typer.Option(None, "--template", "-t", help="Template to use."),
    path: Path = typer.Option(None, "--path", "-p", help="Project path (for project level)."),
) -> None:
    """Create a new CLAUDE.md or rule file."""
    templates = {
        "project": """# Project Name

Brief description of the project.

## Overview

What this project does and its main purpose.

## Key Commands

```bash
# Common commands here
```

## Architecture

Key architectural decisions and patterns.

## Conventions

Coding conventions and standards for this project.
""",
        "global": """# Global Claude Code Instructions

Personal preferences and patterns that apply to all projects.

## Coding Style

- Prefer concise, clear code
- Use type hints in Python
- Follow project conventions

## Communication

- Be direct and concise
- Explain trade-offs when relevant

## Tools

- Use appropriate tools for the task
- Prefer built-in tools over complex solutions
""",
        "rule": """# Rule: {name}

## When to Apply

Describe when this rule should be active.

## Instructions

Specific instructions for Claude when this rule applies.

## Examples

Example interactions or code patterns.
""",
    }

    if level == "global":
        target_path = Path.home() / ".claude" / "CLAUDE.md"
        content = templates["global"]
    elif level == "project":
        project_path = path or Path.cwd()
        target_path = project_path / "CLAUDE.md"
        content = templates["project"]
    elif level == "rule":
        if not name:
            console.print("[red]Rule name required (--name).[/]")
            raise typer.Exit(1)
        project_path = path or Path.cwd()
        rules_dir = project_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        target_path = rules_dir / f"{name}.md"
        content = templates["rule"].replace("{name}", name)
    else:
        console.print(f"[red]Unknown level: {level}[/]")
        console.print("Use 'global', 'project', or 'rule'.")
        raise typer.Exit(1)

    if target_path.exists():
        console.print(f"[yellow]File already exists: {target_path}[/]")
        console.print("Use 'ait memory edit' to modify it.")
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content)
    console.print(f"[green]Created:[/] {target_path}")
    console.print("\n[dim]Edit this file to add project-specific instructions.[/]")


@app.command("show")
def memory_show(
    level: str = typer.Argument("project", help="Level: 'global', 'project', or 'all'."),
    path: Path = typer.Option(None, "--path", "-p", help="Project path."),
) -> None:
    """Show contents of CLAUDE.md file(s)."""
    project_path = path or Path.cwd()

    if level == "global":
        files = [Path.home() / ".claude" / "CLAUDE.md"]
    elif level == "project":
        files = [project_path / "CLAUDE.md"]
    elif level == "all":
        hierarchy = get_memory_hierarchy(project_path)
        files = [m.path for m in hierarchy if m.exists]
    else:
        console.print(f"[red]Unknown level: {level}[/]")
        raise typer.Exit(1)

    for file_path in files:
        if not file_path.exists():
            console.print(f"[yellow]Not found: {file_path}[/]")
            continue

        content = file_path.read_text()
        # Truncate if too long
        lines = content.splitlines()
        if len(lines) > 50:
            display = "\n".join(lines[:50]) + f"\n\n[dim]... ({len(lines) - 50} more lines)[/]"
        else:
            display = content

        console.print(Panel(
            display,
            title=str(file_path),
            border_style="cyan",
        ))


@app.command("stats")
def memory_stats(
    path: Path = typer.Argument(None, help="Project directory (default: current)."),
) -> None:
    """Show memory system statistics."""
    project_path = path or Path.cwd()
    hierarchy = get_memory_hierarchy(project_path)

    table = Table(title="Memory Statistics", border_style="cyan")
    table.add_column("File", style="bold")
    table.add_column("Level")
    table.add_column("Lines", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Age", justify="right")
    table.add_column("Status")

    total_lines = 0
    total_size = 0

    for mem in hierarchy:
        if mem.exists:
            total_lines += mem.lines
            total_size += mem.size
            age = f"{mem.age_days}d" if mem.age_days else "-"
            status = "[green]✓[/]"
            if mem.age_days and mem.age_days > 14:
                status = "[yellow]⚠ stale[/]"
        else:
            age = "-"
            status = "[dim]missing[/]"

        table.add_row(
            mem.path.name,
            mem.level,
            str(mem.lines) if mem.exists else "-",
            f"{mem.size}B" if mem.exists else "-",
            age,
            status,
        )

    console.print(table)
    console.print(f"\n[bold]Total:[/] {total_lines} lines, {total_size} bytes")


@app.command("rules")
def memory_rules(
    path: Path = typer.Argument(None, help="Project directory (default: current)."),
) -> None:
    """List path-specific rules (.claude/rules/*.md)."""
    project_path = path or Path.cwd()
    rules_dir = project_path / ".claude" / "rules"

    if not rules_dir.exists():
        console.print("[yellow]No rules directory found.[/]")
        console.print(f"Create rules at: {rules_dir}")
        console.print("\nUse 'ait memory create rule --name <name>' to create one.")
        return

    rules = list(rules_dir.glob("*.md"))
    if not rules:
        console.print("[yellow]No rules found.[/]")
        return

    table = Table(title="Path-Specific Rules", border_style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Lines", justify="right")
    table.add_column("Description")

    for rule_path in sorted(rules):
        content = rule_path.read_text()
        lines = len(content.splitlines())
        # Extract first non-empty, non-heading line as description
        desc = ""
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                desc = line[:50] + "..." if len(line) > 50 else line
                break

        table.add_row(
            rule_path.stem,
            str(lines),
            desc,
        )

    console.print(table)
