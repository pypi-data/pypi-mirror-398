"""File system tools module

Provides tools and abstraction layer for file system operations, supporting both local and in-memory file systems.
"""

from .edit_tool import FileEditResult, create_edit_tool
from .fs_operator import (
    BaseFileOperator,
    InMemoryFileOperator,
    LocalFileOperator,
    PathLike,
)
from .glob_tool import GlobFileEntry, GlobResult, create_glob_tool
from .grep_tool import GrepMatch, GrepResult, create_grep_tool
from .ls_tool import FileEntry, LsResult, create_ls_tool
from .multiedit_tool import MultiEditResult, create_multiedit_tool
from .read_tool import FileReadResult, create_read_tool
from .str_replace_editor_tool import EditorCommand, create_str_replace_editor_tool
from .utils import (
    ExecutionContext,
    ToolResult,
    create_success_response,
    handle_tool_error,
    resolve_workspace_path,
    validate_directory_exists,
    validate_file_exists,
    validate_required_string,
    validate_workspace_path,
)
from .write_tool import FileWriteResult, create_write_tool

# Optional E2B imports
try:
    from .fs_operator import SandboxFileOperator

    _has_sandbox = True
except ImportError:
    _has_sandbox = False

__all__ = [
    # Utils
    "ExecutionContext",
    "ToolResult",
    "validate_workspace_path",
    "resolve_workspace_path",
    "create_success_response",
    "handle_tool_error",
    "validate_file_exists",
    "validate_directory_exists",
    "validate_required_string",
    # Operators
    "BaseFileOperator",
    "LocalFileOperator",
    "InMemoryFileOperator",
    "PathLike",
    # Tool creators
    "create_read_tool",
    "create_write_tool",
    "create_edit_tool",
    "create_grep_tool",
    "create_ls_tool",
    "create_glob_tool",
    "create_multiedit_tool",
    "create_str_replace_editor_tool",
    # Result types
    "FileReadResult",
    "FileWriteResult",
    "FileEditResult",
    "MultiEditResult",
    "GrepResult",
    "GrepMatch",
    "GlobResult",
    "GlobFileEntry",
    "LsResult",
    "FileEntry",
    "EditorCommand",
]

if _has_sandbox:
    __all__.append("SandboxFileOperator")
