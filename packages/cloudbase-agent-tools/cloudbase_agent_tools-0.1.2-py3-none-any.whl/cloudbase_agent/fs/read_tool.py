"""File reading tool

Provides file reading functionality, supporting text, images, PDF and other file types.
"""

import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field

from .._tools_utils import DynamicTool, tool
from .utils import (
    ExecutionContext,
    ToolResult,
    create_success_response,
    handle_tool_error,
    resolve_workspace_path,
    validate_file_exists,
    validate_workspace_path,
)

# Constants
DEFAULT_MAX_LINES = 1000
MAX_LINE_LENGTH = 2000
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


@dataclass
class FileReadResult:
    """File read result

    Attributes:
        content: File content
        file_path: File path
        file_type: File type (text/image/pdf/binary)
        mime_type: MIME type
        line_count: Line count (for text files)
        is_truncated: Whether content was truncated
        lines_shown: Line range shown [start, end]
        size: File size in bytes
    """

    content: str
    file_path: str
    file_type: str
    mime_type: Optional[str] = None
    line_count: Optional[int] = None
    is_truncated: Optional[bool] = None
    lines_shown: Optional[Tuple[int, int]] = None
    size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            "content": self.content,
            "filePath": self.file_path,
            "fileType": self.file_type,
            "size": self.size,
        }
        if self.mime_type:
            result["mimeType"] = self.mime_type
        if self.line_count is not None:
            result["lineCount"] = self.line_count
        if self.is_truncated is not None:
            result["isTruncated"] = self.is_truncated
        if self.lines_shown:
            result["linesShown"] = list(self.lines_shown)
        return result


def detect_file_type(file_path: str) -> str:
    """Detect file type

    Args:
        file_path: File path

    Returns:
        File type: text/image/pdf/binary
    """
    ext = Path(file_path).suffix.lower()
    mime_type, _ = mimetypes.guess_type(file_path)

    # Check for images
    if mime_type and mime_type.startswith("image/"):
        return "image"

    # Check for PDF
    if mime_type == "application/pdf":
        return "pdf"

    # Known binary extensions
    binary_extensions = {
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".zip",
        ".tar",
        ".gz",
        ".7z",
        ".bin",
        ".dat",
        ".class",
        ".jar",
        ".war",
        ".pyc",
        ".pyo",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".odt",
        ".ods",
        ".odp",
        ".wasm",
        ".obj",
        ".o",
        ".a",
        ".lib",
    }

    if ext in binary_extensions:
        return "binary"

    return "text"


async def process_text_file(
    context: ExecutionContext,
    file_path: str,
    start_line: Optional[int] = None,
    line_count: Optional[int] = None,
    end_line: Optional[int] = None,
    encoding: str = "utf-8",
) -> Tuple[str, Dict[str, Any]]:
    """Process text file

    Args:
        context: Execution context
        file_path: File path
        start_line: Starting line number (1-based)
        line_count: Number of lines to read
        end_line: Ending line number (1-based)
        encoding: Character encoding

    Returns:
        (Processed content, metadata dictionary)
    """
    content = await context.fs_operator.read_file(file_path, encoding=encoding)
    lines = content.split("\n")
    original_line_count = len(lines)

    # Process line range
    actual_start_line = max((start_line or 1) - 1, 0)  # Convert to 0-based
    if end_line is None:
        actual_line_count = line_count or min(DEFAULT_MAX_LINES, original_line_count)
        end_line = min(actual_start_line + actual_line_count, original_line_count)

    if end_line < 0:
        end_line += original_line_count + 1

    selected_lines = lines[actual_start_line:end_line]

    # Truncate overly long lines
    lines_were_truncated = False
    processed_lines = []
    for line in selected_lines:
        if len(line) > MAX_LINE_LENGTH:
            lines_were_truncated = True
            processed_lines.append(line[:MAX_LINE_LENGTH] + "... [line truncated]")
        else:
            processed_lines.append(line)

    content_was_truncated = end_line < original_line_count
    is_truncated = content_was_truncated or lines_were_truncated

    processed_content = cat_with_line_numbers("\n".join(processed_lines), actual_start_line)

    # Add truncation notice
    if content_was_truncated:
        processed_content = (
            f"[Content truncated: showing lines {actual_start_line + 1}-{end_line} "
            f"of {original_line_count} total lines]\n\n{processed_content}"
        )
    elif lines_were_truncated:
        processed_content = f"[Some lines truncated due to length (max {MAX_LINE_LENGTH} chars)]\n\n{processed_content}"

    metadata = {
        "line_count": original_line_count,
        "is_truncated": is_truncated,
        "lines_shown": (actual_start_line + 1, end_line),
    }

    return processed_content, metadata


