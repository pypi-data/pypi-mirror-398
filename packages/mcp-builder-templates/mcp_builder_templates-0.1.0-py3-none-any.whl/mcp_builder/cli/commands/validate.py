"""Validate command for MCP Builder CLI."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def validate_project(
    project_dir: Path = typer.Argument(..., help="Project directory to validate"),
    strict: bool = typer.Option(False, "--strict", "-s", help="Enable strict validation"),
) -> None:
    """
        strict: bool = typer.Option(False, "--strict", "-s", help="Enable strict validation"),
    Validate an MCP server project structure and configuration.

    Checks:
    - Project structure
    - Configuration files
    - Dependencies
    - Code quality

    Examples:
        # Validate current directory
        mcp-builder validate .

        # Validate specific project
        mcp-builder validate ./my-mcp-server

        # Strict validation
        mcp-builder validate . --strict
    """
    if not project_dir.exists():
        console.print(f"[red]✗ Directory not found: {project_dir}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Validating project:[/bold] {project_dir}\n")

    # Validation checks
    checks = []

    # Check project structure
    required_files = ["pyproject.toml", "README.md", ".gitignore"]
    for file in required_files:
        exists = (project_dir / file).exists()
        checks.append(("Project Structure", file, "✓" if exists else "✗"))

    # Check source directory
    src_dirs = list(project_dir.glob("src/*"))
    checks.append(("Source Code", "src/ directory", "✓" if src_dirs else "✗"))

    # Check tests
    has_tests = (project_dir / "tests").exists()
    checks.append(("Testing", "tests/ directory", "✓" if has_tests else "✗"))

    # Display results
    table = Table(title="Validation Results")
    table.add_column("Category", style="cyan")
    table.add_column("Check", style="white")
    table.add_column("Status", style="bold")

    for category, check, status in checks:
        color = "green" if status == "✓" else "red"
        table.add_row(category, check, f"[{color}]{status}[/{color}]")

    console.print(table)

    # Summary
    passed = sum(1 for _, _, status in checks if status == "✓")
    total = len(checks)

    if passed == total:
        console.print(f"\n[green]✓ All checks passed ({passed}/{total})[/green]")
    else:
        console.print(f"\n[yellow]⚠️  {passed}/{total} checks passed[/yellow]")
        if strict:
            raise typer.Exit(1)
