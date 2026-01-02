"""CLI commands for documentation validation and testing."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from aiterm.docs import DocsValidator

app = typer.Typer(help="Documentation validation and testing")
console = Console()


@app.command()
def validate_links(
    docs_dir: Optional[Path] = typer.Option(
        None,
        "--docs-dir",
        "-d",
        help="Documentation directory (defaults to ./docs)"
    ),
    external: bool = typer.Option(
        False,
        "--external",
        "-e",
        help="Check external URLs (slow)"
    )
):
    """Validate links in documentation files."""
    console.print(f"[bold cyan]Validating documentation links...[/bold cyan]\n")

    validator = DocsValidator(docs_dir=docs_dir)
    issues = validator.validate_links(check_external=external)

    if not issues:
        console.print("[green]✓ All links are valid![/green]")
        return

    # Display results
    table = Table(title=f"🔗 Link Validation Results ({len(issues)} issues)", show_header=True)
    table.add_column("File", style="cyan")
    table.add_column("Line", justify="right", style="dim")
    table.add_column("Type", style="yellow")
    table.add_column("Issue")

    for issue in issues:
        file_str = str(issue.file.relative_to(Path.cwd()) if issue.file.is_absolute() else issue.file)
        type_map = {
            "broken_internal": "Internal",
            "missing_anchor": "Anchor",
            "broken_external": "External"
        }
        type_str = type_map.get(issue.issue_type, issue.issue_type)

        table.add_row(file_str, str(issue.line), type_str, issue.message)

    console.print(table)
    raise typer.Exit(1)


@app.command()
def test_examples(
    docs_dir: Optional[Path] = typer.Option(
        None,
        "--docs-dir",
        "-d",
        help="Documentation directory (defaults to ./docs)"
    ),
    language: Optional[str] = typer.Option(
        None,
        "--language",
        "-l",
        help="Only test specific language (python, bash)"
    )
):
    """Test code examples in documentation files."""
    console.print(f"[bold cyan]Testing code examples...[/bold cyan]\n")

    validator = DocsValidator(docs_dir=docs_dir)
    languages = [language] if language else ['python', 'bash']
    failures = validator.validate_code_examples(languages=languages)

    all_examples = validator.extract_code_examples()
    tested_examples = [e for e in all_examples if e.language.lower() in languages]

    if not failures:
        console.print(f"[green]✓ All {len(tested_examples)} code example(s) are valid![/green]")
        return

    # Display failures
    table = Table(title=f"💻 Code Example Validation ({len(failures)} failures)", show_header=True)
    table.add_column("File", style="cyan")
    table.add_column("Lines", style="dim")
    table.add_column("Language", style="yellow")
    table.add_column("Error")

    for failure in failures:
        file_str = str(failure['file'].relative_to(Path.cwd()) if failure['file'].is_absolute() else failure['file'])
        lines_str = f"{failure['line_start']}-{failure['line_end']}"
        error = failure['error']
        if len(error) > 80:
            error = error[:77] + "..."

        table.add_row(file_str, lines_str, failure['language'], error)

    console.print(table)
    console.print()
    console.print(f"[red]✗ {len(failures)}/{len(tested_examples)} example(s) failed validation[/red]")
    raise typer.Exit(1)


@app.command()
def validate_all(
    docs_dir: Optional[Path] = typer.Option(
        None,
        "--docs-dir",
        "-d",
        help="Documentation directory (defaults to ./docs)"
    ),
    external: bool = typer.Option(
        False,
        "--external",
        "-e",
        help="Check external URLs (slow)"
    )
):
    """Run all documentation validation checks."""
    console.print("[bold cyan]Running all documentation checks...[/bold cyan]\n")

    validator = DocsValidator(docs_dir=docs_dir)
    result = validator.validate_all(check_external_links=external)

    # Display summary
    table = Table(title="📚 Documentation Validation Summary", show_header=False)
    table.add_column("Check", style="bold")
    table.add_column("Result")

    table.add_row("Files scanned", f"[cyan]{result.total_files}[/cyan]")
    table.add_row("Links checked", f"[cyan]{result.total_links}[/cyan]")
    table.add_row("Code examples", f"[cyan]{result.total_examples}[/cyan]")
    table.add_row("Link issues", f"[red]{len(result.link_issues)}[/red]" if result.link_issues else "[green]0 ✓[/green]")
    table.add_row("Example failures", f"[red]{len(result.example_failures)}[/red]" if result.example_failures else "[green]0 ✓[/green]")

    console.print(table)

    if result.has_issues:
        console.print()
        console.print(f"[red]✗ Found {result.issue_count} issue(s) in documentation[/red]")
        raise typer.Exit(1)
    else:
        console.print()
        console.print("[green]✓ Documentation validation passed! ✨[/green]")


@app.command()
def stats(
    docs_dir: Optional[Path] = typer.Option(
        None,
        "--docs-dir",
        "-d",
        help="Documentation directory (defaults to ./docs)"
    )
):
    """Show documentation statistics."""
    validator = DocsValidator(docs_dir=docs_dir)
    md_files = list(validator.docs_dir.glob("**/*.md"))

    total_lines = 0
    total_links = 0

    for md_file in md_files:
        content = md_file.read_text()
        total_lines += len(content.split('\n'))

        import re
        total_links += len(re.findall(validator.MARKDOWN_LINK_PATTERN, content))

    examples = validator.extract_code_examples()
    examples_by_language = {}
    for example in examples:
        lang = example.language.lower()
        examples_by_language[lang] = examples_by_language.get(lang, 0) + 1

    # Display statistics
    table = Table(title="📊 Documentation Statistics", show_header=False)
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", justify="right")

    table.add_row("Total files", str(len(md_files)))
    table.add_row("Total lines", f"{total_lines:,}")
    table.add_row("Total links", str(total_links))
    table.add_row("Total examples", str(len(examples)))

    console.print(table)

    if examples_by_language:
        console.print()
        lang_table = Table(title="Code Examples by Language", show_header=True)
        lang_table.add_column("Language", style="yellow")
        lang_table.add_column("Count", justify="right")

        for lang, count in sorted(examples_by_language.items(), key=lambda x: -x[1]):
            lang_table.add_row(lang, str(count))

        console.print(lang_table)
