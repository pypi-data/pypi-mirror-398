#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility functions for bash tools."""

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from .bash_operator.local_operator import LocalBashOperator
from .bash_tool import BashExecutionContext

# Conditional E2B import
try:
    from e2b_code_interpreter import Sandbox

    from .bash_operator.sandbox_operator import SandboxBashOperator

    HAS_E2B = True
except ImportError:
    HAS_E2B = False
    Sandbox = None
    SandboxBashOperator = None


def create_local_bash_context(
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    default_timeout: int = 30000,
) -> BashExecutionContext:
    """Create a local bash execution context.

    Args:
        cwd: Working directory (defaults to current directory)
        env: Environment variables (merged with system environment)
        default_timeout: Default timeout in milliseconds

    Returns:
        BashExecutionContext configured for local execution
    """
    bash_operator = LocalBashOperator(cwd=cwd, env=env)

    return BashExecutionContext(
        bash_operator=bash_operator,
        working_directory=cwd or os.getcwd(),
        environment_variables=env or {},
        default_timeout=default_timeout,
    )


def create_sandbox_bash_context(
    sandbox: "Sandbox",
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    default_timeout: int = 30000,
) -> BashExecutionContext:
    """Create a sandbox bash execution context.

    Args:
        sandbox: E2B Sandbox instance
        cwd: Working directory (defaults to /home/user)
        env: Environment variables
        default_timeout: Default timeout in milliseconds

    Returns:
        BashExecutionContext configured for sandbox execution

    Raises:
        ImportError: If E2B is not installed
    """
    if not HAS_E2B:
        raise ImportError("E2B is required for sandbox execution. Install it with: pip install e2b-code-interpreter")

    bash_operator = SandboxBashOperator(sandbox=sandbox, cwd=cwd, env=env)

    return BashExecutionContext(
        bash_operator=bash_operator,
        working_directory=cwd or "/home/user",
        environment_variables=env or {},
        default_timeout=default_timeout,
    )


@dataclass
class CommandValidation:
    """Result of command validation."""

    is_valid: bool
    reason: Optional[str] = None


def validate_command(command: str) -> CommandValidation:
    """Validate command for security (basic checks).

    Args:
        command: The command to validate

    Returns:
        CommandValidation with validation result
    """
    # Basic security checks
    dangerous_patterns = [
        (r"rm\s+-rf\s+\/", "rm -rf /"),  # rm -rf /
        (r":\(\)\{.*\}", "fork bomb pattern"),  # Fork bomb pattern
        (r"sudo\s+rm", "sudo rm"),  # sudo rm
        (r"mkfs", "format filesystem"),  # Format filesystem
        (r"dd\s+if=.*of=/dev", "direct disk write"),  # Direct disk write
        (r">\s*/dev/sd[a-z]", "write to disk device"),  # Write to disk device
    ]

    for pattern, description in dangerous_patterns:
        if re.search(pattern, command):
            return CommandValidation(
                is_valid=False, reason=f"Command contains potentially dangerous pattern: {description}"
            )

    return CommandValidation(is_valid=True)


def escape_shell_arg(arg: str) -> str:
    """Escape shell arguments.

    Args:
        arg: The argument to escape

    Returns:
        Escaped argument safe for shell execution
    """
    # Replace single quotes with '\''
    escaped = arg.replace("'", "'\"'\"'")
    return f"'{escaped}'"


def build_command(command: str, args: Optional[List[str]] = None) -> str:
    """Build command with escaped arguments.

    Args:
        command: The base command
        args: List of arguments to append

    Returns:
        Complete command string with escaped arguments
    """
    if not args:
        return command

    escaped_args = [escape_shell_arg(arg) for arg in args]
    return f"{command} {' '.join(escaped_args)}"


@dataclass
class ParsedOutput:
    """Parsed command output."""

    lines: List[str]
    error_lines: List[str]
    is_empty: bool
    has_errors: bool
    exited_cleanly: bool


def parse_command_output(stdout: str, stderr: str) -> ParsedOutput:
    """Parse command output for common patterns.

    Args:
        stdout: Standard output
        stderr: Standard error

    Returns:
        ParsedOutput with parsed information
    """
    lines = [line for line in stdout.split("\n") if line.strip()]
    error_lines = [line for line in stderr.split("\n") if line.strip()]
    is_empty = not stdout.strip() and not stderr.strip()
    has_errors = bool(stderr.strip())
    exited_cleanly = not stderr.strip()

    return ParsedOutput(
        lines=lines,
        error_lines=error_lines,
        is_empty=is_empty,
        has_errors=has_errors,
        exited_cleanly=exited_cleanly,
    )


