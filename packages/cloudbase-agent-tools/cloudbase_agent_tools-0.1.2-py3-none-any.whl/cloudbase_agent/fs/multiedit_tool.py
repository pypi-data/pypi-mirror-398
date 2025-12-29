"""Multi-edit tool

Perform multiple find-and-replace operations on a single file in sequence.
"""

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

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


@dataclass
class SingleEdit:
    """Single edit operation"""

    old_string: str
    new_string: str
    expected_replacements: int = 1


@dataclass
class EditResult:
    """Result of a single edit operation"""

    edit: Dict[str, Any]
    success: bool
    occurrences: int
    error: Optional[str] = None


@dataclass
class MultiEditResult:
    """Multi-edit result data"""

    file_path: str
    absolute_path: str
    edits_total: int
    edits_successful: int
    edits_failed: int
    total_replacements: int
    lines_total: int
    bytes_total: int
    content_changed: bool
    edit_results: List[Dict[str, Any]]


def escape_regex(text: str) -> str:
    """Escape special regex characters

    Args:
        text: Text to escape

    Returns:
        Escaped text
    """
    return re.escape(text)


def apply_single_edit(content: str, edit: SingleEdit) -> EditResult:
    """Apply a single edit to content

    Args:
        content: Current file content
        edit: Edit operation to apply

    Returns:
        Edit result with success status and details
    """
    # Count occurrences using literal string match
    occurrences = content.count(edit.old_string)

    # Validate occurrence count
    if occurrences == 0:
        preview = edit.old_string[:50]
        if len(edit.old_string) > 50:
            preview += "..."
        return EditResult(edit=asdict(edit), success=False, occurrences=0, error=f'Text not found: "{preview}"')

    if occurrences != edit.expected_replacements:
        return EditResult(
            edit=asdict(edit),
            success=False,
            occurrences=occurrences,
            error=f"Expected {edit.expected_replacements} replacement(s) but found {occurrences} occurrence(s)",
        )

    return EditResult(edit=asdict(edit), success=True, occurrences=occurrences)


async def _multiedit_impl(
    context: ExecutionContext,
    file_path: str,
    edits: List[Dict[str, Any]],
) -> ToolResult:
    """Internal implementation of multiedit functionality."""
    try:
        fail_fast = True  # Always fail fast in current implementation

        # Validate workspace path
        path_error = validate_workspace_path(file_path, context)
        if path_error:
            return path_error

        # Resolve path
        absolute_path = resolve_workspace_path(file_path, context)

        # Check if file exists
        file_error = await validate_file_exists(context, absolute_path, file_path)
        if file_error:
            return file_error

        print(f"Performing {len(edits)} edit(s) on: {file_path}")

        # Read current content
        try:
            current_content = await context.fs_operator.read_file(absolute_path, encoding="utf-8")
            # Normalize line endings to LF
            current_content = current_content.replace("\r\n", "\n")
        except Exception as error:
            return handle_tool_error(error, "Failed to read file", "permission")

        original_content = current_content
        edit_results: List[EditResult] = []
        success_count = 0
        total_replacements = 0

        # Convert dict edits to SingleEdit objects
        edit_objects = [
            SingleEdit(
                old_string=e["old_string"],
                new_string=e["new_string"],
                expected_replacements=e.get("expected_replacements", 1),
            )
            for e in edits
        ]

        # Apply edits sequentially
        for i, edit in enumerate(edit_objects):
            old_preview = edit.old_string[:30]
            new_preview = edit.new_string[:30]
            if len(edit.old_string) > 30:
                old_preview += "..."
            if len(edit.new_string) > 30:
                new_preview += "..."

            print(f'Applying edit {i + 1}/{len(edits)}: "{old_preview}" => "{new_preview}"')

            edit_result = apply_single_edit(current_content, edit)
            edit_results.append(edit_result)

            if edit_result.success:
                # Apply the edit
                current_content = current_content.replace(edit.old_string, edit.new_string)
                success_count += 1
                total_replacements += edit_result.occurrences
                print(f"✓ Edit {i + 1} successful: {edit_result.occurrences} replacement(s)")
            else:
                print(f"✗ Edit {i + 1} failed: {edit_result.error}")

                if fail_fast:
                    return handle_tool_error(
                        f"Edit operation failed at step {i + 1}: {edit_result.error}", "Edit sequence", "execution"
                    )

        # Write the updated content if any edits were successful
        if success_count > 0:
            await context.fs_operator.write_file(absolute_path, current_content)

        new_lines = len(current_content.split("\n"))
        new_size = len(current_content.encode("utf-8"))

        print(
            f"Multi-edit completed: {success_count}/{len(edits)} edits successful, "
            f"{total_replacements} total replacements"
        )

        result_data = MultiEditResult(
            file_path=file_path,
            absolute_path=absolute_path,
            edits_total=len(edits),
            edits_successful=success_count,
            edits_failed=len(edits) - success_count,
            total_replacements=total_replacements,
            lines_total=new_lines,
            bytes_total=new_size,
            content_changed=current_content != original_content,
            edit_results=[asdict(r) for r in edit_results],
        )
        return create_success_response(asdict(result_data))
    except Exception as error:
        return handle_tool_error(error, "Multiedit tool execution", "execution")


class MultiEditToolInput(BaseModel):
    """Input schema for multiedit tool."""

    file_path: str = Field(description="The absolute path to the file to modify")
    edits: List[Dict[str, Any]] = Field(
        description="Array of edit operations to perform sequentially on the file. Each edit should have: old_string, new_string, and expected_replacements (default: 1)"
    )


def create_multiedit_tool(context: ExecutionContext) -> DynamicTool:
    """Create a multiedit tool with the given context.

    Args:
        context: Execution context containing working directory and file operator

    Returns:
        DynamicTool instance that extends BaseTool
    """

    async def multiedit_tool_func(input_data: Dict, ctx: Optional[Dict] = None) -> ToolResult:
        """Perform multiple edits on a file."""
        file_path = input_data.get("file_path")
        edits = input_data.get("edits", [])

        return await _multiedit_impl(context, file_path, edits)

    return tool(
        func=multiedit_tool_func,
        name="Multiedit",
        description="Perform multiple find-and-replace operations on a single file in sequence. Each edit is applied to the result of the previous edit. Accepts both relative and absolute file paths within the workspace.",
        schema=MultiEditToolInput,
        get_display=lambda name, input_data: f"> Using {name} on file: {input_data.get('file_path', '')}",
    )
