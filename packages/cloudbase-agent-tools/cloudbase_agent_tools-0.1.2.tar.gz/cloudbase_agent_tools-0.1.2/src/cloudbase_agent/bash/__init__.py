#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bash tools for Cloudbase Agent."""

# Operators
from .bash_operator import (
    BaseBashOperator,
    CommandOptions,
    CommandResult,
    LocalBashOperator,
)

# Tools
from .bash_tool import (
    BashExecutionContext,
    BashToolInput,
    BashToolResponse,
    CommandResultItem,
    MultiCommandInput,
    MultiCommandResponse,
    create_bash_tool,
    create_multi_command_tool,
)

# Utils
from .utils import (
    CommandBuilders,
    CommandValidation,
    ParsedOutput,
    build_command,
    create_local_bash_context,
    escape_shell_arg,
    format_execution_time,
    parse_command_output,
    validate_command,
)

__all__ = [
    # Operators
    "BaseBashOperator",
    "CommandResult",
    "CommandOptions",
    "LocalBashOperator",
    # Tools
    "create_bash_tool",
    "create_multi_command_tool",
    "BashExecutionContext",
    "BashToolInput",
    "BashToolResponse",
    "MultiCommandInput",
    "MultiCommandResponse",
    "CommandResultItem",
    # Utils
    "create_local_bash_context",
    "validate_command",
    "CommandValidation",
    "escape_shell_arg",
    "build_command",
    "parse_command_output",
    "ParsedOutput",
    "format_execution_time",
    "CommandBuilders",
]

# Optional E2B imports
try:
    from .bash_operator import SandboxBashOperator
    from .utils import create_sandbox_bash_context

    __all__.extend(["SandboxBashOperator", "create_sandbox_bash_context"])
except ImportError:
    pass
