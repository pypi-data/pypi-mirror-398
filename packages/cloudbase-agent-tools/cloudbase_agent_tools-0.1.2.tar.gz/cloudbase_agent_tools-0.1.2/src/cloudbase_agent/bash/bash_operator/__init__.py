#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bash operator implementations for Cloudbase Agent."""

from .base_operator import BaseBashOperator, CommandOptions, CommandResult
from .local_operator import LocalBashOperator

__all__ = [
    "BaseBashOperator",
    "CommandResult",
    "CommandOptions",
    "LocalBashOperator",
]

# Optional E2B imports
try:
    from .sandbox_operator import SandboxBashOperator

    __all__.append("SandboxBashOperator")
except ImportError:
    pass
