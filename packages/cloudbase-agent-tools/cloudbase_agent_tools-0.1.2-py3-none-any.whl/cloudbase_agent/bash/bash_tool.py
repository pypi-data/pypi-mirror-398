#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bash tool implementations."""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .._tools_utils import DynamicTool, ErrorType, ToolResult, tool
from .bash_operator.base_operator import BaseBashOperator, CommandOptions


@dataclass
class BashExecutionContext:
    """Context for bash execution."""

    bash_operator: BaseBashOperator
    working_directory: Optional[str] = None
    environment_variables: Optional[Dict[str, str]] = None
    default_timeout: int = 30000  # milliseconds


class BashToolInput(BaseModel):
    """Input schema for bash tool."""

    command: str = Field(description="The bash command to execute")
    cwd: Optional[str] = Field(None, description="Working directory for the command (optional)")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables to set (optional)")
    timeout: Optional[int] = Field(None, description="Timeout in milliseconds (default: 30000)")
    input: Optional[str] = Field(None, description="Input to send to the command via stdin (optional)")


class BashToolResponse(BaseModel):
    """Response from bash tool."""

    command: str
    exit_code: Optional[int]
    stdout: str
    stderr: str
    working_directory: str

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "working_directory": self.working_directory,
        }


def create_bash_tool(context: BashExecutionContext) -> DynamicTool:
    """Create a bash tool with the given context.

    Args:
        context: BashExecutionContext with operator and settings

    Returns:
        DynamicTool instance that extends BaseTool
    """

    async def bash_tool_func(input_data: Dict, ctx: Optional[Dict] = None) -> ToolResult:
        """Execute a bash command.

        Args:
            input_data: Dictionary with command, cwd, env, timeout, input
            ctx: Optional execution context

        Returns:
            ToolResult with command execution details
        """
        # Extract parameters from input_data
        command = input_data.get("command")
        cwd = input_data.get("cwd")
        env = input_data.get("env")
        timeout = input_data.get("timeout")
        stdin_input = input_data.get("input")
        on_stdout = input_data.get("on_stdout")
        on_stderr = input_data.get("on_stderr")

        try:
            # Prepare command options
            options = CommandOptions(
                cwd=cwd or context.working_directory,
                env={**(context.environment_variables or {}), **(env or {})},
                timeout=timeout or context.default_timeout,
                input=stdin_input,
                on_stdout=on_stdout,
                on_stderr=on_stderr,
            )

            # Execute the command
            result = await context.bash_operator.execute_command(command, options)

            # Get current working directory
            current_dir = await context.bash_operator.get_current_directory()

            return ToolResult(
                success=result.success,
                data=BashToolResponse(
                    command=command,
                    exit_code=result.exit_code,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    working_directory=current_dir,
                ).to_dict(),
                execution_time=result.execution_time,
            )
        except Exception as error:
            return ToolResult(
                success=False,
                error=f"Bash command execution: {str(error)}",
                error_type=ErrorType.EXECUTION,
                data=BashToolResponse(
                    command=command,
                    exit_code=None,
                    stdout="",
                    stderr=str(error),
                    working_directory=context.working_directory or "",
                ).to_dict(),
            )

    return tool(
        func=bash_tool_func,
        name="BashTool",
        description="Execute bash commands with support for different execution environments",
        schema=BashToolInput,
        get_display=lambda name, input_data: f"> Using {name} to execute command: {input_data.get('command', '')}",
    )


class MultiCommandInput(BaseModel):
    """Input schema for multi-command tool."""

    commands: List[str] = Field(description="Array of bash commands to execute in sequence")
    cwd: Optional[str] = Field(None, description="Working directory for all commands (optional)")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables to set (optional)")
    timeout: Optional[int] = Field(None, description="Timeout in milliseconds per command (default: 30000)")
    continue_on_error: bool = Field(
        False, description="Continue executing remaining commands if one fails (default: false)"
    )


