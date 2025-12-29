"""File system tool utility functions

Provides path validation, resolution and other utility functions.
"""

import os
from dataclasses import dataclass
from typing import Any, Optional

from .._tools_utils import ErrorType, ToolResult, handle_tool_error
from .fs_operator.base_operator import BaseFileOperator


@dataclass
class ExecutionContext:
    """Execution context

    Contains environment information required for tool execution.

    Attributes:
        working_directory: Working directory path
        fs_operator: File system operator instance
        message_handler: Message handler (optional)
    """

    working_directory: str
    fs_operator: BaseFileOperator
    message_handler: Optional[Any] = None


def validate_workspace_path(file_path: str, context: ExecutionContext) -> Optional[ToolResult]:
    """Validate if path is within workspace

    Args:
        file_path: File path to validate
        context: Execution context

    Returns:
        Error result if validation fails, None otherwise
    """
    try:
        # Prevent directory traversal attacks
        if ".." in file_path:
            return handle_tool_error(
                'Path cannot contain ".." for security reasons',
                "Path validation",
                ErrorType.SECURITY,
            )

        normalized_workspace = os.path.normpath(context.working_directory)

        # Handle absolute and relative paths
        if os.path.isabs(file_path):
            resolved_path = os.path.normpath(file_path)
        else:
            resolved_path = os.path.abspath(os.path.join(context.working_directory, file_path))

        # Check if path is within workspace boundaries
        if not resolved_path.startswith(normalized_workspace):
            return handle_tool_error(
                f"Path must be within workspace directory: {file_path}",
                "Security check",
                ErrorType.SECURITY,
            )

        return None  # Validation passed
    except Exception as e:
        return handle_tool_error(e, "Path validation", ErrorType.VALIDATION)


def resolve_workspace_path(file_path: str, context: ExecutionContext) -> str:
    """Safely resolve file path

    Supports both absolute and relative paths.

    Args:
        file_path: File path to resolve
        context: Execution context

    Returns:
        Resolved absolute path
    """
    if os.path.isabs(file_path):
        return os.path.normpath(file_path)
    else:
        return os.path.abspath(os.path.join(context.working_directory, file_path))


def create_success_response(data: Any, execution_time: Optional[float] = None) -> ToolResult:
    """Create success response aligned with top-level ToolResult style.

    Args:
        data: Response data to include in the result
        execution_time: Optional execution time in seconds

    Returns:
        Successful ToolResult instance
    """
    return ToolResult(success=True, data=data, execution_time=execution_time)


# NOTE: handle_tool_error is re-exported from the shared tools.utils module


async def validate_file_exists(context: ExecutionContext, absolute_path: str, file_path: str) -> Optional[ToolResult]:
    """Validate if file exists

    Args:
        context: Execution context
        absolute_path: Absolute path
        file_path: Original file path (for error messages)

    Returns:
        Error result if validation fails, None otherwise
    """
    try:
        if not await context.fs_operator.exists(absolute_path):
            return handle_tool_error(
                f"File not found: {file_path}",
                "File existence check",
                ErrorType.FILE_NOT_FOUND,
            )
        return None
    except Exception as e:
        return handle_tool_error(e, "File existence check", ErrorType.PERMISSION)


async def validate_directory_exists(
    context: ExecutionContext, absolute_path: str, dir_path: str
) -> Optional[ToolResult]:
    """Validate if directory exists

    Args:
        context: Execution context
        absolute_path: Absolute path
        dir_path: Original directory path (for error messages)

    Returns:
        Error result if validation fails, None otherwise
    """
    try:
        if not await context.fs_operator.exists(absolute_path):
            return handle_tool_error(
                f"Directory not found: {dir_path}",
                "Directory existence check",
                ErrorType.FILE_NOT_FOUND,
            )

        stats = await context.fs_operator.stat(absolute_path)
        if not os.path.stat.S_ISDIR(stats.st_mode):
            return handle_tool_error(
                f"Path is not a directory: {dir_path}",
                "Directory validation",
                ErrorType.VALIDATION,
            )

        return None
    except Exception as e:
        return handle_tool_error(e, "Directory validation", ErrorType.PERMISSION)


def validate_required_string(value: Any, param_name: str) -> Optional[ToolResult]:
    """Validate required string parameter

    Args:
        value: Value to validate
        param_name: Parameter name

    Returns:
        Error result if validation fails, None otherwise
    """
    if not value or not isinstance(value, str) or not value.strip():
        return handle_tool_error(
            f"{param_name} is required and must be a non-empty string",
            "Parameter validation",
            ErrorType.VALIDATION,
        )
    return None
