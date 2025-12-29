"""Str-Replace-Editor tool

Text editor tool to view and modify text files.
"""

from enum import Enum
from typing import Dict, Optional, Tuple, Union

from pydantic import BaseModel, Field

from .._tools_utils import DynamicTool, tool
from .edit_tool import FileEditResult, _edit_impl
from .read_tool import FileReadResult, _read_impl
from .utils import ExecutionContext, ToolResult
from .write_tool import FileWriteResult, _write_impl


class EditorCommand(str, Enum):
    """Editor command types"""

    VIEW = "view"
    STR_REPLACE = "str_replace"
    CREATE = "create"
    INSERT = "insert"


# Union type for all possible return types
StrReplaceEditorResult = Union[FileReadResult, FileWriteResult, FileEditResult]


async def _str_replace_editor_impl(
    context: ExecutionContext,
    command: str,
    path: str,
    view_range: Optional[Tuple[int, int]] = None,
    old_str: Optional[str] = None,
    new_str: Optional[str] = None,
    file_text: Optional[str] = None,
    insert_line: Optional[int] = None,
) -> ToolResult:
    """Internal implementation of str_replace_editor functionality."""
    if command == EditorCommand.VIEW:
        # View file or directory
        offset = 0
        limit = None

        if view_range:
            start_line, end_line = view_range
            offset = start_line if start_line > 0 else 0
            if end_line > 0:
                limit = end_line - offset

        return await _read_impl(context, file_path=path, offset=offset, limit=limit)

    elif command == EditorCommand.STR_REPLACE:
        # Replace string in file
        if old_str is None or new_str is None:
            return {"success": False, "error": "str_replace command requires both old_str and new_str parameters"}

        return await _edit_impl(context, file_path=path, old_string=old_str, new_string=new_str)

    elif command == EditorCommand.CREATE:
        # Create new file
        if file_text is None:
            return {"success": False, "error": "create command requires file_text parameter"}

        return await _write_impl(context, file_path=path, content=file_text)

    elif command == EditorCommand.INSERT:
        # Insert text at specific line
        if new_str is None or insert_line is None:
            return {"success": False, "error": "insert command requires both new_str and insert_line parameters"}

        # Read current content
        content = await context.fs_operator.read_file(path, encoding="utf-8")
        lines = content.split("\n")

        # Insert the new string at the specified line
        if insert_line <= len(lines):
            lines.insert(insert_line + 1, new_str)

        # Write back the modified content
        return await _write_impl(context, file_path=path, content="\n".join(lines))

    else:
        return {"success": False, "error": f"Unknown command: {command}"}


class StrReplaceEditorToolInput(BaseModel):
    """Input schema for str_replace_editor tool."""

    command: str = Field(description="Edit type. Must be one of: view, str_replace, create, insert")
    path: str = Field(description="The path to the file or directory")
    view_range: Optional[Tuple[int, int]] = Field(
        None,
        description="Optional array of two integers specifying the start and end line numbers to view. Only applies to view command.",
    )
    old_str: Optional[str] = Field(
        None, description="The text to replace (must match exactly). Required when command is str_replace."
    )
    new_str: Optional[str] = Field(
        None, description="The new text to insert. Required when command is str_replace or insert."
    )
    file_text: Optional[str] = Field(
        None, description="The content to write to the new file. Required when command is create."
    )
    insert_line: Optional[int] = Field(
        None,
        description="The line number after which to insert the text (0 for beginning). Required when command is insert.",
    )


def create_str_replace_editor_tool(context: ExecutionContext) -> DynamicTool:
    """Create a str_replace_editor tool with the given context.

    Args:
        context: Execution context containing working directory and file operator

    Returns:
        DynamicTool instance that extends BaseTool
    """

    async def str_replace_editor_tool_func(input_data: Dict, ctx: Optional[Dict] = None) -> ToolResult:
        """Text editor tool to view and modify text files."""
        command = input_data.get("command")
        path = input_data.get("path")
        view_range = input_data.get("view_range")
        old_str = input_data.get("old_str")
        new_str = input_data.get("new_str")
        file_text = input_data.get("file_text")
        insert_line = input_data.get("insert_line")

        return await _str_replace_editor_impl(
            context, command, path, view_range, old_str, new_str, file_text, insert_line
        )

    return tool(
        func=str_replace_editor_tool_func,
        name="StrReplaceEditor",
        description="Text editor tool to view and modify text files. Supports view, str_replace, create, and insert commands.",
        schema=StrReplaceEditorToolInput,
        get_display=lambda name, input_data: f"> Using {name} with command: {input_data.get('command', '')}",
    )
