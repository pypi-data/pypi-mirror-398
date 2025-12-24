"""Create command for MCP Builder CLI."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from mcp_builder.cli.prompts import get_project_config
from mcp_builder.cli.utils import print_banner
from mcp_builder.config import ProjectConfig
from mcp_builder.generator import ProjectGenerator

console = Console()


def create_project(
    name: Optional[str] = typer.Option(
        None,
        "--name", "-n",
        help="Project name"
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description", "-d",
        help="Project description"
    ),
    author: Optional[str] = typer.Option(
        None,
        "--author", "-a",
        help="Author name"
    ),
    email: Optional[str] = typer.Option(
        None,
        "--email", "-e",
        help="Author email"
    ),
    output: Path = typer.Option(
        Path.cwd(),
        "--output", "-o",
        help="Output directory"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive", "-i/-I",
        help="Interactive mode"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Overwrite existing project"
    ),
    template: Optional[str] = typer.Option(
        None,
        "--template", "-t",
        help="Use a predefined template"
    ),
) -> None:
    """
    Create a new MCP server project.

    Examples:
        # Interactive mode (recommended)
        mcp-builder create

        # Quick non-interactive creation
        mcp-builder create --name my-server --no-interactive

        # With template
        mcp-builder create --template minimal

        # Force overwrite existing
        mcp-builder create --name my-server --force
    """
    print_banner()

    # Template-based creation
    if template:
        from mcp_builder.templates import get_template_config
        try:
            config = get_template_config(template, output)
            if name:
                config.project_name = name
                config.project_slug = name
        except ValueError as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            raise typer.Exit(1)
    # Interactive mode
    elif interactive or not name:
        config = get_project_config()
        if not config:
            raise typer.Exit(1)
    # Non-interactive mode
    else:
        if not all([name, author, email]):
            console.print("[red]✗ Error: --name, --author, and --email are required in non-interactive mode[/red]")
            raise typer.Exit(1)

        config = ProjectConfig(
            project_name=name,
            description=description or f"{name} MCP Server",
            author_name=author,
            author_email=email,
            output_dir=output,
        )

    # Validate configuration
    is_valid, error = config.validate_project_path()
    if not is_valid and not force:
        console.print(f"[red]✗ Validation failed: {error}[/red]")
        console.print("\n[yellow]💡 Use --force to overwrite existing project[/yellow]")
        raise typer.Exit(1)

    # Handle force flag
    project_path = config.get_project_path()
    if force and project_path.exists():
        import shutil
        console.print(f"[yellow]⚠️  Removing existing project: {project_path}[/yellow]")
        shutil.rmtree(project_path)

    # Generate project
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating project...", total=None)

            generator = ProjectGenerator(config)
            project_path = generator.generate()

            progress.update(task, completed=True)

        # Success message
        console.print()
        console.print(Panel(
            f"[bold green]✨ Project created successfully![/bold green]\n\n"
            f"[cyan]Location:[/cyan] {project_path}\n\n"
            f"[bold]Next steps:[/bold]\n"
            f"  1. cd {config.project_slug}\n"
            f"  2. uv sync\n"
            f"  3. uv run {config.get_package_name()}\n\n"
            f"[dim]Run 'mcp-builder validate {config.project_slug}' to verify setup[/dim]",
            title="🎉 Success",
            style="green",
        ))

    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        if "already exists" in str(e):
            console.print("\n[yellow]💡 Use --force to overwrite existing project[/yellow]")
        raise typer.Exit(1)