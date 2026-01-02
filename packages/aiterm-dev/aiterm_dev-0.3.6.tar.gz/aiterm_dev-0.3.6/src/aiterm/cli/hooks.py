"""CLI commands for hook management."""

from typing import Optional
import typer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from aiterm.hooks import HookManager

app = typer.Typer(help="Manage Claude Code hooks")
console = Console()


@app.command(
    epilog="""
[bold]Examples:[/]
  ait hooks list          # Show installed and available hooks
"""
)
def list():
    """List all installed hooks."""
    manager = HookManager()

    installed = manager.list_installed()
    available = manager.list_available()

    # Show installed hooks
    if installed:
        table = Table(title="📌 Installed Hooks", show_header=True)
        table.add_column("Hook Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Size", justify="right")

        for hook in installed:
            status = "✅ Ready" if hook.is_valid else "⚠️  Not executable"
            size_kb = hook.size / 1024
            table.add_row(
                hook.name,
                status,
                f"{size_kb:.1f} KB"
            )

        console.print(table)
    else:
        console.print("[yellow]No hooks installed yet[/yellow]")

    # Show available templates
    print()
    if available:
        table = Table(title="📦 Available Templates", show_header=True)
        table.add_column("Template", style="blue")
        table.add_column("Type", style="magenta")
        table.add_column("Description")

        for template in available:
            # Check if already installed
            is_installed = any(h.name == f"{template.name}.sh" for h in installed)
            name_display = f"{template.name} ✓" if is_installed else template.name

            table.add_row(
                name_display,
                template.hook_type,
                template.description
            )

        console.print(table)
        print()
        console.print("[dim]Install a template: aiterm hooks install <name>[/dim]")
    else:
        console.print("[yellow]No templates available[/yellow]")


@app.command(
    epilog="""
[bold]Examples:[/]
  ait hooks install prompt-optimizer    # Install optimizer hook
  ait hooks install context-auto -f     # Force reinstall
"""
)
def install(
    template: str = typer.Argument(..., help="Template name to install"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists")
):
    """Install a hook from template."""
    manager = HookManager()

    try:
        # Install hook
        manager.install(template, force=force)

        console.print(f"[green]✓[/green] Installed hook: [cyan]{template}[/cyan]")
        console.print(f"[dim]Location: ~/.claude/hooks/{template}.sh[/dim]")

        # Show next steps
        print()
        console.print(Panel(
            "[bold]Next Steps:[/bold]\n\n"
            f"1. Hook is active for all Claude Code sessions\n"
            f"2. Test it: [cyan]aiterm hooks test {template}[/cyan]\n"
            f"3. Edit if needed: [cyan]~/.claude/hooks/{template}.sh[/cyan]",
            title="🎉 Installation Complete",
            border_style="green"
        ))

    except FileNotFoundError:
        console.print(f"[red]✗[/red] Template '[cyan]{template}[/cyan]' not found")
        console.print("\n[dim]See available templates: aiterm hooks list[/dim]")
        raise typer.Exit(1)

    except FileExistsError:
        console.print(f"[red]✗[/red] Hook '[cyan]{template}[/cyan]' already exists")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(1)


@app.command(
    epilog="""
[bold]Examples:[/]
  ait hooks validate                    # Validate all hooks
  ait hooks validate prompt-optimizer   # Validate specific hook
"""
)
def validate(
    hook: Optional[str] = typer.Argument(None, help="Specific hook to validate")
):
    """Validate installed hooks."""
    manager = HookManager()

    results = manager.validate(hook)

    if not results["hooks"]:
        console.print("[yellow]No hooks to validate[/yellow]")
        return

    # Show results
    table = Table(title="🔍 Hook Validation", show_header=True)
    table.add_column("Hook", style="cyan")
    table.add_column("Status")
    table.add_column("Issues")

    for hook_result in results["hooks"]:
        status = "[green]✓ Valid[/green]" if hook_result["valid"] else "[red]✗ Invalid[/red]"
        issues = "\n".join(hook_result["issues"]) if hook_result["issues"] else "-"

        table.add_row(
            hook_result["name"],
            status,
            issues
        )

    console.print(table)

    # Overall result
    print()
    if results["valid"]:
        console.print("[green]All hooks are valid! ✨[/green]")
    else:
        console.print("[yellow]⚠️  Some hooks have issues[/yellow]")
        console.print("\n[dim]Fix executable: chmod +x ~/.claude/hooks/<hook>[/dim]")


@app.command(
    epilog="""
[bold]Examples:[/]
  ait hooks test prompt-optimizer   # Test hook execution
"""
)
def test(
    hook: str = typer.Argument(..., help="Hook name to test")
):
    """Test a hook by executing it."""
    manager = HookManager()

    console.print(f"Testing hook: [cyan]{hook}[/cyan]...")

    try:
        result = manager.test(hook)

        # Show results
        if result["success"]:
            console.print(f"[green]✓ Test passed[/green] ({result['duration_ms']:.0f}ms)")
        else:
            console.print(f"[red]✗ Test failed[/red] (exit code: {result['exit_code']})")

        # Show output
        if result["stdout"]:
            print()
            console.print(Panel(result["stdout"], title="stdout", border_style="blue"))

        if result["stderr"]:
            print()
            console.print(Panel(result["stderr"], title="stderr", border_style="red"))

        # Performance warning
        if result["duration_ms"] > 500:
            print()
            console.print(
                f"[yellow]⚠️  Hook took {result['duration_ms']:.0f}ms[/yellow]\n"
                "[dim]Claude Code hooks should complete in <500ms to avoid delays[/dim]"
            )

    except FileNotFoundError:
        console.print(f"[red]✗[/red] Hook '[cyan]{hook}[/cyan]' not found")
        raise typer.Exit(1)


@app.command(
    epilog="""
[bold]Examples:[/]
  ait hooks uninstall prompt-optimizer      # Uninstall with prompt
  ait hooks uninstall prompt-optimizer -y   # Skip confirmation
"""
)
def uninstall(
    hook: str = typer.Argument(..., help="Hook name to uninstall"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Uninstall a hook."""
    manager = HookManager()

    # Confirm
    if not yes:
        confirm = typer.confirm(f"Uninstall hook '{hook}'?")
        if not confirm:
            console.print("Cancelled")
            raise typer.Exit(0)

    # Uninstall
    if manager.uninstall(hook):
        console.print(f"[green]✓[/green] Uninstalled hook: [cyan]{hook}[/cyan]")
    else:
        console.print(f"[red]✗[/red] Hook '[cyan]{hook}[/cyan]' not found")
        raise typer.Exit(1)
