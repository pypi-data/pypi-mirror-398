"""File writing tool

Provides file writing functionality, supporting creating new files and overwriting existing files.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .._tools_utils import DynamicTool, tool
from .utils import (
    ExecutionContext,
    ToolResult,
    create_success_response,
    handle_tool_error,
    resolve_workspace_path,
    validate_workspace_path,
)


@dataclass
class FileWriteResult:
    """File write result

    Attributes:
        file_path: File path
        absolute_path: Absolute path
        is_new_file: Whether this is a new file
        lines_written: Number of lines written
        bytes_written: Number of bytes written
    """

    file_path: str
    absolute_path: str
    is_new_file: bool
    lines_written: int
    bytes_written: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "file_path": self.file_path,
            "absolute_path": self.absolute_path,
            "is_new_file": self.is_new_file,
            "lines_written": self.lines_written,
            "bytes_written": self.bytes_written,
        }


async def _write_impl(
    context: ExecutionContext,
    file_path: str = "",
    content: str = "",
    create_dirs: bool = True,
) -> ToolResult:
    """Internal implementation of write functionality."""
    try:
        # Validate workspace path
        path_error = validate_workspace_path(file_path, context)
        if path_error:
            return path_error

        # Resolve absolute path
        absolute_path = resolve_workspace_path(file_path, context)

        if context.message_handler:
            context.message_handler.append(f"\n[write] Writing to file: {file_path}\n")

        # Check if target is a directory
        if await context.fs_operator.exists(absolute_path):
            stats = await context.fs_operator.stat(absolute_path)
            if os.path.stat.S_ISDIR(stats.st_mode):
                return handle_tool_error(
                    f"Target path is a directory, not a file: {file_path}",
                    "Path validation",
                    "validation",
                )

        # Create parent directories if needed
        if create_dirs:
            dir_name = os.path.dirname(absolute_path)
            if not await context.fs_operator.exists(dir_name):
                await context.fs_operator.mkdir(dir_name, parents=True, exist_ok=True)
                if context.message_handler:
                    context.message_handler.append(f"\n[write] Created parent directories for: {file_path}\n")

        # Determine if this is a new file or overwrite
        is_new_file = not await context.fs_operator.exists(absolute_path)

        # Write file
        await context.fs_operator.write_file(absolute_path, content, encoding="utf-8")

        lines = len(content.split("\n"))
        size = len(content.encode("utf-8"))

        if context.message_handler:
            action = "Created" if is_new_file else "Updated"
            context.message_handler.append(f"\n[write] {action} file: {file_path} ({lines} lines, {size} bytes)\n")

        result = FileWriteResult(
            file_path=file_path,
            absolute_path=absolute_path,
            is_new_file=is_new_file,
            lines_written=lines,
            bytes_written=size,
        )

        return create_success_response(result.to_dict())

    except Exception as error:
        error_message = str(error)
        if context.message_handler:
            context.message_handler.append(f"\n[write] Error writing file: {error_message}\n")
        return handle_tool_error(error, "Write tool execution", "execution")


class WriteToolInput(BaseModel):
    """Input schema for write tool."""

    file_path: str = Field(description="Path to the file to write")
    content: str = Field(description="Content to write to the file")
    create_dirs: bool = Field(True, description="Whether to automatically create parent directories (default: true)")


def create_write_tool(context: ExecutionContext) -> DynamicTool:
    """Create a write tool with the given context.

    Args:
        context: ExecutionContext with fs_operator and working_directory

    Returns:
        DynamicTool instance that extends BaseTool
    """

    async def write_tool_func(input_data: Dict, ctx: Optional[Dict] = None) -> ToolResult:
        """Write a file.

        Args:
            input_data: Dictionary with file_path, content, create_dirs
            ctx: Optional execution context

        Returns:
            ToolResult with write operation details
        """
        file_path = input_data.get("file_path", "")
        content = input_data.get("content", "")
        create_dirs = input_data.get("create_dirs", True)

        return await _write_impl(context, file_path, content, create_dirs)

    return tool(
        func=write_tool_func,
        name="WriteTool",
        description="Write files to the local filesystem. This tool will overwrite existing files.",
        schema=WriteToolInput,
        get_display=lambda name, input_data: f"> Using {name} to write file: {input_data.get('file_path', '')}",
    )