def format_execution_time(ms: float) -> str:
    """Format execution time.

    Args:
        ms: Time in milliseconds

    Returns:
        Formatted time string
    """
    if ms < 1000:
        return f"{ms:.0f}ms"
    elif ms < 60000:
        return f"{ms / 1000:.2f}s"
    else:
        minutes = int(ms / 60000)
        seconds = (ms % 60000) / 1000
        return f"{minutes}m {seconds:.2f}s"


class CommandBuilders:
    """Common command builders."""

    @staticmethod
    def list_files(
        path: str = ".",
        all: bool = False,
        long: bool = False,
        human: bool = False,
    ) -> str:
        """Build ls command.

        Args:
            path: Path to list
            all: Include hidden files
            long: Long format
            human: Human-readable sizes

        Returns:
            ls command string
        """
        cmd = "ls"
        if all:
            cmd += " -a"
        if long:
            cmd += " -l"
        if human:
            cmd += " -h"
        return f"{cmd} {escape_shell_arg(path)}"

    @staticmethod
    def find_files(pattern: str, path: str = ".") -> str:
        """Build find command.

        Args:
            pattern: File name pattern
            path: Search path

        Returns:
            find command string
        """
        return f"find {escape_shell_arg(path)} -name {escape_shell_arg(pattern)}"

    @staticmethod
    def grep(
        pattern: str,
        files: str = "*",
        recursive: bool = False,
        ignore_case: bool = False,
        line_numbers: bool = False,
    ) -> str:
        """Build grep command.

        Args:
            pattern: Search pattern
            files: Files to search
            recursive: Recursive search
            ignore_case: Case-insensitive search
            line_numbers: Show line numbers

        Returns:
            grep command string
        """
        cmd = "grep"
        if recursive:
            cmd += " -r"
        if ignore_case:
            cmd += " -i"
        if line_numbers:
            cmd += " -n"
        return f"{cmd} {escape_shell_arg(pattern)} {escape_shell_arg(files)}"

    @staticmethod
    def exists(path: str) -> str:
        """Build command to check if file/directory exists.

        Args:
            path: Path to check

        Returns:
            test command string
        """
        return f'test -e {escape_shell_arg(path)} && echo "exists" || echo "not found"'

    @staticmethod
    def stat(path: str) -> str:
        """Build stat command.

        Args:
            path: Path to stat

        Returns:
            stat command string
        """
        return f"stat {escape_shell_arg(path)}"

    @staticmethod
    def mkdir(path: str, parents: bool = False) -> str:
        """Build mkdir command.

        Args:
            path: Directory path
            parents: Create parent directories

        Returns:
            mkdir command string
        """
        cmd = "mkdir"
        if parents:
            cmd += " -p"
        return f"{cmd} {escape_shell_arg(path)}"

    @staticmethod
    def copy(
        source: str,
        destination: str,
        recursive: bool = False,
        preserve: bool = False,
    ) -> str:
        """Build cp command.

        Args:
            source: Source path
            destination: Destination path
            recursive: Copy directories recursively
            preserve: Preserve attributes

        Returns:
            cp command string
        """
        cmd = "cp"
        if recursive:
            cmd += " -r"
        if preserve:
            cmd += " -p"
        return f"{cmd} {escape_shell_arg(source)} {escape_shell_arg(destination)}"

    @staticmethod
    def move(source: str, destination: str) -> str:
        """Build mv command.

        Args:
            source: Source path
            destination: Destination path

        Returns:
            mv command string
        """
        return f"mv {escape_shell_arg(source)} {escape_shell_arg(destination)}"

    @staticmethod
    def remove(path: str, recursive: bool = False, force: bool = False) -> str:
        """Build rm command.

        Args:
            path: Path to remove
            recursive: Remove directories recursively
            force: Force removal

        Returns:
            rm command string
        """
        cmd = "rm"
        if recursive:
            cmd += " -r"
        if force:
            cmd += " -f"
        return f"{cmd} {escape_shell_arg(path)}"
