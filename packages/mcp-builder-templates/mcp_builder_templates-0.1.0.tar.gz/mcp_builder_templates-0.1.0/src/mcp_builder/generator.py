"""FIXED: Enhanced project generation logic for MCP Builder - Critical bug fix."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

from mcp_builder.config import ProjectConfig, TemplateContext
from mcp_builder.exceptions import GenerationError, TemplateError

logger = structlog.get_logger(__name__)


class ProjectGenerator:
    """
    Generates MCP server projects from templates with comprehensive error handling.
    
    CRITICAL FIX: Ensures project_path is always output_dir / project_slug
    """

    def __init__(self, config: ProjectConfig):
        """
        Initialize project generator.
        
        Args:
            config: Project configuration with validated paths
        """
        self.config = config
        # FIX: Use config.get_project_path() which returns output_dir / project_slug
        self.project_path = config.get_project_path()
        self.package_name = config.get_package_name()
        
        # Debug logging to verify paths
        logger.info(
            "generator_initialized",
            project_name=config.project_name,
            project_slug=config.project_slug,
            output_dir=str(config.output_dir),
            project_path=str(self.project_path),
            package_name=self.package_name,
        )
        
        # Verify project_path is correct
        expected_path = config.output_dir / config.project_slug
        if self.project_path != expected_path:
            raise GenerationError(
                "Internal error: project_path mismatch",
                details={
                    "expected": str(expected_path),
                    "actual": str(self.project_path),
                }
            )
        
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        if not template_dir.exists():
            raise GenerationError(
                "Template directory not found",
                details={"template_dir": str(template_dir)}
            )
        
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Add custom filters
        self.env.filters["snake_case"] = self._snake_case
        self.env.filters["pascal_case"] = self._pascal_case
        
        # Template context
        self.context = TemplateContext(
            project=config,
            year=datetime.now().year,
        )

    @staticmethod
    def _snake_case(text: str) -> str:
        """Convert text to snake_case."""
        return text.lower().replace("-", "_").replace(" ", "_")

    @staticmethod
    def _pascal_case(text: str) -> str:
        """Convert text to PascalCase."""
        parts = text.replace("-", " ").replace("_", " ").split()
        return "".join(word.capitalize() for word in parts)

    def generate(self) -> Path:
        """
        Generate the complete project structure.
        
        Returns:
            Path to generated project

        Raises:
            GenerationError: If project generation fails
        """
        logger.info(
            "project_generation_started",
            project_path=str(self.project_path),
            project_name=self.config.project_name,
        )
        
        # Verify project_path is not the same as output_dir
        if self.project_path == self.config.output_dir:
            raise GenerationError(
                "Internal error: project_path equals output_dir. "
                f"Expected: {self.config.output_dir / self.config.project_slug}",
                details={
                    "project_path": str(self.project_path),
                    "output_dir": str(self.config.output_dir),
                    "project_slug": self.config.project_slug,
                }
            )
        
        # Create project directory with proper error handling
        try:
            logger.debug(
                "creating_project_directory",
                path=str(self.project_path),
                exists=self.project_path.exists(),
            )
            
            self.project_path.mkdir(parents=True, exist_ok=False)
            logger.info("project_directory_created", path=str(self.project_path))
            
        except FileExistsError:
            raise GenerationError(
                f"Project directory already exists: {self.project_path}",
                details={"path": str(self.project_path)}
            )
        except PermissionError:
            raise GenerationError(
                f"Permission denied creating directory: {self.project_path}",
                details={"path": str(self.project_path)}
            )
        except Exception as e:
            raise GenerationError(
                f"Failed to create project directory: {e}",
                details={"path": str(self.project_path), "error": str(e)}
            )

        try:
            # Generate all project files
            self._create_directory_structure()
            self._generate_base_files()
            self._generate_source_files()
            self._generate_test_files()

            # Optional components
            if self.config.include_docker:
                self._generate_docker_files()

            self._generate_cicd_files()
            self._generate_documentation()
            self._generate_additional_files()
            
            # Initialize git repository
            self._initialize_git()

            logger.info(
                "project_generation_completed",
                project_path=str(self.project_path),
                files_created=self._count_files(),
            )
            
            return self.project_path

        except Exception as e:
            # Cleanup on failure (atomic operation)
            logger.error(
                "project_generation_failed",
                error=str(e),
                project_path=str(self.project_path),
            )
            
            if self.project_path.exists():
                logger.warning("cleaning_up_failed_project", path=str(self.project_path))
                try:
                    shutil.rmtree(self.project_path)
                    logger.info("cleanup_successful")
                except Exception as cleanup_error:
                    logger.error(
                        "cleanup_failed",
                        error=str(cleanup_error),
                        path=str(self.project_path),
                    )
            
            # Re-raise the original exception
            if isinstance(e, (GenerationError, TemplateError)):
                raise
            raise GenerationError(
                f"Project generation failed: {e}",
                details={"error": str(e), "type": type(e).__name__}
            ) from e

    def _count_files(self) -> int:
        """Count generated files for logging."""
        try:
            return sum(1 for _ in self.project_path.rglob("*") if _.is_file())
        except Exception:
            return 0

    def _create_directory_structure(self) -> None:
        """Create the project directory structure."""
        logger.debug("creating_directory_structure")
        
        dirs = [
            "src" / Path(self.package_name),
            "src" / Path(self.package_name) / "tools",
            "src" / Path(self.package_name) / "resources",
            "src" / Path(self.package_name) / "prompts",
            "tests",
            "tests" "/" "tools",
            "tests" "/" "resources",
            "docs",
        ]
        
        # Add CI/CD directories
        if self.config.cicd_platform == "github-actions":
            dirs.append(Path(".github") / "workflows")
        elif self.config.cicd_platform == "gitlab-ci":
            dirs.append(".gitlab")
        
        # Add VS Code directory
        if self.config.include_vscode_settings:
            dirs.append(".vscode")

        for dir_path in dirs:
            full_path = self.project_path / dir_path
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                logger.debug("directory_created", path=str(dir_path))
            except Exception as e:
                raise GenerationError(
                    f"Failed to create directory: {dir_path}",
                    details={"path": str(full_path), "error": str(e)}
                ) from e

    def _generate_base_files(self) -> None:
        """Generate base project files."""
        logger.debug("generating_base_files")
        
        files = {
            "pyproject.toml": "base/pyproject.toml.j2",
            "README.md": "base/README.md.j2",
            ".gitignore": "base/.gitignore.j2",
            ".pre-commit-config.yaml": "base/.pre-commit-config.yaml.j2",
            "LICENSE": f"licenses/{self.config.license_type.value}.j2",
        }

        if self.config.include_makefile:
            files["Makefile"] = "base/Makefile.j2"

        for filename, template_path in files.items():
            self._render_template(template_path, self.project_path / filename)

    def _generate_source_files(self) -> None:
        """Generate source code files."""
        logger.debug("generating_source_files")
        
        src_path = self.project_path / "src" / self.package_name

        # Core files
        files = {
            "__init__.py": "src/__init__.py.j2",
            "server.py": "src/server.py.j2",
            "config.py": "src/config.py.j2",
            "__main__.py": "src/__main__.py.j2",
        }

        for filename, template_path in files.items():
            self._render_template(template_path, src_path / filename)

        # Generate tool files based on selected categories
        if self.config.include_example_tools:
            self._generate_tool_files(src_path / "tools")

        # Generate __init__.py for subdirectories
        for subdir in ["tools", "resources", "prompts"]:
            init_file = src_path / subdir / "__init__.py"
            init_file.write_text(f'"""{subdir.capitalize()} package."""\n')

    def _generate_tool_files(self, tools_path: Path) -> None:
        """Generate MCP tool implementation files."""
        logger.debug("generating_tool_files")
        
        from mcp_builder.config import ToolCategory

        tool_templates = {
            ToolCategory.GENAI: "tools/genai_tools.py.j2",
            ToolCategory.RAG: "tools/rag_tools.py.j2",
            ToolCategory.WEB_SCRAPING: "tools/web_tools.py.j2",
            ToolCategory.DATA_PROCESSING: "tools/data_tools.py.j2",
            ToolCategory.FILE_OPERATIONS: "tools/file_tools.py.j2",
            ToolCategory.API_INTEGRATION: "tools/api_tools.py.j2",
            ToolCategory.DATABASE: "tools/database_tools.py.j2",
            ToolCategory.CUSTOM: "tools/custom_tools.py.j2",
        }

        for category in self.config.tool_categories:
            if category in tool_templates:
                template_path = tool_templates[category]
                output_file = tools_path / f"{category.replace('-', '_')}_tools.py"
                self._render_template(template_path, output_file)

    def _generate_test_files(self) -> None:
        """Generate test files."""
        logger.debug("generating_test_files")
        
        tests_path = self.project_path / "tests"

        files = {
            "__init__.py": "tests/__init__.py.j2",
            "conftest.py": "tests/conftest.py.j2",
            "test_server.py": "tests/test_server.py.j2",
        }

        for filename, template_path in files.items():
            self._render_template(template_path, tests_path / filename)

    def _generate_docker_files(self) -> None:
        """Generate Docker configuration files."""
        logger.debug("generating_docker_files")
        
        files = {
            "Dockerfile": "docker/Dockerfile.j2",
            ".dockerignore": "docker/.dockerignore.j2",
        }

        if self.config.include_docker_compose:
            files["docker-compose.yml"] = "docker/docker-compose.yml.j2"

        for filename, template_path in files.items():
            self._render_template(template_path, self.project_path / filename)

    def _generate_cicd_files(self) -> None:
        """Generate CI/CD configuration files."""
        logger.debug("generating_cicd_files")
        
        if self.config.cicd_platform == "github-actions":
            workflows_path = self.project_path / ".github" / "workflows"
            self._render_template("github/workflows/ci.yml.j2", workflows_path / "ci.yml")
            
        elif self.config.cicd_platform == "gitlab-ci":
            self._render_template("gitlab/.gitlab-ci.yml.j2", self.project_path / ".gitlab-ci.yml")

    def _generate_documentation(self) -> None:
        """Generate documentation files."""
        logger.debug("generating_documentation")
        
        docs_path = self.project_path / "docs"

        files = {
            "usage.md": "docs/usage.md.j2",
            "api.md": "docs/api.md.j2",
        }

        if self.config.include_contributing_guide:
            files["CONTRIBUTING.md"] = "docs/CONTRIBUTING.md.j2"
            # Also copy to root
            self._render_template(
                "docs/CONTRIBUTING.md.j2",
                self.project_path / "CONTRIBUTING.md"
            )

        for filename, template_path in files.items():
            self._render_template(template_path, docs_path / filename)

    def _generate_additional_files(self) -> None:
        """Generate additional configuration files."""
        logger.debug("generating_additional_files")
        
        # VS Code settings
        if self.config.include_vscode_settings:
            vscode_path = self.project_path / ".vscode"
            self._render_template("vscode/settings.json.j2", vscode_path / "settings.json")
            self._render_template("vscode/extensions.json.j2", vscode_path / "extensions.json")

        # Environment template
        self._render_template("base/.env.example.j2", self.project_path / ".env.example")

    def _render_template(self, template_path: str, output_path: Path) -> None:
        """
        Render a Jinja2 template and write to file.

        Args:
            template_path: Path to template file
            output_path: Output file path

        Raises:
            TemplateError: If template rendering fails
        """
        try:
            template = self.env.get_template(template_path)
            content = template.render(**self.context.to_dict())

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            
            logger.debug("template_rendered", template=template_path, output=str(output_path))
            
        except Exception as e:
            raise TemplateError(
                f"Failed to render template {template_path}: {e}",
                details={
                    "template": template_path,
                    "output": str(output_path),
                    "error": str(e)
                }
            ) from e

    def _initialize_git(self) -> None:
        """Initialize git repository."""
        logger.debug("initializing_git_repository")
        
        import subprocess
        
        try:
            # Initialize repo
            subprocess.run(
                ["git", "init"],
                cwd=self.project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            
            # Add all files
            subprocess.run(
                ["git", "add", "."],
                cwd=self.project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            
            # Initial commit
            subprocess.run(
                ["git", "commit", "-m", "Initial commit from mcp-builder"],
                cwd=self.project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            
            logger.info("git_repository_initialized")
            
        except subprocess.CalledProcessError as e:
            logger.warning("git_initialization_failed", error=e.stderr if hasattr(e, 'stderr') else str(e))
        except FileNotFoundError:
            logger.warning("git_not_found", message="Git not installed or not in PATH")