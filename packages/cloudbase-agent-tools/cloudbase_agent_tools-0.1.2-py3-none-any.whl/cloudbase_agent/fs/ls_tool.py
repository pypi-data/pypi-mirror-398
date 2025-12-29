"""Ls (list directory) tool

Lists files and directories in a given path.
"""

import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .._tools_utils import DynamicTool, tool
from .utils import (
    ExecutionContext,
    ToolResult,
    create_success_response,
    handle_tool_error,
    resolve_workspace_path,
    validate_directory_exists,
    validate_workspace_path,
)


@dataclass
class FileEntry:
    """File or directory entry"""

    name: str
    is_directory: bool
    size: int
    modified_time: datetime
    extension: Optional[str] = None


@dataclass
class LsResult:
    """Ls command result"""

    path: str
    absolute_path: str
    entries: List[Dict[str, Any]]
    total_count: int
    hidden_count: Optional[int] = None
    ignored_count: Optional[int] = None
    directories: Optional[int] = None
    files: Optional[int] = None
    summary: Optional[str] = None
    detailed_listing: Optional[str] = None


def should_ignore(filename: str, patterns: Optional[List[str]]) -> bool:
    """Check if a filename should be ignored based on patterns

    Args:
        filename: Filename to check
        patterns: List of glob patterns to ignore

    Returns:
        True if should ignore
    """
    if not patterns:
        return False

    for pattern in patterns:
        # Convert glob pattern to RegExp (simplified version)
        regex_pattern = pattern
        # Escape special regex chars (but not backslash to avoid double-escaping)
        for char in [".", "+", "^", "$", "{", "}", "(", ")", "|", "[", "]"]:
            regex_pattern = regex_pattern.replace(char, f"\\{char}")

        # Convert glob wildcards
        regex_pattern = regex_pattern.replace("*", ".*")  # * becomes .*
        regex_pattern = regex_pattern.replace("?", ".")  # ? becomes .

        regex = re.compile(f"^{regex_pattern}$")
        if regex.match(filename):
            return True

    return False


def format_file_size(bytes_size: int) -> str:
    """Format file size in human-readable format

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted size string
    """
    if bytes_size == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    k = 1024
    i = 0
    size = float(bytes_size)

    while size >= k and i < len(units) - 1:
        size /= k
        i += 1

    return f"{size:.1f} {units[i]}"


def format_modified_time(date: datetime) -> str:
    """Format modified time in relative format

    Args:
        date: Modification datetime

    Returns:
        Formatted time string
    """
    now = datetime.now()
    diff = now - date
    diff_minutes = diff.total_seconds() / 60
    diff_hours = diff.total_seconds() / 3600
    diff_days = diff.days

    if diff_minutes < 1:
        return "just now"
    if diff_minutes < 60:
        return f"{int(diff_minutes)}m ago"
    if diff_hours < 24:
        return f"{int(diff_hours)}h ago"
    if diff_days < 7:
        return f"{diff_days}d ago"

    return date.strftime("%Y-%m-%d")


