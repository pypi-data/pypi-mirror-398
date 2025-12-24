"""Interactive prompts for MCP Builder CLI"""

from pathlib import Path
from typing import Optional

import questionary
from rich.console import Console
from rich.table import Table

from mcp_builder.config import (
    CICDPlatform,
    DeploymentTarget,
    LicenseType,
    ProjectConfig,
    PythonVersion,
    ToolCategory,
)
from mcp_builder.validators import (
    AuthorNameValidator,
    DescriptionValidator,
    EmailValidator,
    ProjectNameValidator,
    validate_directory_available,
)

console = Console()


def get_project_config() -> Optional[ProjectConfig]:
    """
    Interactive prompts to collect project configuration.
    """

    try:
        console.print(
            "[bold cyan]Let's create your MCP server project! 🚀[/bold cyan]\n"
        )
        console.print("[bold]📋 Basic Information[/bold]\n")

        project_name = questionary.text(
            "Project name: ",
            validate=ProjectNameValidator,
            instruction="(lowercase, hyphens allowed, e.g., 'my-mcp-server')",
        ).ask()
        if not project_name:
            return None

        description = questionary.text(
            "Project description: ",
            validate=DescriptionValidator,
            instruction="(what does your MCP server do?)",
        ).ask()
        if not description:
            return None

        author_name = questionary.text(
            "Author name: ",
            validate=AuthorNameValidator,
        ).ask()
        if not author_name:
            return None

        author_email = questionary.text(
            "Author email: ",
            validate=EmailValidator,
        ).ask()
        if not author_email:
            return None

        console.print()
        console.print("[bold]🐍 Python Configuration[/bold]\n")

        python_choice = questionary.select(
            "Python version: ",
            choices=[
                questionary.Choice(
                    "3.13 (Latest)",
                    value=PythonVersion.PY313
                ),
                questionary.Choice(
                    "3.12 (Recommended)",
                    value=PythonVersion.PY312
                ),
                questionary.Choice(
                    "3.11 (Stable)",
                    value=PythonVersion.PY311
                ),
            ],
        ).ask()
        if not python_choice:
            return None

        python_version = (
            python_choice
            if isinstance(python_choice, PythonVersion)
            else PythonVersion(python_choice)
        )

        console.print()
        console.print("[bold]🛠️  MCP Tools & Features[/bold]\n")

        tool_categories_choices = questionary.checkbox(
            "Select tool categories to include: ",
            choices=[
                questionary.Choice(
                    "🤖 GenAI (LLM integrations)",
                    value=ToolCategory.GENAI
                ),
                questionary.Choice(
                    "📚 RAG (Retrieval Augmented Generation)",
                    value=ToolCategory.RAG
                ),
                questionary.Choice(
                    "🌐 Web Scraping",
                    value=ToolCategory.WEB_SCRAPING
                ),
                questionary.Choice(
                    "📊 Data Processing",
                    value=ToolCategory.DATA_PROCESSING
                ),
                questionary.Choice(
                    "📁 File Operations",
                    value=ToolCategory.FILE_OPERATIONS
                ),
                questionary.Choice(
                    "🔌 API Integration",
                    value=ToolCategory.API_INTEGRATION
                ),
                questionary.Choice(
                    "🗄️  Database",
                    value=ToolCategory.DATABASE
                ),
                questionary.Choice(
                    "✨ Custom",
                    value=ToolCategory.CUSTOM
                ),
            ],
            instruction="(Space to select, Enter to confirm)",
        ).ask()
        if tool_categories_choices is None:
            return None

        tool_categories = [
            cat
            if isinstance(cat, ToolCategory)
            else ToolCategory(cat)
            for cat in tool_categories_choices
        ]

        # GenAI providers if GenAI selected
        genai_providers = []
        if ToolCategory.GENAI in tool_categories:
            genai_providers = questionary.checkbox(
                "Select GenAI providers: ",
                choices=[
                    "OpenAI",
                    "Anthropic",
                    "Google (Gemini)",
                    "Cohere",
                    "Mistral",
                    "HuggingFace",
                ],
            ).ask()
            if genai_providers is None:
                return None

        # RAG options if RAG selected
        rag_vector_stores = []
        rag_embedding_models = []
        if ToolCategory.RAG in tool_categories:
            rag_vector_stores = questionary.checkbox(
                "Select vector stores: ",
                choices=[
                    "ChromaDB",
                    "Pinecone",
                    "Weaviate",
                    "Qdrant",
                    "FAISS"
                ],
            ).ask()
            if rag_vector_stores is None:
                return None

            rag_embedding_models = questionary.checkbox(
                "Select embedding models:",
                choices=[
                    "OpenAI",
                    "Sentence Transformers",
                    "Cohere",
                    "HuggingFace"
                ],
            ).ask()
            if rag_embedding_models is None:
                return None

        include_example_tools = questionary.confirm(
            "Include example tool implementations?",
            default=True,
        ).ask()

        include_example_resources = questionary.confirm(
            "Include example resource implementations?",
            default=True,
        ).ask()

        include_example_prompts = questionary.confirm(
            "Include example prompt templates?",
            default=False,
        ).ask()

        console.print()
        console.print("[bold]🔧 Development & Deployment[/bold]\n")

        include_docker = questionary.confirm(
            "Include Docker support?",
            default=True,
        ).ask()

        include_docker_compose = False
        if include_docker:
            include_docker_compose = questionary.confirm(
                "Include Docker Compose?",
                default=False,
            ).ask()

        cicd_choice = questionary.select(
            "CI/CD platform: ",
            choices=[
                questionary.Choice(
                    "GitHub Actions",
                    value=CICDPlatform.GITHUB_ACTIONS
                ),
                questionary.Choice(
                    "GitLab CI",
                    value=CICDPlatform.GITLAB_CI
                ),
                questionary.Choice(
                    "None",
                    value=CICDPlatform.NONE
                ),
            ],
        ).ask()
        if not cicd_choice:
            return None

        cicd_platform = (
            cicd_choice
            if isinstance(cicd_choice, CICDPlatform)
            else CICDPlatform(cicd_choice)
        )

        deployment_choices = questionary.checkbox(
            "Deployment targets: ",
            choices=[
                questionary.Choice(
                    "🐳 Docker",
                    value=DeploymentTarget.DOCKER
                ),
                questionary.Choice(
                    "☸️  Kubernetes",
                    value=DeploymentTarget.KUBERNETES
                ),
                questionary.Choice(
                    "λ AWS Lambda",
                    value=DeploymentTarget.AWS_LAMBDA
                ),
                questionary.Choice(
                    "☁️  Google Cloud Run",
                    value=DeploymentTarget.GOOGLE_CLOUD_RUN
                ),
                questionary.Choice(
                    "⚡ Azure Functions",
                    value=DeploymentTarget.AZURE_FUNCTIONS
                ),
            ],
            instruction="(optional)",
        ).ask()

        deployment_targets = []
        if deployment_choices is not None:
            deployment_targets = [
                dt
                if isinstance(dt, DeploymentTarget)
                else DeploymentTarget(dt)
                for dt in deployment_choices
            ]

        license_choice = questionary.select(
            "License:",
            choices=[
                questionary.Choice(
                    "MIT",
                    value=LicenseType.MIT
                ),
                questionary.Choice(
                    "Apache 2.0",
                    value=LicenseType.APACHE_2
                ),
                questionary.Choice(
                    "BSD 3-Clause",
                    value=LicenseType.BSD_3
                ),
                questionary.Choice(
                    "GPL 3.0",
                    value=LicenseType.GPL_3
                ),
                questionary.Choice(
                    "Proprietary",
                    value=LicenseType.PROPRIETARY
                ),
            ],
        ).ask()
        if not license_choice:
            return None

        license_type = (
            license_choice
            if isinstance(license_choice, LicenseType)
            else LicenseType(license_choice)
        )

        console.print()
        console.print("[bold]⚙️  Advanced Options[/bold]\n")

        include_makefile = questionary.confirm(
            "Include Makefile for common tasks?",
            default=True,
        ).ask()

        include_vscode_settings = questionary.confirm(
            "Include VS Code settings?",
            default=True,
        ).ask()

        include_contributing_guide = questionary.confirm(
            "Include contributing guidelines?",
            default=True,
        ).ask()

        enable_strict_mypy = questionary.confirm(
            "Enable strict type checking (mypy)?",
            default=True,
        ).ask()

        console.print()

        console.print("[bold]📂 Project Location[/bold]\n")
        console.print("[dim]Project will be created at: output_directory / project_name[/dim]\n")

        output_dir_str = questionary.text(
            "Output directory (parent folder):",
            default=".",
            instruction=f"(project will be created at this location / {project_name})",
        ).ask()
        if not output_dir_str:
            return None

        output_dir = Path(output_dir_str).expanduser().resolve()
        project_path = output_dir / project_name

        console.print(f"\n[cyan]→ Project will be created at:[/cyan] [bold]{project_path}[/bold]\n")

        # Validate directory
        is_valid, error = validate_directory_available(output_dir, project_name)
        if not is_valid:
            console.print(f"[red]✗ Error: {error}[/red]")
            retry = questionary.confirm(
                "Try a different location?",
                default=True
            ).ask()
            if retry:
                return get_project_config()
            return None

        # Create config with properly typed enums
        config = ProjectConfig(
            project_name=project_name,
            description=description,
            author_name=author_name,
            author_email=author_email,
            python_version=python_version,
            include_example_tools=include_example_tools,
            include_example_resources=include_example_resources,
            include_example_prompts=include_example_prompts,
            tool_categories=tool_categories,
            include_docker=include_docker,
            include_docker_compose=include_docker_compose,
            cicd_platform=cicd_platform,
            license_type=license_type,
            deployment_targets=deployment_targets,
            include_makefile=include_makefile,
            include_vscode_settings=include_vscode_settings,
            include_contributing_guide=include_contributing_guide,
            enable_strict_mypy=enable_strict_mypy,
            genai_providers=[p.lower() for p in genai_providers],
            rag_vector_stores=[v.lower() for v in rag_vector_stores],
            rag_embedding_models=[e.lower() for e in rag_embedding_models],
            output_dir=output_dir,
        )

        # Final validation
        is_valid, error = config.validate_project_path()
        if not is_valid:
            console.print(f"\n[red]✗ Path validation failed: {error}[/red]")
            return None

        # Show summary
        _show_config_summary(config, project_path)

        confirm = questionary.confirm(
            "Create project with these settings?",
            default=True,
        ).ask()

        if not confirm:
            console.print("[yellow]Project creation cancelled.[/yellow]")
            return None

        return config

    except KeyboardInterrupt:
        console.print("\n[yellow]Project creation cancelled.[/yellow]")
        return None


def _show_config_summary(config: ProjectConfig, project_path: Path) -> None:
    """Display configuration summary table."""
    console.print("\n[bold cyan]📋 Project Summary[/bold cyan]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Project Name", config.project_name)
    table.add_row("Description", config.description)
    table.add_row("Author", f"{config.author_name} <{config.author_email}>")
    table.add_row("Python Version", config.python_version.value)
    table.add_row(
        "Tool Categories",
        ", ".join(
            [tc.value for tc in config.tool_categories]
        ) if config.tool_categories else "Custom only"
    )
    table.add_row("CI/CD", config.cicd_platform.value)
    table.add_row("License", config.license_type.value)
    table.add_row("Output Path", str(project_path))

    console.print(table)
    console.print()
