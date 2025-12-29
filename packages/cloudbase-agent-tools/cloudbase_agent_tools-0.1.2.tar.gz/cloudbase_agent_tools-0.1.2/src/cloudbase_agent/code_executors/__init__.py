#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Code executors for Cloudbase Agent.

This package provides code execution tools that can run code in various
programming languages, both in secure sandbox environments and locally.
"""

from .base_code_executor import BaseCodeExecutor, CodeExecutorInput
from .code_executor_context import CodeExecutorContext
from .unsafe_local_code_executor import (
    Execution,
    ExecutionError,
    Logs,
    Result,
    UnsafeLocalCodeExecutor,
)

# Optional E2B imports
try:
    from .built_in_code_executor import BuiltInCodeExecutor

    _has_e2b = True
except ImportError:
    _has_e2b = False
    BuiltInCodeExecutor = None

__all__ = [
    "BaseCodeExecutor",
    "CodeExecutorInput",
    "UnsafeLocalCodeExecutor",
    "CodeExecutorContext",
    "Execution",
    "ExecutionError",
    "Logs",
    "Result",
]

if _has_e2b:
    __all__.append("BuiltInCodeExecutor")
