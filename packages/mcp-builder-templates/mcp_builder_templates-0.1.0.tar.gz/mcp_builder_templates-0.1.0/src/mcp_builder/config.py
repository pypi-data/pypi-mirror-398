"""Enhanced configuration models with FIXED enum handling."""

from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class PythonVersion(str, Enum):
    """Supported Python versions."""
    PY311 = "3.11"
    PY312 = "3.12"
    PY313 = "3.13"


class CICDPlatform(str, Enum):
    """Supported CI/CD platforms."""
    GITHUB_ACTIONS = "github-actions"
    GITLAB_CI = "gitlab-ci"
    NONE = "none"


class LicenseType(str, Enum):
    """Supported license types."""
    MIT = "mit"
    APACHE_2 = "apache-2.0"
    BSD_3 = "bsd-3-clause"
    GPL_3 = "gpl-3.0"
    PROPRIETARY = "proprietary"


class ToolCategory(str, Enum):
    """MCP tool categories."""
    GENAI = "genai"
    RAG = "rag"
    WEB_SCRAPING = "web-scraping"
    DATA_PROCESSING = "data-processing"
    FILE_OPERATIONS = "file-operations"
    API_INTEGRATION = "api-integration"
    DATABASE = "database"
    CUSTOM = "custom"


class DeploymentTarget(str, Enum):
    """Deployment targets."""
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS_LAMBDA = "aws-lambda"
    GOOGLE_CLOUD_RUN = "google-cloud-run"
    AZURE_FUNCTIONS = "azure-functions"
    NONE = "none"


