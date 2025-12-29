"""File system operators module

Provides different types of file system operator implementations.
"""

from .base_operator import BaseFileOperator, LocalFileOperator, PathLike
from .in_memory_operator import InMemoryFileOperator

# Optional E2B imports
try:
    from .sandbox_operator import SandboxFileOperator

    _has_sandbox = True
except ImportError:
    _has_sandbox = False

__all__ = [
    "BaseFileOperator",
    "LocalFileOperator",
    "InMemoryFileOperator",
    "PathLike",
]

if _has_sandbox:
    __all__.append("SandboxFileOperator")
