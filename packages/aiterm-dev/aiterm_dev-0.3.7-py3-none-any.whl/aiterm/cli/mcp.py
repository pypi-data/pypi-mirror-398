"""CLI commands for MCP server management."""

from typing import Optional
import typer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from aiterm.mcp import MCPManager

app = typer.Typer(help="Manage MCP servers for Claude Code")
console = Console()


@app.command(
    epilog="""
[bold]Examples:[/]
  ait mcp list            # Show all configured servers
"""
)
def list():
    """List all configured MCP servers."""
    manager = MCPManager()

    servers = manager.list_servers()

    if not servers:
        console.print("[yellow]No MCP servers configured[/yellow]")
        console.print("\n[dim]Configure servers in: ~/.claude/settings.json[/dim]")
        console.print("[dim]See: https://modelcontextprotocol.io[/dim]")
        return

    # Create table
    table = Table(title="📡 Configured MCP Servers", show_header=True)
    table.add_column("Server Name", style="cyan")
    table.add_column("Command", style="green")
    table.add_column("Args", style="dim")

    for server in servers:
        args_display = " ".join(server.args[:2])  # Show first 2 args
        if len(server.args) > 2:
            args_display += "..."

        table.add_row(
            server.name,
            server.command,
            args_display or "-"
        )

    console.print(table)
    print()
    console.print(f"[dim]Total servers: {len(servers)}[/dim]")
    console.print(f"[dim]Config: {manager.settings_path}[/dim]")
    print()
    console.print("[dim]Test a server: aiterm mcp test <name>[/dim]")


@app.command(
    epilog="""
[bold]Examples:[/]
  ait mcp test filesystem        # Test specific server
  ait mcp test memory -t 10      # Test with 10s timeout
"""
)
def test(
    server_name: str = typer.Argument(..., help="Server name to test"),
    timeout: float = typer.Option(5.0, "--timeout", "-t", help="Timeout in seconds")
):
    """Test an MCP server by checking if it's reachable."""
    manager = MCPManager()

    console.print(f"Testing MCP server: [cyan]{server_name}[/cyan]...")

    result = manager.test_server(server_name, timeout=timeout)

    # Show results
    if result["success"]:
        console.print(
            f"[green]✓ Server reachable[/green] ({result['duration_ms']:.0f}ms)"
        )

        # Show server info
        info = manager.get_server_info(server_name)
        if info:
            print()
            console.print(Panel(
                f"[bold]Command:[/bold] {info['command']}\n"
                f"[bold]Args:[/bold] {' '.join(info['args']) if info['args'] else 'none'}\n"
                f"[bold]Full:[/bold] {info['full_command']}",
                title=f"Server: {server_name}",
                border_style="green"
            ))
    else:
        console.print(f"[red]✗ Server unreachable[/red]")

        if result["error"]:
            print()
            console.print(f"[red]Error:[/red] {result['error']}")

        # Show troubleshooting
        print()
        console.print(Panel(
            "[bold]Troubleshooting:[/bold]\n\n"
            "1. Check if command exists: [cyan]which <command>[/cyan]\n"
            "2. Verify settings.json syntax\n"
            "3. Check environment variables\n"
            "4. Try running command manually",
            title="⚠️  Server Not Reachable",
            border_style="yellow"
        ))


@app.command(
    epilog="""
[bold]Examples:[/]
  ait mcp validate       # Check configuration syntax
"""
)
def validate():
    """Validate MCP server configuration."""
    manager = MCPManager()

    console.print("Validating MCP configuration...")

    result = manager.validate_config()

    # Show results
    table = Table(title="🔍 Configuration Validation", show_header=False)
    table.add_column("Check", style="bold")
    table.add_column("Status")

    # Settings file
    status = "[green]✓ Found[/green]" if result["settings_exists"] else "[red]✗ Not Found[/red]"
    table.add_row("Settings file", status)

    # Valid JSON
    if result["settings_exists"]:
        status = "[green]✓ Valid[/green]" if result["valid_json"] else "[red]✗ Invalid[/red]"
        table.add_row("JSON syntax", status)

    # Server count
    if result["valid_json"]:
        table.add_row("Servers configured", f"[cyan]{result['servers_count']}[/cyan]")

    console.print(table)

    # Show issues
    if result["issues"]:
        print()
        console.print("[yellow]Issues found:[/yellow]")
        for issue in result["issues"]:
            console.print(f"  [red]✗[/red] {issue}")
    else:
        print()
        console.print("[green]Configuration is valid! ✨[/green]")

    # Show config path
    print()
    console.print(f"[dim]Config: {manager.settings_path}[/dim]")


@app.command(
    epilog="""
[bold]Examples:[/]
  ait mcp info filesystem   # Show server details
  ait mcp info memory       # Show env vars, command
"""
)
def info(
    server_name: str = typer.Argument(..., help="Server name to show info for")
):
    """Show detailed information about a server."""
    manager = MCPManager()

    info = manager.get_server_info(server_name)

    if not info:
        console.print(f"[red]✗[/red] Server '[cyan]{server_name}[/cyan]' not found")
        console.print("\n[dim]See available servers: aiterm mcp list[/dim]")
        raise typer.Exit(1)

    # Show server details
    console.print(Panel(
        f"[bold cyan]{info['name']}[/bold cyan]\n\n"
        f"[bold]Command:[/bold] {info['command']}\n"
        f"[bold]Args:[/bold] {' '.join(info['args']) if info['args'] else 'none'}\n"
        f"[bold]Environment:[/bold] {len(info['env'])} variables\n\n"
        f"[bold]Full command:[/bold]\n{info['full_command']}",
        title="MCP Server Info",
        border_style="cyan"
    ))

    # Show environment variables if any
    if info['env']:
        print()
        console.print("[bold]Environment Variables:[/bold]")
        for key, value in info['env'].items():
            # Mask sensitive values
            if any(x in key.lower() for x in ['key', 'secret', 'token', 'password']):
                value = '***' + value[-4:] if len(value) > 4 else '***'
            console.print(f"  {key}={value}")

    # Show config location
    print()
    console.print(f"[dim]Config: {info['config_path']}[/dim]")


@app.command(
    epilog="""
[bold]Examples:[/]
  ait mcp test-all           # Test all servers
  ait mcp test-all -t 10     # 10s timeout per server
"""
)
def test_all(
    timeout: float = typer.Option(5.0, "--timeout", "-t", help="Timeout per server")
):
    """Test all configured MCP servers."""
    manager = MCPManager()

    servers = manager.list_servers()

    if not servers:
        console.print("[yellow]No MCP servers configured[/yellow]")
        return

    console.print(f"Testing {len(servers)} MCP servers...\n")

    # Test each server
    results = []
    for server in servers:
        result = manager.test_server(server.name, timeout=timeout)
        results.append(result)

    # Show results table
    table = Table(title="🧪 Server Test Results", show_header=True)
    table.add_column("Server", style="cyan")
    table.add_column("Status")
    table.add_column("Time", justify="right")
    table.add_column("Notes")

    for result in results:
        if result["success"]:
            status = "[green]✓ Reachable[/green]"
            time_str = f"{result['duration_ms']:.0f}ms"
            notes = "-"
        else:
            status = "[red]✗ Failed[/red]"
            time_str = "-"
            notes = result["error"] or "Unknown error"

        table.add_row(
            result["server_name"],
            status,
            time_str,
            notes
        )

    console.print(table)

    # Summary
    successful = sum(1 for r in results if r["success"])
    print()
    console.print(
        f"Results: [green]{successful} passed[/green], "
        f"[red]{len(results) - successful} failed[/red]"
    )
