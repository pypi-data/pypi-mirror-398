"""Grep tool

Fast content search tool using regular expressions.
"""

import os
import re
from dataclasses import asdict, dataclass
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
class GrepMatch:
    """Single grep match result"""

    file_path: str
    line_number: int
    line: str
    match_start: int
    match_end: int


@dataclass
class GrepResult:
    """Grep search result"""

    pattern: str
    search_path: str
    include_pattern: Optional[str] = None
    files_searched: int = 0
    files_with_matches: Optional[int] = None
    matches: List[Dict[str, Any]] = None
    matches_by_file: Optional[Dict[str, List[Dict[str, Any]]]] = None
    total_matches: int = 0
    summary: Optional[str] = None
    truncated: Optional[bool] = None
    message: Optional[str] = None


# Common skip patterns
SKIP_PATTERNS = [
    re.compile(r"node_modules"),
    re.compile(r"\.git"),
    re.compile(r"\.vscode"),
    re.compile(r"dist"),
    re.compile(r"build"),
    re.compile(r"coverage"),
    re.compile(r"\.nyc_output"),
    re.compile(r"\.next"),
    re.compile(r"\.cache"),
    re.compile(r"\.DS_Store"),
    re.compile(r"Thumbs\.db"),
    re.compile(r"\.log$"),
    re.compile(r"\.tmp$"),
    re.compile(r"\.temp$"),
]

# Text file extensions
TEXT_EXTENSIONS = {
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".json",
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".sass",
    ".py",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".php",
    ".rb",
    ".go",
    ".rs",
    ".swift",
    ".kt",
    ".scala",
    ".clj",
    ".hs",
    ".elm",
    ".ml",
    ".f",
    ".txt",
    ".md",
    ".rst",
    ".asciidoc",
    ".xml",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".properties",
    ".env",
    ".gitignore",
    ".gitattributes",
    ".dockerfile",
    ".makefile",
    ".sh",
    ".bat",
    ".ps1",
    ".sql",
    ".graphql",
    ".vue",
    ".svelte",
    ".astro",
    ".prisma",
    ".proto",
}


def matches_include_pattern(file_path: str, include_pattern: Optional[str]) -> bool:
    """Check if a file path matches the include pattern

    Args:
        file_path: File path to check
        include_pattern: Glob pattern to match

    Returns:
        True if matches or no pattern specified
    """
    if not include_pattern:
        return True

    # Convert glob pattern to regex (simplified)
    regex_pattern = include_pattern
    # Escape special regex chars except glob chars (but not backslash to avoid double-escaping)
    for char in [".", "+", "^", "$", "{", "}", "(", ")", "|", "[", "]"]:
        regex_pattern = regex_pattern.replace(char, f"\\{char}")

    # Handle glob patterns
    regex_pattern = regex_pattern.replace("**/", "###DOUBLESTAR###")
    regex_pattern = regex_pattern.replace("**", "###DOUBLESTAR###")
    regex_pattern = regex_pattern.replace("*", "[^/]*")  # * becomes [^/]*
    regex_pattern = regex_pattern.replace("###DOUBLESTAR###", ".*")  # ** becomes .*
    regex_pattern = regex_pattern.replace("?", "[^/]")  # ? becomes [^/]

    regex = re.compile(f"^{regex_pattern}$")
    return bool(regex.match(file_path))


def should_skip_file(file_path: str) -> bool:
    """Check if a file should be skipped based on common patterns

    Args:
        file_path: File path to check

    Returns:
        True if should skip
    """
    return any(pattern.search(file_path) for pattern in SKIP_PATTERNS)


def is_text_file(file_path: str) -> bool:
    """Simple check if file is likely a text file

    Args:
        file_path: File path to check

    Returns:
        True if likely a text file
    """
    ext = Path(file_path).suffix.lower()
    return ext in TEXT_EXTENSIONS or not ext  # Include extensionless files


async def find_files_to_search(
    context: ExecutionContext, dir_path: str, include_pattern: Optional[str] = None, max_files: int = 1000
) -> List[str]:
    """Recursively find files to search

    Args:
        context: Execution context
        dir_path: Directory path to search
        include_pattern: File pattern to include
        max_files: Maximum number of files to find

    Returns:
        List of file paths to search
    """
    files: List[str] = []

    async def scan_directory(current_path: str) -> None:
        if len(files) >= max_files:
            return

        try:
            entries = await context.fs_operator.readdir(current_path, with_file_types=True)

            for entry in entries:
                if len(files) >= max_files:
                    break

                # Get entry name
                if hasattr(entry, "name"):
                    entry_name = entry.name
                else:
                    entry_name = str(entry)

                full_path = os.path.join(current_path, entry_name)
                relative_path = os.path.relpath(full_path, dir_path)

                # Skip common directories and files
                if should_skip_file(relative_path):
                    continue

                # Check if directory or file
                if hasattr(entry, "is_dir"):
                    is_dir = entry.is_dir()
                else:
                    # Fallback: check if path is directory
                    is_dir = await context.fs_operator.exists(full_path)
                    if is_dir:
                        stat = await context.fs_operator.stat(full_path)
                        is_dir = hasattr(stat, "st_mode") and os.path.stat.S_ISDIR(stat.st_mode)

                if is_dir:
                    await scan_directory(full_path)
                else:
                    # Check if file matches include pattern
                    if matches_include_pattern(relative_path, include_pattern):
                        # Only include text files (basic check)
                        if is_text_file(full_path):
                            files.append(full_path)
        except Exception:
            # Ignore permission errors and continue
            pass

    await scan_directory(dir_path)
    return files