class ProjectConfig(BaseModel):
    """
    Main project configuration with enhanced path handling.
    
    Path Structure:
        output_dir: Parent directory where project will be created (e.g., /home/user/projects)
        project_slug: Project name/folder name (e.g., my-mcp-server)
        project_path: Full path = output_dir / project_slug (e.g., /home/user/projects/my-mcp-server)
    """

    # Basic metadata
    project_name: Annotated[
        str,
        Field(
            min_length=1,
            max_length=100,
            pattern=r"^[a-z][a-z0-9-]*$",
            description="Project name (lowercase, hyphens allowed)",
        ),
    ]
    project_slug: str = ""
    description: Annotated[str, Field(min_length=10, max_length=500)]
    author_name: Annotated[str, Field(min_length=1, max_length=100)]
    author_email: EmailStr
    python_version: PythonVersion = PythonVersion.PY312

    # Features
    include_example_tools: bool = True
    include_example_resources: bool = True
    include_example_prompts: bool = True
    tool_categories: list[ToolCategory] = Field(default_factory=list)

    # Development tools
    include_docker: bool = True
    include_docker_compose: bool = False
    cicd_platform: CICDPlatform = CICDPlatform.GITHUB_ACTIONS
    license_type: LicenseType = LicenseType.MIT

    # Deployment
    deployment_targets: list[DeploymentTarget] = Field(default_factory=list)

    # Advanced options
    include_makefile: bool = True
    include_vscode_settings: bool = True
    include_contributing_guide: bool = True
    include_code_of_conduct: bool = True
    use_src_layout: bool = True
    enable_strict_mypy: bool = True

    # GenAI specific
    genai_providers: list[str] = Field(default_factory=list)
    include_prompt_templates: bool = False

    # RAG specific
    rag_vector_stores: list[str] = Field(default_factory=list)
    rag_embedding_models: list[str] = Field(default_factory=list)

    # Output directory
    output_dir: Path = Field(default_factory=lambda: Path.cwd())


    model_config = {
        "use_enum_values": False,
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
    }

    @field_validator("output_dir", mode="before")
    @classmethod
    def resolve_output_dir(cls, v: Path | str) -> Path:
        """Resolve output directory to absolute path."""
        path = Path(v) if isinstance(v, str) else v
        return path.expanduser().resolve()

    @field_validator("project_slug", mode="before")
    @classmethod
    def generate_project_slug(cls, v: str, info) -> str:
        """Generate project slug from project name if not provided."""
        # If project_slug is empty, use project_name
        if not v:
            project_name = info.data.get("project_name", "")
            if project_name:
                # Already normalized, just use it
                return project_name.lower().replace(" ", "-").replace("_", "-")
        return v if v else ""

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        """Validate project name follows conventions."""
        if not v.islower():
            raise ValueError("Project name must be lowercase")
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Project name cannot start or end with hyphen")
        if "__" in v or "--" in v:
            raise ValueError("Project name cannot contain consecutive special characters")
        return v

    @field_validator("python_version", mode="before")
    @classmethod
    def validate_python_version(cls, v) -> PythonVersion:
        """Ensure python_version is enum."""
        if isinstance(v, PythonVersion):
            return v
        if isinstance(v, str):
            return PythonVersion(v)
        raise ValueError(f"Invalid python version: {v}")

    @field_validator("cicd_platform", mode="before")
    @classmethod
    def validate_cicd_platform(cls, v) -> CICDPlatform:
        """Ensure cicd_platform is enum."""
        if isinstance(v, CICDPlatform):
            return v
        if isinstance(v, str):
            return CICDPlatform(v)
        raise ValueError(f"Invalid CI/CD platform: {v}")

    @field_validator("license_type", mode="before")
    @classmethod
    def validate_license_type(cls, v) -> LicenseType:
        """Ensure license_type is enum."""
        if isinstance(v, LicenseType):
            return v
        if isinstance(v, str):
            return LicenseType(v)
        raise ValueError(f"Invalid license type: {v}")

    @field_validator("tool_categories", mode="before")
    @classmethod
    def validate_tool_categories(cls, v) -> list[ToolCategory]:
        """Ensure tool_categories are enums."""
        if not v:
            return [ToolCategory.CUSTOM]

        result = []
        for item in v:
            if isinstance(item, ToolCategory):
                result.append(item)
            elif isinstance(item, str):
                result.append(ToolCategory(item))
            else:
                raise ValueError(f"Invalid tool category: {item}")

        return result if result else [ToolCategory.CUSTOM]

    @field_validator("deployment_targets", mode="before")
    @classmethod
    def validate_deployment_targets(cls, v) -> list[DeploymentTarget]:
        """Ensure deployment_targets are enums."""
        if not v:
            return []

        result = []
        for item in v:
            if isinstance(item, DeploymentTarget):
                result.append(item)
            elif isinstance(item, str):
                result.append(DeploymentTarget(item))
            else:
                raise ValueError(f"Invalid deployment target: {item}")

        return result

    @model_validator(mode="after")
    def validate_paths(self):
        """Validate all path-related configurations."""
        # Ensure output_dir is absolute
        if not self.output_dir.is_absolute():
            self.output_dir = self.output_dir.resolve()
        
        # Ensure project_slug is set
        if not self.project_slug:
            self.project_slug = self.project_name
        
        # Validate project_path is different from output_dir
        project_path = self.get_project_path()
        if project_path == self.output_dir:
            raise ValueError(
                f"Internal error: project_path equals output_dir. "
                f"project_slug='{self.project_slug}' might be empty or invalid."
            )
        
        return self

    def get_python_version_full(self) -> str:
        """Get full Python version string."""
        return f"python{self.python_version.value}"

    def get_package_name(self) -> str:
        """
        Get Python package name (underscore-separated).
        
        Converts project-slug to project_slug for valid Python package name.
        """
        return self.project_slug.replace("-", "_")

    def get_project_path(self) -> Path:
        """
        Get full project path where the project will be created.
        
        Returns: output_dir / project_slug
        
        Example:
            output_dir = /home/user/projects
            project_slug = my-mcp-server
            returns: /home/user/projects/my-mcp-server
        """
        return self.output_dir / self.project_slug
    
    def get_output_dir(self) -> Path:
        """
        Get the base output directory (parent directory).
        
        This is where the project folder will be created.
        """
        return self.output_dir

    def validate_project_path(self) -> tuple[bool, str]:
        """
        Validate that the project path is available and safe.
        
        Performs comprehensive validation:
        1. Path safety check (no traversal attacks)
        2. Directory availability check
        3. Write permission check
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        from mcp_builder.validators import (
            validate_directory_available, 
            validate_path_safety,
            validate_writable_path,
        )
        
        project_path = self.get_project_path()
        
        # Check path safety
        is_safe, safety_error = validate_path_safety(project_path)
        if not is_safe:
            return False, f"Path safety check failed: {safety_error}"
        
        # Check directory availability
        is_available, avail_error = validate_directory_available(
            self.output_dir, 
            self.project_slug
        )
        if not is_available:
            return False, avail_error
        
        # Check write permissions
        is_writable, write_error = validate_writable_path(self.output_dir)
        if not is_writable:
            return False, write_error
        
        return True, ""


class TemplateContext(BaseModel):
    """Context for Jinja2 templates."""

    project: ProjectConfig
    year: int
    mcp_version: str = "1.0.0"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for template rendering."""
        return {
            "project_name": self.project.project_name,
            "project_slug": self.project.project_slug,
            "package_name": self.project.get_package_name(),
            "description": self.project.description,
            "author_name": self.project.author_name,
            "author_email": self.project.author_email,
            "python_version": self.project.python_version.value,
            "python_version_full": self.project.get_python_version_full(),
            "license_type": self.project.license_type.value,
            "year": self.year,
            "mcp_version": self.mcp_version,
            "include_docker": self.project.include_docker,
            "include_docker_compose": self.project.include_docker_compose,
            "cicd_platform": self.project.cicd_platform.value,
            "tool_categories": [cat.value for cat in self.project.tool_categories],
            "deployment_targets": [dt.value for dt in self.project.deployment_targets],
            "genai_providers": self.project.genai_providers,
            "rag_vector_stores": self.project.rag_vector_stores,
            "rag_embedding_models": self.project.rag_embedding_models,
            "include_example_tools": self.project.include_example_tools,
            "include_example_resources": self.project.include_example_resources,
            "include_example_prompts": self.project.include_example_prompts,
            "use_src_layout": self.project.use_src_layout,
            "enable_strict_mypy": self.project.enable_strict_mypy,
            "include_makefile": self.project.include_makefile,
            "include_vscode_settings": self.project.include_vscode_settings,
            "include_contributing_guide": self.project.include_contributing_guide,
        }