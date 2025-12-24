"""List command for MCP Builder CLI."""

import typer
from rich.console import Console
from rich.table import Table

from mcp_builder.config import ToolCategory, PythonVersion, LicenseType

console = Console()


def list_all(
    categories: bool = typer.Option(
        False,
        "--categories", "-c",
        help="List tool categories"
    ),
    templates: bool = typer.Option(
        False,
        "--templates", "-t",
        help="List available templates"
    ),
    python: bool = typer.Option(
        False,
        "--python", "-p",
        help="List Python versions"
    ),
    licenses: bool = typer.Option(
        False,
        "--licenses", "-l",
        help="List license types"
    ),
) -> None:
    """
    List available templates, categories, and options.

    Examples:
        # List everything
        mcp-builder list

        # List only tool categories
        mcp-builder list --categories

        # List templates
        mcp-builder list --templates
    """
    show_all = not any([categories, templates, python, licenses])

    if show_all or categories:
        _list_tool_categories()

    if show_all or python:
        _list_python_versions()

    if show_all or licenses:
        _list_licenses()

    if show_all or templates:
        _list_templates()


def _list_tool_categories() -> None:
    """List available tool categories."""
    table = Table(title="🛠️  Available Tool Categories")
    table.add_column("Category", style="cyan")
    table.add_column("Description", style="white")

    descriptions = {
        ToolCategory.GENAI: "LLM integrations (OpenAI, Anthropic, etc.)",
        ToolCategory.RAG: "Retrieval Augmented Generation",
        ToolCategory.WEB_SCRAPING: "Web scraping and data extraction",
        ToolCategory.DATA_PROCESSING: "Data transformation and analysis",
        ToolCategory.FILE_OPERATIONS: "File system operations",
        ToolCategory.API_INTEGRATION: "External API integrations",
        ToolCategory.DATABASE: "Database operations",
        ToolCategory.CUSTOM: "Custom tool implementations",
    }

    for category in ToolCategory:
        table.add_row(category.value, descriptions.get(category, ""))

    console.print(table)
    console.print()


def _list_python_versions() -> None:
    """List supported Python versions."""
    table = Table(title="🐍 Supported Python Versions")
    table.add_column("Version", style="cyan")
    table.add_column("Status", style="white")

    for version in PythonVersion:
        status = "✓ Recommended" if version == PythonVersion.PY312 else ""
        table.add_row(version.value, status)

    console.print(table)
    console.print()


def _list_licenses() -> None:
    """List available license types."""
    table = Table(title="📝 Available Licenses")
    table.add_column("License", style="cyan")
    table.add_column("Description", style="white")

    descriptions = {
        LicenseType.MIT: "Permissive, widely used",
        LicenseType.APACHE_2: "Permissive with patent grant",
        LicenseType.BSD_3: "Permissive BSD 3-Clause",
        LicenseType.GPL_3: "Copyleft GPL v3",
        LicenseType.PROPRIETARY: "Proprietary/closed source",
    }

    for license_type in LicenseType:
        table.add_row(license_type.value, descriptions.get(license_type, ""))

    console.print(table)
    console.print()


def _list_templates() -> None:
    """List available project templates."""
    table = Table(title="📋 Available Templates")
    table.add_column("Template", style="cyan")
    table.add_column("Description", style="white")

    templates = {
        "minimal": "Minimal MCP server with custom tools only",
        "standard": "Standard setup with common tools",
        "full": "Full-featured server with all tool categories",
        "ai-agent": "AI agent with GenAI and RAG tools",
        "web-scraper": "Web scraping and data extraction",
        "api-gateway": "API integration and gateway",
    }

    for name, desc in templates.items():
        table.add_row(name, desc)

    console.print(table)
    console.print("\n[dim]Use with: mcp-builder create --template <name>[/dim]\n")