async def search_in_file(
    context: ExecutionContext, file_path: str, regex: re.Pattern, max_matches: int
) -> List[GrepMatch]:
    """Search for pattern in a single file

    Args:
        context: Execution context
        file_path: File path to search
        regex: Compiled regex pattern
        max_matches: Maximum matches to find

    Returns:
        List of grep matches
    """
    matches: List[GrepMatch] = []

    try:
        content = await context.fs_operator.read_file(file_path, encoding="utf-8")
        lines = content.split("\n")

        for line_index, line in enumerate(lines):
            if len(matches) >= max_matches:
                break

            # Find all matches in the line
            for match in regex.finditer(line):
                matches.append(
                    GrepMatch(
                        file_path=file_path,
                        line_number=line_index + 1,
                        line=line,
                        match_start=match.start(),
                        match_end=match.end(),
                    )
                )

                if len(matches) >= max_matches:
                    break
    except Exception:
        # Ignore files that can't be read (binary files, permission issues, etc.)
        pass

    return matches


async def _grep_impl(
    context: ExecutionContext,
    pattern: str,
    path: Optional[str] = None,
    include: Optional[str] = None,
    case_sensitive: bool = False,
    max_files: int = 1000,
    max_matches: int = 100,
) -> ToolResult:
    """Internal implementation of grep functionality."""
    try:
        search_path = path or "."

        # Pattern validation (test if it's a valid regex)
        try:
            re.compile(pattern)
        except re.error as error:
            return handle_tool_error(
                f"Invalid regular expression pattern: {str(error)}", "Pattern validation", "validation"
            )

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

        # Create regex pattern
        regex_flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, regex_flags)

        # Find files to search
        files_to_search = await find_files_to_search(context, absolute_path, include, max_files)

        if len(files_to_search) == 0:
            message = f"No files found to search in {search_path}"
            if include:
                message += f" matching {include}"

            result_data = GrepResult(
                pattern=pattern,
                search_path=search_path,
                include_pattern=include,
                files_searched=0,
                matches=[],
                total_matches=0,
                message=message,
            )
            return create_success_response(asdict(result_data))

        # Search in files
        all_matches: List[GrepMatch] = []
        files_searched = 0
        files_with_matches = 0

        for file in files_to_search:
            if len(all_matches) >= max_matches:
                break

            file_matches = await search_in_file(context, file, regex, max_matches - len(all_matches))

            if len(file_matches) > 0:
                # Convert absolute paths to relative paths for output
                relative_path = os.path.relpath(file, absolute_path)
                for match in file_matches:
                    match.file_path = relative_path

                all_matches.extend(file_matches)
                files_with_matches += 1

            files_searched += 1

        # Format results
        summary = f'Found {len(all_matches)} match(es) for "{pattern}" in {files_with_matches} file(s)'
        if files_searched < len(files_to_search):
            summary += f" (searched {files_searched}/{len(files_to_search)} files)"

        # Group matches by file for better readability
        matches_by_file: Dict[str, List[Dict[str, Any]]] = {}
        for match in all_matches:
            if match.file_path not in matches_by_file:
                matches_by_file[match.file_path] = []
            matches_by_file[match.file_path].append(asdict(match))

        result_data = GrepResult(
            pattern=pattern,
            search_path=search_path,
            include_pattern=include,
            files_searched=files_searched,
            files_with_matches=files_with_matches,
            matches=[asdict(m) for m in all_matches],
            matches_by_file=matches_by_file,
            total_matches=len(all_matches),
            summary=summary,
            truncated=len(all_matches) >= max_matches,
        )
        return create_success_response(asdict(result_data))
    except Exception as error:
        return handle_tool_error(error, "Grep tool execution", "execution")


class GrepToolInput(BaseModel):
    """Input schema for grep tool."""

    pattern: str = Field(description="Regular expression pattern to search for")
    path: str = Field(
        default=".",
        description="Directory to search in (relative to workspace root, or absolute path within workspace). Defaults to workspace root.",
    )
    include: Optional[str] = Field(
        None, description="File pattern to include (e.g., '*.js', '*.{ts,tsx}', 'src/**/*.ts')"
    )
    case_sensitive: bool = Field(default=False, description="Whether the search should be case-sensitive")
    max_files: int = Field(default=1000, description="Maximum number of files to search")
    max_matches: int = Field(default=100, description="Maximum number of matches to return")


def create_grep_tool(context: ExecutionContext) -> DynamicTool:
    """Create a grep tool with the given context.

    Args:
        context: Execution context containing working directory and file operator

    Returns:
        DynamicTool instance that extends BaseTool
    """

    async def grep_tool_func(input_data: Dict, ctx: Optional[Dict] = None) -> ToolResult:
        """Search for patterns in files."""
        pattern = input_data.get("pattern")
        path = input_data.get("path", ".")
        include = input_data.get("include")
        case_sensitive = input_data.get("case_sensitive", False)
        max_files = input_data.get("max_files", 1000)
        max_matches = input_data.get("max_matches", 100)

        return await _grep_impl(context, pattern, path, include, case_sensitive, max_files, max_matches)

    return tool(
        func=grep_tool_func,
        name="Grep",
        description="Search for patterns in files using regular expressions. Efficient for finding specific text patterns across multiple files.",
        schema=GrepToolInput,
        get_display=lambda name, input_data: f"> Using {name} to search for pattern: {input_data.get('pattern', '')}",
    )