async def process_media_file(context: ExecutionContext, file_path: str, file_type: str) -> Tuple[str, Dict[str, Any]]:
    """Process media file (images, PDF)

    Args:
        context: Execution context
        file_path: File path
        file_type: File type

    Returns:
        (Description content, metadata dictionary)
    """
    buffer = await context.fs_operator.read_file(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"

    file_name = Path(file_path).name
    file_size = len(buffer) / 1024

    content = (
        f"[{file_type.upper()} FILE: {file_name}]\n"
        f"File size: {file_size:.1f} KB\n"
        f"MIME type: {mime_type}\n"
        f"Base64 data available for display."
    )

    metadata = {"mime_type": mime_type}

    return content, metadata


def cat_with_line_numbers(content: str, offset: int = 0) -> str:
    """Add line numbers to content

    Args:
        content: File content
        offset: Line number offset

    Returns:
        Content with line numbers
    """
    lines = content.split("\n")
    numbered_lines = []

    for index, line in enumerate(lines):
        line_number = index + 1 + offset
        # Right-align line number, 6 characters wide, followed by tab
        numbered_lines.append(f"{line_number:6}\t{line}")

    return "\n".join(numbered_lines)


async def _read_impl(
    context: ExecutionContext,
    file_path: str,
    offset: Optional[int] = None,
    end_line: Optional[int] = None,
    limit: Optional[int] = None,
    encoding: str = "utf-8",
) -> ToolResult:
    """Internal implementation of read functionality."""
    start_line = offset
    line_count = limit

    try:
        # Validate workspace path
        path_error = validate_workspace_path(file_path, context)
        if path_error:
            return path_error

        # Resolve file path
        absolute_path = resolve_workspace_path(file_path, context)

        # Check if file exists
        file_error = await validate_file_exists(context, absolute_path, file_path)
        if file_error:
            return file_error

        # Check if path is a directory
        stats = await context.fs_operator.stat(absolute_path)
        if os.path.stat.S_ISDIR(stats.st_mode):
            return handle_tool_error(
                f"Path is a directory, not a file: {file_path}",
                "Path validation",
                "validation",
            )

        # Check file size
        if stats.st_size > MAX_FILE_SIZE_BYTES:
            size_mb = stats.st_size / 1024 / 1024
            return handle_tool_error(
                f"File too large ({size_mb:.1f}MB). Maximum size: {MAX_FILE_SIZE_BYTES / 1024 / 1024}MB",
                "File size check",
                "validation",
            )

        # Detect file type
        file_type = detect_file_type(absolute_path)
        if context.message_handler:
            context.message_handler.append(
                f"\n[read] Reading {file_type} file: {file_path} ({stats.st_size / 1024:.1f} KB)"
            )

        content = ""
        metadata = {}

        # Process based on file type
        if file_type == "text":
            content, metadata = await process_text_file(
                context, absolute_path, start_line, line_count, end_line, encoding
            )
        elif file_type in ("image", "pdf"):
            content, metadata = await process_media_file(context, absolute_path, file_type)
        elif file_type == "binary":
            file_name = Path(absolute_path).name
            file_size = stats.st_size / 1024
            content = (
                f"[BINARY FILE: {file_name}]\nFile size: {file_size:.1f} KB\nCannot display binary content as text."
            )
        else:
            return handle_tool_error(
                f"Unsupported file type: {file_type}",
                "File type detection",
                "validation",
            )

        # Create result
        mime_type, _ = mimetypes.guess_type(absolute_path)
        file_read_result = FileReadResult(
            content=content,
            file_path=file_path,
            file_type=file_type,
            mime_type=mime_type,
            size=stats.st_size,
            **metadata,
        )

        if context.message_handler:
            context.message_handler.append("\n[read] File read completed\n")

        return create_success_response(file_read_result.to_dict())

    except Exception as error:
        error_message = str(error)
        if context.message_handler:
            context.message_handler.append(f"\n[read] Read failed: {error_message}\n")
        return handle_tool_error(error, "Read tool execution", "execution")


class ReadToolInput(BaseModel):
    """Input schema for read tool."""

    file_path: str = Field(description="Path to the file to read")
    offset: Optional[int] = Field(None, description="Starting line number (1-based, optional)")
    end_line: Optional[int] = Field(None, description="Ending line number (1-based, optional)")
    limit: Optional[int] = Field(None, description="Number of lines to read (optional)")
    encoding: str = Field("utf-8", description="Character encoding (default: utf-8)")


def create_read_tool(context: ExecutionContext) -> DynamicTool:
    """Create a read tool with the given context.

    Args:
        context: ExecutionContext with fs_operator and working_directory

    Returns:
        DynamicTool instance that extends BaseTool
    """

    async def read_tool_func(input_data: Dict, ctx: Optional[Dict] = None) -> ToolResult:
        """Read a file.

        Args:
            input_data: Dictionary with file_path, offset, end_line, limit, encoding
            ctx: Optional execution context

        Returns:
            ToolResult with file content and metadata
        """
        file_path = input_data.get("file_path")
        offset = input_data.get("offset")
        end_line = input_data.get("end_line")
        limit = input_data.get("limit")
        encoding = input_data.get("encoding", "utf-8")

        return await _read_impl(context, file_path, offset, end_line, limit, encoding)

    return tool(
        func=read_tool_func,
        name="ReadTool",
        description="Read files from the local filesystem with support for text, images, PDF and other file types",
        schema=ReadToolInput,
        get_display=lambda name, input_data: f"> Using {name} to read file: {input_data.get('file_path', '')}",
    )
