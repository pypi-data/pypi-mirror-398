"""Output styles management CLI for Claude Code.

Phase 2.5.3: Manage Claude Code output styles.
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
    help="Manage Claude Code output styles.",
    no_args_is_help=True,
)
console = Console()


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class OutputStyle:
    """Represents a Claude Code output style configuration."""

    name: str
    description: str = ""
    tone: str = ""  # formal, casual, technical
    verbosity: str = ""  # concise, balanced, detailed
    format_preferences: list[str] = field(default_factory=list)
    code_style: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {"name": self.name}
        if self.description:
            result["description"] = self.description
        if self.tone:
            result["tone"] = self.tone
        if self.verbosity:
            result["verbosity"] = self.verbosity
        if self.format_preferences:
            result["format_preferences"] = self.format_preferences
        if self.code_style:
            result["code_style"] = self.code_style
        return result


# Built-in style presets
STYLE_PRESETS = {
    "default": OutputStyle(
        name="default",
        description="Balanced output for general use",
        tone="professional",
        verbosity="balanced",
    ),
    "concise": OutputStyle(
        name="concise",
        description="Minimal, direct responses",
        tone="professional",
        verbosity="concise",
        format_preferences=["bullet points", "short paragraphs"],
    ),
    "detailed": OutputStyle(
        name="detailed",
        description="Comprehensive explanations",
        tone="professional",
        verbosity="detailed",
        format_preferences=["full explanations", "examples", "trade-offs"],
    ),
    "academic": OutputStyle(
        name="academic",
        description="Formal academic writing style",
        tone="formal",
        verbosity="detailed",
        format_preferences=["citations", "formal language", "structured arguments"],
    ),
    "teaching": OutputStyle(
        name="teaching",
        description="Educational, student-friendly style",
        tone="casual",
        verbosity="detailed",
        format_preferences=["step-by-step", "examples", "analogies"],
    ),
    "code-review": OutputStyle(
        name="code-review",
        description="Focused on code quality feedback",
        tone="professional",
        verbosity="balanced",
        format_preferences=["bullet points", "code snippets", "severity levels"],
        code_style={"comments": "inline", "suggestions": "diff format"},
    ),
}


def get_styles_dir() -> Path:
    """Get the styles configuration directory."""
    return Path.home() / ".claude" / "styles"


def load_style(name: str) -> OutputStyle | None:
    """Load a style configuration."""
    # Check presets first
    if name in STYLE_PRESETS:
        return STYLE_PRESETS[name]

    # Check custom styles
    styles_dir = get_styles_dir()
    style_file = styles_dir / f"{name}.json"

    if not style_file.exists():
        return None

    try:
        data = json.loads(style_file.read_text())
        return OutputStyle(
            name=name,
            description=data.get("description", ""),
            tone=data.get("tone", ""),
            verbosity=data.get("verbosity", ""),
            format_preferences=data.get("format_preferences", []),
            code_style=data.get("code_style", {}),
        )
    except (json.JSONDecodeError, OSError):
        return None


def save_style(style: OutputStyle) -> bool:
    """Save a custom style configuration."""
    styles_dir = get_styles_dir()
    styles_dir.mkdir(parents=True, exist_ok=True)

    style_file = styles_dir / f"{style.name}.json"
    try:
        style_file.write_text(json.dumps(style.to_dict(), indent=2))
        return True
    except OSError:
        return False


def list_all_styles() -> list[OutputStyle]:
    """List all available styles (presets + custom)."""
    styles = list(STYLE_PRESETS.values())

    # Add custom styles
    styles_dir = get_styles_dir()
    if styles_dir.exists():
        for style_file in styles_dir.glob("*.json"):
            if style_file.stem not in STYLE_PRESETS:
                style = load_style(style_file.stem)
                if style:
                    styles.append(style)

    return sorted(styles, key=lambda s: s.name)


def get_current_style() -> str | None:
    """Get the currently active style from settings."""
    settings_file = Path.home() / ".claude" / "settings.json"
    if settings_file.exists():
        try:
            data = json.loads(settings_file.read_text())
            return data.get("outputStyle")
        except (json.JSONDecodeError, OSError):
            pass
    return None


def set_current_style(style_name: str) -> bool:
    """Set the current output style in settings."""
    settings_file = Path.home() / ".claude" / "settings.json"
    try:
        if settings_file.exists():
            data = json.loads(settings_file.read_text())
        else:
            data = {}

        data["outputStyle"] = style_name
        settings_file.write_text(json.dumps(data, indent=2))
        return True
    except (json.JSONDecodeError, OSError):
        return False


# =============================================================================
# CLI Commands
# =============================================================================


@app.command("list")
def styles_list() -> None:
    """List available output styles."""
    styles = list_all_styles()
    current = get_current_style()

    table = Table(title="Output Styles", border_style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Tone")
    table.add_column("Verbosity")
    table.add_column("Description")
    table.add_column("Active", justify="center")

    for style in styles:
        is_current = "●" if style.name == current else ""
        table.add_row(
            style.name,
            style.tone or "-",
            style.verbosity or "-",
            style.description[:40] + "..." if len(style.description) > 40 else style.description,
            f"[green]{is_current}[/]" if is_current else "",
        )

    console.print(table)
    console.print(f"\n[dim]Current style: {current or 'default'}[/]")


@app.command("show")
def styles_show(
    name: str = typer.Argument(..., help="Style name to show."),
) -> None:
    """Show detailed style configuration."""
    style = load_style(name)
    if not style:
        console.print(f"[red]Style '{name}' not found.[/]")
        raise typer.Exit(1)

    content = []
    content.append(f"[bold]Description:[/] {style.description or 'No description'}")
    content.append(f"[bold]Tone:[/] {style.tone or 'default'}")
    content.append(f"[bold]Verbosity:[/] {style.verbosity or 'balanced'}")

    if style.format_preferences:
        content.append(f"[bold]Format:[/] {', '.join(style.format_preferences)}")

    if style.code_style:
        content.append(f"[bold]Code Style:[/]")
        for key, value in style.code_style.items():
            content.append(f"  {key}: {value}")

    is_preset = name in STYLE_PRESETS
    content.append(f"\n[dim]Type: {'Built-in preset' if is_preset else 'Custom style'}[/]")

    console.print(Panel(
        "\n".join(content),
        title=f"Style: {name}",
        border_style="cyan",
    ))


@app.command("set")
def styles_set(
    name: str = typer.Argument(..., help="Style name to activate."),
) -> None:
    """Set the active output style."""
    style = load_style(name)
    if not style:
        console.print(f"[red]Style '{name}' not found.[/]")
        console.print("Use 'ait styles list' to see available styles.")
        raise typer.Exit(1)

    if set_current_style(name):
        console.print(f"[green]✓[/] Set output style to '{name}'")
        console.print(f"  Tone: {style.tone or 'default'}")
        console.print(f"  Verbosity: {style.verbosity or 'balanced'}")
    else:
        console.print("[red]Failed to set style.[/]")
        raise typer.Exit(1)


@app.command("create")
def styles_create(
    name: str = typer.Argument(..., help="Name for the new style."),
    description: str = typer.Option("", "--desc", "-d", help="Style description."),
    tone: str = typer.Option("professional", "--tone", "-t", help="Tone: formal, professional, casual."),
    verbosity: str = typer.Option("balanced", "--verbosity", "-v", help="Verbosity: concise, balanced, detailed."),
) -> None:
    """Create a custom output style."""
    if name in STYLE_PRESETS:
        console.print(f"[red]Cannot override built-in preset '{name}'.[/]")
        raise typer.Exit(1)

    existing = load_style(name)
    if existing and name not in STYLE_PRESETS:
        console.print(f"[yellow]Style '{name}' already exists. Overwriting.[/]")

    style = OutputStyle(
        name=name,
        description=description,
        tone=tone,
        verbosity=verbosity,
    )

    if save_style(style):
        console.print(f"[green]Created style '{name}'[/]")
        console.print(f"  Location: {get_styles_dir() / f'{name}.json'}")
    else:
        console.print("[red]Failed to save style.[/]")
        raise typer.Exit(1)


@app.command("remove")
def styles_remove(
    name: str = typer.Argument(..., help="Style to remove."),
) -> None:
    """Remove a custom style."""
    if name in STYLE_PRESETS:
        console.print(f"[red]Cannot remove built-in preset '{name}'.[/]")
        raise typer.Exit(1)

    style_file = get_styles_dir() / f"{name}.json"
    if not style_file.exists():
        console.print(f"[red]Custom style '{name}' not found.[/]")
        raise typer.Exit(1)

    try:
        style_file.unlink()
        console.print(f"[green]Removed style '{name}'[/]")

        # Reset if this was the active style
        if get_current_style() == name:
            set_current_style("default")
            console.print("[dim]Reset to default style.[/]")
    except OSError as e:
        console.print(f"[red]Failed to remove style: {e}[/]")
        raise typer.Exit(1)


@app.command("preview")
def styles_preview(
    name: str = typer.Argument(..., help="Style to preview."),
) -> None:
    """Preview how a style affects output."""
    style = load_style(name)
    if not style:
        console.print(f"[red]Style '{name}' not found.[/]")
        raise typer.Exit(1)

    console.print(f"[bold cyan]Preview: {name} style[/]\n")

    # Show example based on style
    if style.verbosity == "concise":
        example = """[bold]Question:[/] How do I create a Python virtual environment?

[bold]Response (concise style):[/]
```bash
python -m venv .venv
source .venv/bin/activate
```"""
    elif style.verbosity == "detailed":
        example = """[bold]Question:[/] How do I create a Python virtual environment?

[bold]Response (detailed style):[/]
A Python virtual environment isolates project dependencies from your system Python.

**Steps:**
1. Create the environment:
   ```bash
   python -m venv .venv
   ```

2. Activate it:
   - macOS/Linux: `source .venv/bin/activate`
   - Windows: `.venv\\Scripts\\activate`

3. Verify: `which python` should show `.venv/bin/python`

**Benefits:** Isolated dependencies, reproducible builds, no system pollution."""
    else:
        example = """[bold]Question:[/] How do I create a Python virtual environment?

[bold]Response (balanced style):[/]
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

This creates an isolated environment for your project's dependencies."""

    console.print(Panel(example, border_style="dim"))
