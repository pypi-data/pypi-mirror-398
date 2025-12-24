"""Custom exceptions for MCP Builder."""


class MCPBuilderError(Exception):
    """Base exception for MCP Builder."""

    def __init__(
        self,
        message: str,
        details: dict | None = None
    ) -> None:
        """
        Initialize exception.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            details_str = ", ".join(
                f"{k}={v}" 
                for k, v in self.details.items()
            )
            return f"{self.message} ({details_str})"
        return self.message


class ValidationError(MCPBuilderError):
    """Raised when validation fails."""
    pass


class TemplateError(MCPBuilderError):
    """Raised when template rendering fails."""
    pass


class GenerationError(MCPBuilderError):
    """Raised when project generation fails."""
    pass


class ConfigurationError(MCPBuilderError):
    """Raised when configuration is invalid."""
    pass


class FileSystemError(MCPBuilderError):
    """Raised when file system operations fail."""
    pass


class DependencyError(MCPBuilderError):
    """Raised when dependency resolution fails."""
    pass
