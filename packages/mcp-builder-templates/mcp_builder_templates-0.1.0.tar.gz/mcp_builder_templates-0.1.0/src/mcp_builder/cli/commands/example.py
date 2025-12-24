"""Example command for MCP Builder CLI."""

from pathlib import Path

import typer
from rich.console import Console

console = Console()


def generate_example(
    name: str = typer.Argument(..., help="Example project name"),
    output: Path = typer.Option(Path.cwd(), "--output", "-o", help="Output directory"),
) -> None:
    """
    Generate an example MCP server project.

    Available examples:
    - hello-world: Simple echo server
    - calculator: Basic calculator tools
    - file-manager: File operations
    - web-fetcher: Web scraping example

    Examples:
        # Generate hello world example
        mcp-builder example hello-world

        # Generate in specific directory
        mcp-builder example calculator --output ./examples
    """
    examples = {
        "hello-world": "Simple echo server with greeting tools",
        "calculator": "Calculator with basic arithmetic operations",
        "file-manager": "File system operations and management",
        "web-fetcher": "Web scraping and content extraction",
    }

    if name not in examples:
        console.print(f"[red]✗ Unknown example: {name}[/red]")
        console.print("\n[bold]Available examples:[/bold]")
        for ex_name, desc in examples.items():
            console.print(f"  • {ex_name}: {desc}")
        raise typer.Exit(1)

    console.print(f"[cyan]→ Generating example:[/cyan] {name}")
    console.print(f"[dim]{examples[name]}[/dim]\n")

    # TODO: Implement example generation
    console.print("[yellow]⚠️  Example generation not yet implemented[/yellow]")