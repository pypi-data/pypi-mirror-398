"""Utility functions for CLI."""

from rich.console import Console
from rich.panel import Panel

console = Console()


def print_banner() -> None:
    """Print welcome banner."""
    banner = """
    ███╗   ███╗ ██████╗██████╗     ██████╗ ██╗   ██╗██╗██╗     ██████╗ ███████╗██████╗ 
    ████╗ ████║██╔════╝██╔══██╗    ██╔══██╗██║   ██║██║██║     ██╔══██╗██╔════╝██╔══██╗
    ██╔████╔██║██║     ██████╔╝    ██████╔╝██║   ██║██║██║     ██║  ██║█████╗  ██████╔╝
    ██║╚██╔╝██║██║     ██╔═══╝     ██╔══██╗██║   ██║██║██║     ██║  ██║██╔══╝  ██╔══██╗
    ██║ ╚═╝ ██║╚██████╗██║         ██████╔╝╚██████╔╝██║███████╗██████╔╝███████╗██║  ██║
    ╚═╝     ╚═╝ ╚═════╝╚═╝         ╚═════╝  ╚═════╝ ╚═╝╚══════╝╚═════╝ ╚══════╝╚═╝  ╚═╝
    """
    console.print(banner, style="bold cyan")
    console.print(
        Panel(
            "[bold green]Production-grade MCP Server Project Generator[/bold green]\n"
            "Create enterprise-ready Model Context Protocol servers with best practices\n\n"
            "[dim]Version 0.1.0 | MIT License | github.com/KapilDagur/mcp-builder[/dim]",
            style="cyan",
        )
    )
    console.print()


def print_success(message: str, details: dict = None) -> None:
    """Print success message with optional details."""
    console.print(f"[green]✓[/green] {message}")
    if details:
        for key, value in details.items():
            console.print(f"  [cyan]{key}:[/cyan] {value}")


def print_error(message: str, details: dict = None) -> None:
    """Print error message with optional details."""
    console.print(f"[red]✗[/red] {message}")
    if details:
        for key, value in details.items():
            console.print(f"  [yellow]{key}:[/yellow] {value}")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]⚠️[/yellow] {message}")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[cyan]ℹ[/cyan] {message}")