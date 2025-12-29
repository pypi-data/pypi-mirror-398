"""Glob tool

Find files and directories matching glob patterns.
"""

import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
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
class GlobFileEntry:
    """File entry from glob search"""

    path: str
    absolute_path: str
    is_directory: bool
    size: int
    modified_time: datetime
    extension: Optional[str] = None


@dataclass
class GlobResult:
    """Glob search result"""

    pattern: str
    search_path: str
    matches: List[Dict[str, Any]]
    total_matches: int
    file_count: int
    directory_count: int
    summary: str
    truncated: bool
    sorted_by_time: bool


def glob_to_regex(pattern: str, case_sensitive: bool = False) -> re.Pattern:
    """Convert glob pattern to regex pattern

    Args:
        pattern: Glob pattern (e.g., "*.js", "src/**/*.ts")
        case_sensitive: Whether to match case-sensitively

    Returns:
        Compiled regex pattern
    """
    # Handle brace expansion like {js,ts,jsx}
    regex_pattern = pattern

    # Handle brace expansion
    brace_regex = re.compile(r"\{([^}]+)\}")

    def replace_braces(match):
        content = match.group(1)
        options = [s.strip() for s in content.split(",")]
        return f"({'|'.join(options)})"

    regex_pattern = brace_regex.sub(replace_braces, regex_pattern)

    # Escape regex special characters except glob chars (but not backslash to avoid double-escaping)
    chars_to_escape = [".", "+", "^", "$", "[", "]"]
    for char in chars_to_escape:
        regex_pattern = regex_pattern.replace(char, f"\\{char}")

    # Handle glob patterns
    regex_pattern = regex_pattern.replace("**/", "###DOUBLESTAR###")
    regex_pattern = regex_pattern.replace("**", "###DOUBLESTAR###")
    regex_pattern = regex_pattern.replace("*", "[^/]*")  # * becomes [^/]*
    regex_pattern = regex_pattern.replace("###DOUBLESTAR###", ".*")  # ** becomes .*
    regex_pattern = regex_pattern.replace("?", "[^/]")  # ? becomes [^/]

    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(f"^{regex_pattern}$", flags)


def should_skip_path(relative_path: str, show_hidden: bool) -> bool:
    """Check if a path should be skipped

    Args:
        relative_path: Relative path to check
        show_hidden: Whether to show hidden files

    Returns:
        True if should skip
    """
    # Skip hidden files unless requested
    if not show_hidden:
        parts = relative_path.split(os.sep)
        if any(part.startswith(".") for part in parts):
            return True

    # Skip common directories that should never be searched
    skip_patterns = [
        re.compile(r"node_modules"),
        re.compile(r"\.git$"),
        re.compile(r"\.svn$"),
        re.compile(r"\.hg$"),
        re.compile(r"\.vscode$"),
        re.compile(r"dist$"),
        re.compile(r"build$"),
        re.compile(r"coverage$"),
        re.compile(r"\.nyc_output$"),
        re.compile(r"\.next$"),
        re.compile(r"\.cache$"),
    ]

    return any(pattern.search(relative_path) for pattern in skip_patterns)


async def find_matches(
    context: ExecutionContext, search_dir: str, pattern: re.Pattern, options: Dict[str, Any]
) -> List[GlobFileEntry]:
    """Recursively find files matching the pattern

    Args:
        context: Execution context
        search_dir: Directory to search
        pattern: Compiled regex pattern
        options: Search options (include_dirs, show_hidden, max_results)

    Returns:
        List of matching file entries
    """
    results: List[GlobFileEntry] = []

    async def scan_directory(current_dir: str) -> None:
        if len(results) >= options["max_results"]:
            return

        try:
            entries = await context.fs_operator.readdir(current_dir, with_file_types=True)

            for entry in entries:
                if len(results) >= options["max_results"]:
                    break

                # Get entry name
                if hasattr(entry, "name"):
                    entry_name = entry.name
                else:
                    entry_name = str(entry)

                full_path = os.path.join(current_dir, entry_name)
                relative_path = os.path.relpath(full_path, search_dir)

                # Skip paths that should be ignored
                if should_skip_path(relative_path, options["show_hidden"]):
                    continue

                # Check if directory
                if hasattr(entry, "is_dir"):
                    is_directory = entry.is_dir()
                else:
                    # Fallback
                    try:
                        stat = await context.fs_operator.stat(full_path)
                        is_directory = hasattr(stat, "st_mode") and os.path.stat.S_ISDIR(stat.st_mode)
                    except:
                        continue

                # Check if this path matches the pattern
                matches = bool(pattern.match(relative_path))

                if matches and (options["include_dirs"] or not is_directory):
                    try:
                        stats = await context.fs_operator.stat(full_path)

                        # Get modification time
                        if hasattr(stats, "st_mtime"):
                            mod_time = datetime.fromtimestamp(stats.st_mtime)
                        else:
                            mod_time = datetime.now()

                        # Get size
                        size = 0 if is_directory else (stats.st_size if hasattr(stats, "st_size") else 0)

                        # Get extension
                        extension = None if is_directory else Path(entry_name).suffix.lstrip(".")
                        if extension == "":
                            extension = None

                        results.append(
                            GlobFileEntry(
                                path=relative_path,
                                absolute_path=full_path,
                                is_directory=is_directory,
                                size=size,
                                modified_time=mod_time,
                                extension=extension,
                            )
                        )
                    except Exception:
                        # Ignore stat errors and continue
                        pass

                # Recursively scan subdirectories
                if is_directory:
                    await scan_directory(full_path)
        except Exception:
            # Ignore permission errors and continue
            pass

    await scan_directory(search_dir)
    return results


