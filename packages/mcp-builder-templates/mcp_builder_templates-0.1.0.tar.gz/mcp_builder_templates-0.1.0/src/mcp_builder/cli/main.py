"""Main CLI application for MCP Builder."""

import typer
from rich.console import Console

from mcp_builder.cli.commands import (
    create as create_command,
    init as init_command,
    validate as validate_command,
    list as list_command,
    example as example_command
)


# Create main app
app = typer.Typer(
    name="mcp-builder",
    help="🚀 Production-grade MCP server project generator",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# Create console
console = Console()

# Add commands

# create command
app.command(
    name="create",
    help="Create a new MCP server project"
)(create_command.create_project)

# init command
app.command(
    name="init",
    help="Initialize MCP builder in current directory"
)(init_command.init_project)

# validate command
app.command(
    name="validate",
    help="Validate project configuration"
)(validate_command.validate_project)

# list command
app.command(
    name="list",
    help="List available templates and categories"
)(list_command.list_all)

# example command
app.command(
    name="example",
    help="Generate example projects"
)(example_command.generate_example)


@app.command(
    name="version",
    help="Print Version"
)
def version() -> None:
    """Show version information."""
    from mcp_builder import __version__
    console.print(f"[bold cyan]MCP Builder[/bold cyan] version [green]{__version__}[/green]")


@app.callback()
def main_callback(
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output"
    ),
    debug: bool = typer.Option(
        False,
        "--debug", "-d",
        help="Enable debug mode"
    ),
) -> None:
    """
    MCP Builder - Production-grade MCP server project generator.

    Create enterprise-ready Model Context Protocol servers with best practices,
    comprehensive tooling, and modern development standards.
    """
    import logging

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)