#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tools package for Cloudbase Agent.

This package provides various tools for Cloudbase Agent agents.
"""

# Bash tools
from .bash import (
    LocalBashOperator,
    create_bash_tool,
    create_multi_command_tool,
)
from .code_executors import (
    BaseCodeExecutor,
    CodeExecutorContext,
    CodeExecutorInput,
    Execution,
    ExecutionError,
    Logs,
    Result,
    UnsafeLocalCodeExecutor,
)

# Filesystem tools
from .fs import (
    ExecutionContext,
    LocalFileOperator,
    create_edit_tool,
    create_glob_tool,
    create_grep_tool,
    create_ls_tool,
    create_multiedit_tool,
    create_read_tool,
    create_str_replace_editor_tool,
    create_write_tool,
)
from ._tools_utils import (
    BaseTool,
    BaseToolkit,
    DynamicTool,
    ErrorType,
    ToolExecutionContext,
    ToolkitEvent,
    ToolkitEventListener,
    ToolkitManager,
    ToolResult,
    handle_tool_error,
    tool,
    toolkit_manager,
    tools_to_json_schemas,
)

# Optional E2B imports
try:
    from .code_executors import BuiltInCodeExecutor

    _has_e2b = True
except ImportError:
    _has_e2b = False
    BuiltInCodeExecutor = None

# Optional MCP imports
try:
    from .mcp import (
        AGKitMCPServer,
        MCPAdapterConfig,
        MCPClientConfig,
        MCPClientManager,
        MCPClientTool,
        MCPEvent,
        MCPEventListener,
        MCPEventType,
        MCPServerConfig,
        MCPToolConfig,
        MCPToolkit,
    )

    _has_mcp = True
except ImportError:
    _has_mcp = False
    MCPToolkit = None
    MCPClientManager = None
    MCPClientTool = None
    AGKitMCPServer = None
    MCPClientConfig = None
    MCPToolConfig = None
    MCPAdapterConfig = None
    MCPServerConfig = None
    MCPEvent = None
    MCPEventType = None
    MCPEventListener = None

# Framework adapters
from .adapters import AGKitTool

__all__ = [
    # Utils
    "BaseTool",
    "DynamicTool",
    "ToolResult",
    "ToolExecutionContext",
    "ErrorType",
    "handle_tool_error",
    "tool",
    "tools_to_json_schemas",
    # Toolkit
    "BaseToolkit",
    "ToolkitManager",
    "toolkit_manager",
    "ToolkitEvent",
    "ToolkitEventListener",
    # Code Executors
    "BaseCodeExecutor",
    "CodeExecutorInput",
    "UnsafeLocalCodeExecutor",
    "CodeExecutorContext",
    "Execution",
    "ExecutionError",
    "Logs",
    "Result",
    # Bash Tools
    "create_bash_tool",
    "create_multi_command_tool",
    "LocalBashOperator",
    # Filesystem Tools
    "create_read_tool",
    "create_write_tool",
    "create_edit_tool",
    "create_multiedit_tool",
    "create_grep_tool",
    "create_glob_tool",
    "create_ls_tool",
    "create_str_replace_editor_tool",
    "LocalFileOperator",
    "ExecutionContext",
    # Framework Adapters
    "AGKitTool",
]

if _has_e2b:
    __all__.append("BuiltInCodeExecutor")

if _has_mcp:
    __all__.extend(
        [
            "MCPToolkit",
            "MCPClientManager",
            "MCPClientTool",
            "AGKitMCPServer",
            "MCPClientConfig",
            "MCPToolConfig",
            "MCPAdapterConfig",
            "MCPServerConfig",
            "MCPEvent",
            "MCPEventType",
            "MCPEventListener",
        ]
    )
