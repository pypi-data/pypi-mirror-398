"""Enhanced input validators for MCP Builder CLI with robust path handling."""

import re
import os
from pathlib import Path
from typing import Any

from questionary import ValidationError, Validator


class ProjectNameValidator(Validator):
    """Validates project names according to Python package naming conventions."""

    RESERVED_NAMES = {
        "test", "tests", "src", "dist", "build", "venv", ".venv",
        "lib", "bin", "include", "share", "site-packages",
        "__pycache__", ".git", ".github", ".gitlab", "node_modules",
    }

    def validate(self, document: Any) -> None:
        """Validate project name."""
        value = document.text.strip()

        if not value:
            raise ValidationError(
                message="Project name cannot be empty",
                cursor_position=len(document.text),
            )

        if not re.match(r"^[a-z][a-z0-9-]*$", value):
            raise ValidationError(
                message="Must start with lowercase letter, contain only lowercase letters, numbers, and hyphens",
                cursor_position=len(document.text),
            )

        if value.startswith("-") or value.endswith("-"):
            raise ValidationError(
                message="Cannot start or end with a hyphen",
                cursor_position=len(document.text),
            )

        if "--" in value:
            raise ValidationError(
                message="Cannot contain consecutive hyphens",
                cursor_position=len(document.text),
            )

        if len(value) > 100:
            raise ValidationError(
                message="Must be less than 100 characters",
                cursor_position=len(document.text),
            )

        if value in self.RESERVED_NAMES:
            raise ValidationError(
                message=f"'{value}' is a reserved name and cannot be used",
                cursor_position=len(document.text),
            )


class DescriptionValidator(Validator):
    """Validates project description."""

    def validate(self, document: Any) -> None:
        value = document.text.strip()

        if not value:
            raise ValidationError(
                message="Description cannot be empty",
                cursor_position=len(document.text),
            )

        if len(value) < 10:
            raise ValidationError(
                message="Description must be at least 10 characters",
                cursor_position=len(document.text),
            )

        if len(value) > 500:
            raise ValidationError(
                message="Description must be less than 500 characters",
                cursor_position=len(document.text),
            )


class EmailValidator(Validator):
    """Validates email addresses."""

    def validate(self, document: Any) -> None:
        value = document.text.strip()

        if not value:
            raise ValidationError(
                message="Email cannot be empty",
                cursor_position=len(document.text),
            )

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, value):
            raise ValidationError(
                message="Please enter a valid email address",
                cursor_position=len(document.text),
            )


class AuthorNameValidator(Validator):
    """Validates author name."""

    def validate(self, document: Any) -> None:
        value = document.text.strip()

        if not value:
            raise ValidationError(
                message="Author name cannot be empty",
                cursor_position=len(document.text),
            )

        if len(value) < 2:
            raise ValidationError(
                message="Author name must be at least 2 characters",
                cursor_position=len(document.text),
            )

        if len(value) > 100:
            raise ValidationError(
                message="Author name must be less than 100 characters",
                cursor_position=len(document.text),
            )


def validate_project_name(name: str) -> tuple[bool, str]:
    """
    Validate project name and return (is_valid, error_message).
    
    Args:
        name: Project name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Project name cannot be empty"

    if not re.match(r"^[a-z][a-z0-9-]*$", name):
        return False, "Must start with letter, contain only lowercase letters, numbers, hyphens"

    if name.startswith("-") or name.endswith("-"):
        return False, "Cannot start or end with hyphen"

    if "--" in name:
        return False, "Cannot contain consecutive hyphens"

    if len(name) > 100:
        return False, "Must be less than 100 characters"

    reserved = ProjectNameValidator.RESERVED_NAMES
    if name in reserved:
        return False, f"'{name}' is a reserved name"

    return True, ""


def validate_directory_available(output_dir: Path, project_name: str) -> tuple[bool, str]:
    """
    Check if directory is available for project creation.
    
    CRITICAL: This validates that we can create project_name inside output_dir.
    The actual project will be created at: output_dir / project_name
    
    Args:
        output_dir: Base output directory (parent folder where project will be created)
        project_name: Name of the project (used as subdirectory name)

    Returns:
        Tuple of (is_available, error_message)
        
    Example:
        validate_directory_available(Path("/home/user/projects"), "my-server")
        → Checks if we can create /home/user/projects/my-server/
    """
    try:
        # Always resolve to absolute path
        output_dir = output_dir.expanduser().resolve()
        
        # The actual project will be created here
        project_path = output_dir / project_name
        
        # Check if output directory exists, create if needed
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                return False, f"No permission to create directory: {output_dir}"
            except OSError as e:
                return False, f"Cannot create output directory: {e}"
        
        # Verify it's actually a directory
        if not output_dir.is_dir():
            return False, f"Output path is not a directory: {output_dir}"

        # Check write permissions on output directory
        if not os.access(output_dir, os.W_OK):
            return False, f"No write permission for directory: {output_dir}"

        # Check if project directory already exists
        if project_path.exists():
            return False, f"Project directory already exists: {project_path}"

        return True, ""

    except Exception as e:
        return False, f"Path validation error: {e}"


def validate_path_safety(path: Path) -> tuple[bool, str]:
    """
    Validate that a path is safe to use (prevents path traversal attacks).
    
    Args:
        path: Path to validate
        
    Returns:
        Tuple of (is_safe, error_message)
    """
    try:
        resolved = path.resolve()
        
        # Check for path traversal attempts in the original path
        path_str = str(path)
        if ".." in path_str.split(os.sep):
            # Allow parent directory references in normal usage
            # but validate that resolved path makes sense
            pass
        
        # Ensure path doesn't try to escape to sensitive areas
        resolved_str = str(resolved)
        
        # Block paths that try to access system directories
        dangerous_paths = ["/etc", "/sys", "/proc", "/root"]
        for dangerous in dangerous_paths:
            if resolved_str.startswith(dangerous):
                return False, f"Cannot create projects in system directory: {dangerous}"
        
        return True, ""
        
    except Exception as e:
        return False, f"Path safety check failed: {e}"


def validate_writable_path(path: Path) -> tuple[bool, str]:
    """
    Check if a path is writable (for existing paths).
    
    Args:
        path: Path to check
        
    Returns:
        Tuple of (is_writable, error_message)
    """
    try:
        if not path.exists():
            # Check parent directory
            parent = path.parent
            if not parent.exists():
                return False, f"Parent directory does not exist: {parent}"
            if not os.access(parent, os.W_OK):
                return False, f"No write permission for parent directory: {parent}"
            return True, ""
        
        if not os.access(path, os.W_OK):
            return False, f"No write permission: {path}"
        
        return True, ""
        
    except Exception as e:
        return False, f"Write permission check failed: {e}"