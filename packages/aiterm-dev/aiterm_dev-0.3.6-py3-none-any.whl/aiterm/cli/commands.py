"""CLI commands for command template management."""

from typing import Optional
import typer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from aiterm.commands import CommandLibrary

app = typer.Typer(help="Manage Claude Code command templates")
console = Console()


@app.command()
def list(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category")
):
    """List installed commands and available templates."""
    library = CommandLibrary()

    installed = library.list_installed(category=category)
    available = library.list_available(category=category)

    # Show installed commands
    if installed:
        table = Table(title="📌 Installed Commands", show_header=True)
        table.add_column("Command", style="cyan")
        table.add_column("Category", style="magenta")
        table.add_column("Size", justify="right")

        for cmd in installed:
            size_kb = cmd.size / 1024
            table.add_row(
                cmd.name,
                cmd.category or "-",
                f"{size_kb:.1f} KB"
            )

        console.print(table)
    else:
        console.print("[yellow]No commands installed yet[/yellow]")

    # Show available templates
    print()
    if available:
        table = Table(title="📦 Available Templates", show_header=True)
        table.add_column("Template", style="blue")
        table.add_column("Category", style="magenta")
        table.add_column("Description")

        for template in available:
            # Check if already installed
            is_installed = any(
                c.name == template.name and c.category == template.category
                for c in installed
            )
            name_display = f"{template.name} ✓" if is_installed else template.name

            table.add_row(
                name_display,
                template.category or "-",
                template.description
            )

        console.print(table)
        print()
        console.print("[dim]Install a template: aiterm commands install <category>:<name>[/dim]")
        console.print("[dim]Or just: aiterm commands install <name>[/dim]")
    else:
        console.print("[yellow]No templates available[/yellow]")


@app.command()
def browse():
    """Browse templates by category (interactive)."""
    library = CommandLibrary()

    categories = library.browse_by_category()

    if not categories:
        console.print("[yellow]No templates available[/yellow]")
        return

    # Create tree view
    tree = Tree("📚 Command Templates", guide_style="cyan")

    for category, templates in sorted(categories.items()):
        category_node = tree.add(f"[bold magenta]{category}[/bold magenta] ({len(templates)} templates)")

        for template in templates:
            template_node = category_node.add(
                f"[cyan]{template.name}[/cyan] - {template.description}"
            )

    console.print(tree)
    print()
    console.print("[dim]Install: aiterm commands install <category>:<name>[/dim]")


@app.command()
def install(
    template: str = typer.Argument(..., help="Template to install (category:name or name)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists")
):
    """Install a command from template."""
    library = CommandLibrary()

    try:
        # Install command
        library.install(template, force=force)

        console.print(f"[green]✓[/green] Installed command: [cyan]{template}[/cyan]")

        # Determine location
        if ':' in template:
            category, name = template.split(':', 1)
            location = f"~/.claude/commands/{category}/{name}.md"
        else:
            location = f"~/.claude/commands/{template}.md"

        console.print(f"[dim]Location: {location}[/dim]")

        # Show next steps
        print()
        console.print(Panel(
            "[bold]Next Steps:[/bold]\n\n"
            f"1. Command is available in Claude Code sessions\n"
            f"2. Use it: [cyan]/{template.split(':')[-1]}[/cyan]\n"
            f"3. Edit if needed: [cyan]{location}[/cyan]",
            title="🎉 Installation Complete",
            border_style="green"
        ))

    except FileNotFoundError:
        console.print(f"[red]✗[/red] Template '[cyan]{template}[/cyan]' not found")
        console.print("\n[dim]See available templates: aiterm commands list[/dim]")
        console.print("[dim]Or browse by category: aiterm commands browse[/dim]")
        raise typer.Exit(1)

    except FileExistsError:
        console.print(f"[red]✗[/red] Command '[cyan]{template}[/cyan]' already exists")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(1)


@app.command()
def validate(
    command: Optional[str] = typer.Argument(None, help="Specific command to validate")
):
    """Validate installed commands."""
    library = CommandLibrary()

    results = library.validate(command)

    if not results["commands"]:
        console.print("[yellow]No commands to validate[/yellow]")
        return

    # Show results
    table = Table(title="🔍 Command Validation", show_header=True)
    table.add_column("Command", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Status")
    table.add_column("Issues")

    for cmd_result in results["commands"]:
        name = cmd_result["name"]
        category = name.split(':')[0] if ':' in name else "-"
        cmd_name = name.split(':')[-1]

        status = "[green]✓ Valid[/green]" if cmd_result["valid"] else "[red]✗ Invalid[/red]"
        issues = "\n".join(cmd_result["issues"]) if cmd_result["issues"] else "-"

        table.add_row(
            cmd_name,
            category,
            status,
            issues
        )

    console.print(table)

    # Overall result
    print()
    if results["valid"]:
        console.print("[green]All commands are valid! ✨[/green]")
    else:
        console.print("[yellow]⚠️  Some commands have issues[/yellow]")
        console.print("\n[dim]Common fixes:[/dim]")
        console.print("[dim]  - Add YAML frontmatter with '---' markers[/dim]")
        console.print("[dim]  - Include required field: description[/dim]")


@app.command()
def uninstall(
    command: str = typer.Argument(..., help="Command to uninstall"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Uninstall a command."""
    library = CommandLibrary()

    # Confirm
    if not yes:
        confirm = typer.confirm(f"Uninstall command '{command}'?")
        if not confirm:
            console.print("Cancelled")
            raise typer.Exit(0)

    # Uninstall
    if library.uninstall(command):
        console.print(f"[green]✓[/green] Uninstalled command: [cyan]{command}[/cyan]")
    else:
        console.print(f"[red]✗[/red] Command '[cyan]{command}[/cyan]' not found")
        raise typer.Exit(1)
