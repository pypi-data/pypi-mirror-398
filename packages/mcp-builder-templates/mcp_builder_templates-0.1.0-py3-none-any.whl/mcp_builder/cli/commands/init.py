"""Init command for MCP Builder CLI."""

from pathlib import Path

import typer
from rich.console import Console

console = Console()


def init_project(
    directory: Path = typer.Argument(
        Path.cwd(),
        help="Directory to initialize (defaults to current directory)"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Force initialization"
    ),
) -> None:
    """
    Initialize MCP builder configuration in an existing directory.

    This creates a .mcp-builder.yaml configuration file for customizing
    the project generation process.

    Examples:
        # Initialize in current directory
        mcp-builder init

        # Initialize in specific directory
        mcp-builder init ./my-project

        # Force overwrite existing config
        mcp-builder init --force
    """
    config_file = directory / ".mcp-builder.yaml"

    if config_file.exists() and not force:
        console.print(f"[yellow]⚠️  Configuration already exists: {config_file}[/yellow]")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(1)

    # Create configuration
    config_content = """# MCP Builder Configuration
# See https://github.com/KapilDagur/mcp-builder for documentation

# Project defaults
project:
  python_version: "3.12"
  license: "MIT"
  include_docker: true
  include_tests: true

# Tool categories
tools:
  - custom

# Development settings
development:
  enable_strict_mypy: true
  include_pre_commit: true
  include_makefile: true
"""

    config_file.write_text(config_content)
    console.print(f"[green]✓[/green] Created configuration: {config_file}")
    console.print("\n[dim]Edit .mcp-builder.yaml to customize your project generation[/dim]")