async def _ls_impl(
    context: ExecutionContext,
    path: Optional[str] = None,
    ignore: Optional[List[str]] = None,
) -> ToolResult:
    """Internal implementation of ls functionality.

    Note:
        You should generally prefer the Glob and Grep tools, if you know which
        directories to search.
    """
    try:
        target_path = path or "."
        show_hidden = False
        detailed = False

        # Validate workspace path
        path_error = validate_workspace_path(target_path, context)
        if path_error:
            return path_error

        # Resolve target directory
        absolute_path = resolve_workspace_path(target_path, context)

        # Check if path exists and is a directory
        dir_error = await validate_directory_exists(context, absolute_path, target_path)
        if dir_error:
            return dir_error

        # Read directory contents
        files = await context.fs_operator.readdir(absolute_path, with_file_types=True)

        if len(files) == 0:
            result_data = LsResult(path=target_path, absolute_path=absolute_path, entries=[], total_count=0)
            return create_success_response(asdict(result_data))

        entries: List[FileEntry] = []
        hidden_count = 0
        ignored_count = 0

        # Process each file/directory
        for file in files:
            # Get file name
            if hasattr(file, "name"):
                file_name = file.name
            else:
                file_name = str(file)

            # Skip hidden files unless requested
            if not show_hidden and file_name.startswith("."):
                hidden_count += 1
                continue

            # Check ignore patterns
            if should_ignore(file_name, ignore):
                ignored_count += 1
                continue

            full_path = os.path.join(absolute_path, file_name)

            try:
                file_stats = await context.fs_operator.stat(full_path)

                # Check if directory
                if hasattr(file_stats, "st_mode"):
                    is_dir = os.path.stat.S_ISDIR(file_stats.st_mode)
                else:
                    is_dir = False

                # Get size
                size = 0 if is_dir else (file_stats.st_size if hasattr(file_stats, "st_size") else 0)

                # Get modification time
                if hasattr(file_stats, "st_mtime"):
                    mod_time = datetime.fromtimestamp(file_stats.st_mtime)
                else:
                    mod_time = datetime.now()

                # Get extension
                extension = None if is_dir else Path(file_name).suffix.lstrip(".")
                if extension == "":
                    extension = None

                entry = FileEntry(
                    name=file_name, is_directory=is_dir, size=size, modified_time=mod_time, extension=extension
                )

                entries.append(entry)
            except Exception as error:
                # Log error but continue with other files
                print(f"Error accessing {file}: {str(error)}")

        # Sort entries (directories first, then alphabetically)
        def sort_key(entry: FileEntry):
            return (not entry.is_directory, entry.name.lower())

        entries.sort(key=sort_key)

        # Create formatted output
        summary = f"Listed {len(entries)} item(s) in {target_path}"
        if hidden_count > 0:
            summary += f" ({hidden_count} hidden)"
        if ignored_count > 0:
            summary += f" ({ignored_count} ignored)"

        # Create detailed listing if requested
        detailed_listing = None
        if detailed and len(entries) > 0:
            lines = ["\n\nDetailed listing:"]
            for entry in entries:
                type_str = "[DIR]" if entry.is_directory else "[FILE]"
                size_str = "" if entry.is_directory else f" {format_file_size(entry.size)}"
                modified_str = f" {format_modified_time(entry.modified_time)}"
                ext_str = f" .{entry.extension}" if entry.extension else ""
                lines.append(f"{type_str} {entry.name}{size_str}{modified_str}{ext_str}")
            detailed_listing = "\n".join(lines)

        dir_count = sum(1 for e in entries if e.is_directory)
        file_count = sum(1 for e in entries if not e.is_directory)

        result_data = LsResult(
            path=target_path,
            absolute_path=absolute_path,
            entries=[asdict(e) for e in entries],
            total_count=len(entries),
            hidden_count=hidden_count,
            ignored_count=ignored_count,
            directories=dir_count,
            files=file_count,
            summary=summary,
            detailed_listing=detailed_listing,
        )
        return create_success_response(asdict(result_data))
    except Exception as error:
        return handle_tool_error(error, "Ls tool execution", "execution")


class LsToolInput(BaseModel):
    """Input schema for ls tool."""

    path: str = Field(
        default=".", description="The absolute path to the directory to list (must be absolute, not relative)"
    )
    ignore: Optional[List[str]] = Field(None, description="List of glob patterns to ignore (e.g., ['*.log', 'temp*'])")


def create_ls_tool(context: ExecutionContext) -> DynamicTool:
    """Create an ls tool with the given context.

    Args:
        context: Execution context containing working directory and file operator

    Returns:
        DynamicTool instance that extends BaseTool
    """

    async def ls_tool_func(input_data: Dict, ctx: Optional[Dict] = None) -> ToolResult:
        """List files and directories."""
        path = input_data.get("path", ".")
        ignore = input_data.get("ignore")

        return await _ls_impl(context, path, ignore)

    return tool(
        func=ls_tool_func,
        name="Ls",
        description="List files and directories in a given path. The path parameter must be an absolute path, not a relative path. You can optionally provide an array of glob patterns to ignore with the ignore parameter.",
        schema=LsToolInput,
        get_display=lambda name, input_data: f"> Using {name} to list directory: {input_data.get('path', '.')}",
    )