def sort_results(results: List[GlobFileEntry], sort_by_time: bool) -> List[GlobFileEntry]:
    """Sort results by modification time or alphabetically

    Args:
        results: List of file entries
        sort_by_time: Whether to sort by modification time

    Returns:
        Sorted list of file entries
    """
    if not sort_by_time:
        # Sort alphabetically with directories first
        def sort_key(entry: GlobFileEntry):
            return (not entry.is_directory, entry.path)

        return sorted(results, key=sort_key)

    # Sort by modification time (newest first) with recent files prioritized
    one_day_ago = datetime.now() - timedelta(days=1)

    def sort_key(entry: GlobFileEntry):
        is_recent = entry.modified_time > one_day_ago
        if is_recent:
            # Recent files: sort by time (newest first)
            return (0, -entry.modified_time.timestamp())
        else:
            # Old files: sort alphabetically
            return (1, entry.path)

    return sorted(results, key=sort_key)


async def _glob_impl(
    context: ExecutionContext,
    pattern: str,
    path: Optional[str] = None,
    case_sensitive: bool = False,
    include_dirs: bool = False,
    show_hidden: bool = False,
    max_results: int = 500,
    sort_by_time: bool = False,
) -> ToolResult:
    """Internal implementation of glob functionality."""
    try:
        search_path = path or "."

        # Validate workspace path
        path_error = validate_workspace_path(search_path, context)
        if path_error:
            return path_error

        # Resolve search directory
        absolute_path = resolve_workspace_path(search_path, context)

        # Check if path exists and is a directory
        dir_error = await validate_directory_exists(context, absolute_path, search_path)
        if dir_error:
            return dir_error

        # Convert glob pattern to regex
        regex = glob_to_regex(pattern, case_sensitive)

        # Find matching files
        matches = await find_matches(
            context,
            absolute_path,
            regex,
            {
                "include_dirs": include_dirs,
                "show_hidden": show_hidden,
                "max_results": max_results,
            },
        )

        # Sort results
        sorted_matches = sort_results(matches, sort_by_time)

        # Create summary
        file_count = sum(1 for m in sorted_matches if not m.is_directory)
        dir_count = sum(1 for m in sorted_matches if m.is_directory)

        summary = f'Found {len(sorted_matches)} match(es) for pattern "{pattern}"'
        if file_count > 0 and dir_count > 0:
            summary += f" ({file_count} files, {dir_count} directories)"
        elif file_count > 0:
            summary += f" ({file_count} files)"
        elif dir_count > 0:
            summary += f" ({dir_count} directories)"

        if len(sorted_matches) >= max_results:
            summary += f" - results truncated at {max_results}"

        result_data = GlobResult(
            pattern=pattern,
            search_path=search_path,
            matches=[asdict(m) for m in sorted_matches],
            total_matches=len(sorted_matches),
            file_count=file_count,
            directory_count=dir_count,
            summary=summary,
            truncated=len(sorted_matches) >= max_results,
            sorted_by_time=sort_by_time,
        )
        return create_success_response(asdict(result_data))
    except Exception as error:
        return handle_tool_error(error, "Glob tool execution", "execution")


class GlobToolInput(BaseModel):
    """Input schema for glob tool."""

    pattern: str = Field(description="Glob pattern to match (e.g., '*.js', '*.{ts,tsx}', '**/*.{js,ts}')")
    path: str = Field(
        default=".",
        description="Directory to search in (relative to workspace root, or absolute path within workspace). Defaults to workspace root.",
    )
    case_sensitive: bool = Field(default=False, description="Whether the search should be case-sensitive")
    include_dirs: bool = Field(default=False, description="Whether to include directories in results")
    show_hidden: bool = Field(
        default=False, description="Whether to include hidden files/directories (starting with .)"
    )
    max_results: int = Field(default=500, description="Maximum number of results to return")
    sort_by_time: bool = Field(default=False, description="Whether to sort results by modification time, newest first")


def create_glob_tool(context: ExecutionContext) -> DynamicTool:
    """Create a glob tool with the given context.

    Args:
        context: Execution context containing working directory and file operator

    Returns:
        DynamicTool instance that extends BaseTool
    """

    async def glob_tool_func(input_data: Dict, ctx: Optional[Dict] = None) -> ToolResult:
        """Find files matching glob patterns."""
        pattern = input_data.get("pattern")
        path = input_data.get("path", ".")
        case_sensitive = input_data.get("case_sensitive", False)
        include_dirs = input_data.get("include_dirs", False)
        show_hidden = input_data.get("show_hidden", False)
        max_results = input_data.get("max_results", 500)
        sort_by_time = input_data.get("sort_by_time", False)

        return await _glob_impl(
            context, pattern, path, case_sensitive, include_dirs, show_hidden, max_results, sort_by_time
        )

    return tool(
        func=glob_tool_func,
        name="Glob",
        description='Find files and directories matching glob patterns (e.g., "*.js", "src/**/*.ts"). Efficient for locating files by name or path structure.',
        schema=GlobToolInput,
        get_display=lambda name, input_data: f"> Using {name} for pattern: {input_data.get('pattern', '')}",
    )
