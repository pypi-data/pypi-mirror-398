"""File edit tool

Performs exact string replacements in files with strict occurrence count validation.
"""

import os
import re
from dataclasses import asdict, dataclass
from typing import Dict, Optional

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
class FileEditResult:
    """File edit result data"""

    file_path: str
    absolute_path: str
    is_new_file: bool
    replacements_made: int
    lines_total: int
    bytes_total: int
    old_string_length: int
    new_string_length: int


@dataclass
class CalculatedEdit:
    """Calculated edit operation"""

    current_content: str
    new_content: str
    occurrences: int
    is_new_file: bool
    error: Optional[str] = None


def escape_regex(text: str) -> str:
    """Escape special regex characters

    Args:
        text: Text to escape

    Returns:
        Escaped text
    """
    return re.escape(text)


async def calculate_edit(
    file_path: str, old_string: str, new_string: str, expected_replacements: int, context: ExecutionContext
) -> CalculatedEdit:
    """Calculate the edit operation without executing it

    Args:
        file_path: File path (relative or absolute)
        old_string: Text to find and replace
        new_string: Text to replace with
        expected_replacements: Expected number of replacements
        context: Execution context

    Returns:
        Calculated edit result
    """
    # Resolve absolute path
    absolute_path = resolve_workspace_path(file_path, context)

    # Check if file exists
    try:
        await context.fs_operator.access(absolute_path)
        file_exists = True
    except (FileNotFoundError, PermissionError):
        file_exists = False

    # Handle new file creation
    if not file_exists:
        if old_string == "":
            # Creating a new file
            return CalculatedEdit(current_content="", new_content=new_string, occurrences=1, is_new_file=True)
        else:
            return CalculatedEdit(
                current_content="",
                new_content="",
                occurrences=0,
                is_new_file=False,
                error=f"File not found: {file_path}. Cannot apply edit. Use empty old_string to create a new file.",
            )

    # Read current content
    try:
        current_content = await context.fs_operator.read_file(absolute_path, encoding="utf-8")
        # Normalize line endings to LF
        current_content = current_content.replace("\r\n", "\n")
    except Exception as e:
        return CalculatedEdit(
            current_content="", new_content="", occurrences=0, is_new_file=False, error=f"Failed to read file: {str(e)}"
        )

    # Handle creating file that already exists
    if old_string == "":
        return CalculatedEdit(
            current_content=current_content,
            new_content="",
            occurrences=0,
            is_new_file=False,
            error=f"File already exists, cannot create: {file_path}",
        )

    # Count occurrences using literal string match
    occurrences = current_content.count(old_string)

    # Validate occurrence count
    if occurrences == 0:
        return CalculatedEdit(
            current_content=current_content,
            new_content=current_content,
            occurrences=0,
            is_new_file=False,
            error="Text not found in file. 0 occurrences of old_string found. Ensure exact text match including whitespace and indentation.",
        )

    if occurrences != expected_replacements:
        return CalculatedEdit(
            current_content=current_content,
            new_content=current_content,
            occurrences=occurrences,
            is_new_file=False,
            error=f"Expected {expected_replacements} replacement(s) but found {occurrences} occurrence(s).",
        )

    # Apply replacement
    new_content = current_content.replace(old_string, new_string)

    return CalculatedEdit(
        current_content=current_content, new_content=new_content, occurrences=occurrences, is_new_file=False
    )


class EditToolInput(BaseModel):
    """Input schema for edit tool."""

    file_path: str = Field(description="The absolute path to the file to modify")
    old_string: str = Field(
        description="The exact text to find and replace. Must match exactly including whitespace, indentation, and context. For single replacements, include 2+ lines of context before and after the target text."
    )
    new_string: str = Field(description="The text to replace it with (must be different from old_string)")
    expected_replacements: int = Field(
        default=1, description="The expected number of replacements to perform. Defaults to 1 if not specified."
    )


async def _edit_impl(
    context: ExecutionContext, file_path: str, old_string: str, new_string: str, expected_replacements: int = 1
) -> ToolResult:
    """Internal implementation of edit functionality."""
    try:
        # Validate workspace path
        path_error = validate_workspace_path(file_path, context)
        if path_error:
            return path_error

        # Calculate the edit
        edit_result = await calculate_edit(file_path, old_string, new_string, expected_replacements, context)

        if edit_result.error:
            return handle_tool_error(edit_result.error, "Edit operation", "execution")

        absolute_path = resolve_workspace_path(file_path, context)

        # Create parent directories if needed (for new files)
        if edit_result.is_new_file:
            dir_name = os.path.dirname(absolute_path)
            try:
                await context.fs_operator.access(dir_name)
            except (FileNotFoundError, PermissionError):
                await context.fs_operator.mkdir(dir_name, parents=True, exist_ok=True)
                print(f"Created parent directories for: {file_path}")

        # Write the updated content
        await context.fs_operator.write_file(absolute_path, edit_result.new_content)

        new_lines = len(edit_result.new_content.split("\n"))
        new_size = len(edit_result.new_content.encode("utf-8"))

        result_data = FileEditResult(
            file_path=file_path,
            absolute_path=absolute_path,
            is_new_file=edit_result.is_new_file,
            replacements_made=edit_result.occurrences,
            lines_total=new_lines,
            bytes_total=new_size,
            old_string_length=len(old_string),
            new_string_length=len(new_string),
        )
        return create_success_response(asdict(result_data))
    except Exception as error:
        return handle_tool_error(error, "Edit tool execution", "execution")


def create_edit_tool(context: ExecutionContext) -> DynamicTool:
    """Create an edit tool with the given context.

    Args:
        context: Execution context containing working directory and file operator

    Returns:
        DynamicTool instance that extends BaseTool
    """

    async def edit_tool_func(input_data: Dict, ctx: Optional[Dict] = None) -> ToolResult:
        """Edit a file with exact string replacement."""
        file_path = input_data.get("file_path")
        old_string = input_data.get("old_string")
        new_string = input_data.get("new_string")
        expected_replacements = input_data.get("expected_replacements", 1)

        return await _edit_impl(context, file_path, old_string, new_string, expected_replacements)

    return tool(
        func=edit_tool_func,
        name="Edit",
        description="Performs exact string replacements in files with strict occurrence count validation.\n\nUsage:\n- When editing text from Read tool output, ensure you preserve the exact indentation (tabs/spaces) as it appears AFTER the line number prefix. The line number prefix format is: spaces + line number + tab. Everything after that tab is the actual file content to match. Never include any part of the line number prefix in the old_string or new_string.\n- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.",
        schema=EditToolInput,
        get_display=lambda name, input_data: f"> Using {name} to edit file: {input_data.get('file_path', '')}",
    )