class CommandResultItem(BaseModel):
    """Single command result in multi-command response."""

    command: str
    success: bool
    exit_code: Optional[int]
    stdout: str
    stderr: str
    execution_time: float


class MultiCommandResponse(BaseModel):
    """Response from multi-command tool."""

    commands: List[str]
    results: List[Dict]
    successful_commands: int
    failed_commands: int
    working_directory: str

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "commands": self.commands,
            "results": self.results,
            "successful_commands": self.successful_commands,
            "failed_commands": self.failed_commands,
            "working_directory": self.working_directory,
        }


def create_multi_command_tool(context: BashExecutionContext) -> DynamicTool:
    """Create a multi-command tool with the given context.

    Args:
        context: BashExecutionContext with operator and settings

    Returns:
        DynamicTool instance that extends BaseTool
    """

    async def multi_command_tool_func(input_data: Dict, ctx: Optional[Dict] = None) -> ToolResult:
        """Execute multiple bash commands in sequence.

        Args:
            input_data: Dictionary with commands, cwd, env, timeout, continue_on_error
            ctx: Optional execution context

        Returns:
            ToolResult with execution details for all commands
        """
        # Extract parameters from input_data
        commands = input_data.get("commands", [])
        cwd = input_data.get("cwd")
        env = input_data.get("env")
        timeout = input_data.get("timeout")
        continue_on_error = input_data.get("continue_on_error", False)
        on_stdout = input_data.get("on_stdout")
        on_stderr = input_data.get("on_stderr")

        start_time = time.time()
        results: List[Dict] = []
        successful_commands = 0
        failed_commands = 0

        try:
            # Prepare command options
            merged_env = {
                **(context.environment_variables or {}),
                **(env or {}),
                "CONTINUE_ON_ERROR": "1" if continue_on_error else "0",
            }

            options = CommandOptions(
                cwd=cwd or context.working_directory,
                env=merged_env,
                timeout=timeout or context.default_timeout,
                on_stdout=on_stdout,
                on_stderr=on_stderr,
            )

            # Execute commands in sequence
            for command in commands:
                try:
                    result = await context.bash_operator.execute_command(command, options)

                    results.append(
                        {
                            "command": command,
                            "success": result.success,
                            "exit_code": result.exit_code,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "execution_time": result.execution_time,
                        }
                    )

                    if result.success:
                        successful_commands += 1
                    else:
                        failed_commands += 1
                        # Stop on first failure unless continue_on_error is true
                        if not continue_on_error:
                            break

                except Exception as error:
                    failed_commands += 1
                    results.append(
                        {
                            "command": command,
                            "success": False,
                            "exit_code": None,
                            "stdout": "",
                            "stderr": str(error),
                            "execution_time": 0,
                        }
                    )

                    if not continue_on_error:
                        break

            current_dir = await context.bash_operator.get_current_directory()
            execution_time = (time.time() - start_time) * 1000

            return ToolResult(
                success=failed_commands == 0,
                data=MultiCommandResponse(
                    commands=commands,
                    results=results,
                    successful_commands=successful_commands,
                    failed_commands=failed_commands,
                    working_directory=current_dir,
                ).to_dict(),
                execution_time=execution_time,
            )
        except Exception as error:
            return ToolResult(
                success=False,
                error=f"MultiCommandTool: {str(error)}",
                error_type=ErrorType.EXECUTION,
                data=MultiCommandResponse(
                    commands=commands,
                    results=results,
                    successful_commands=successful_commands,
                    failed_commands=failed_commands + 1,
                    working_directory=context.working_directory or "",
                ).to_dict(),
            )

    return tool(
        func=multi_command_tool_func,
        name="MultiCommandTool",
        description="Execute multiple bash commands in sequence with support for different execution environments",
        schema=MultiCommandInput,
        get_display=lambda name,
        input_data: f"> Using {name} to execute {len(input_data.get('commands', []))} commands",
    )
