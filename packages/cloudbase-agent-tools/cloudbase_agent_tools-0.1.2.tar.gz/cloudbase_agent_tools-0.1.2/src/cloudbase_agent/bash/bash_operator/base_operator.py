#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Base bash operator interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Dict, Optional


@dataclass
class CommandResult:
    """Result of a command execution."""

    success: bool
    exit_code: Optional[int]
    stdout: str
    stderr: str
    execution_time: float  # in milliseconds


@dataclass
class CommandOptions:
    """Options for command execution."""

    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None  # in milliseconds
    input: Optional[str] = None
    shell: Optional[bool] = True
    on_stdout: Optional[Callable[[str], None]] = None
    on_stderr: Optional[Callable[[str], None]] = None


class BaseBashOperator(ABC):
    """Abstract base class for bash operators."""

    def __init__(self):
        """Initialize the bash operator."""
        pass

    @abstractmethod
    async def execute_command(self, command: str, options: Optional[CommandOptions] = None) -> CommandResult:
        """Execute a command and return the result.

        Args:
            command: The command to execute
            options: Command execution options

        Returns:
            CommandResult with execution details
        """
        pass

    @abstractmethod
    async def get_current_directory(self) -> str:
        """Get the current working directory.

        Returns:
            The current working directory path
        """
        pass

    @abstractmethod
    async def change_directory(self, path: str) -> None:
        """Change the current working directory.

        Args:
            path: The target directory path

        Raises:
            Exception: If the directory change fails
        """
        pass

    @abstractmethod
    async def get_environment_variables(self) -> Dict[str, str]:
        """Get environment variables.

        Returns:
            Dictionary of environment variables
        """
        pass

    @abstractmethod
    async def set_environment_variable(self, key: str, value: str) -> None:
        """Set an environment variable.

        Args:
            key: The environment variable name
            value: The environment variable value
        """
        pass

    async def cleanup(self) -> None:
        """Cleanup resources. Default implementation does nothing."""
        pass
