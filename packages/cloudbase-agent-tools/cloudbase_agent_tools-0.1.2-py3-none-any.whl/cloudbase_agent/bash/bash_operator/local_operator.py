#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local bash operator implementation."""

import asyncio
import os
import time
from typing import Dict, Optional

from .base_operator import BaseBashOperator, CommandOptions, CommandResult


class LocalBashOperator(BaseBashOperator):
    """Bash operator that executes commands locally."""

    def __init__(self, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None):
        """Initialize the local bash operator.

        Args:
            cwd: Working directory (defaults to current directory)
            env: Environment variables (merged with system environment)
        """
        super().__init__()
        self.current_working_directory = cwd or os.getcwd()
        self.environment_variables = {**os.environ.copy(), **(env or {})}

    async def execute_command(self, command: str, options: Optional[CommandOptions] = None) -> CommandResult:
        """Execute a command locally.

        Args:
            command: The command to execute
            options: Command execution options

        Returns:
            CommandResult with execution details
        """
        start_time = time.time()
        options = options or CommandOptions()

        # Merge options
        merged_cwd = options.cwd or self.current_working_directory
        merged_env = {**self.environment_variables, **(options.env or {})}
        timeout = (options.timeout / 1000.0) if options.timeout else 30.0

        try:
            # Create the subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if options.input else None,
                cwd=merged_cwd,
                env=merged_env,
            )

            # Collect output with callbacks
            stdout_data = []
            stderr_data = []

            async def read_stdout():
                if process.stdout:
                    async for line in process.stdout:
                        text = line.decode("utf-8", errors="replace")
                        stdout_data.append(text)
                        if options.on_stdout:
                            options.on_stdout(text)

            async def read_stderr():
                if process.stderr:
                    async for line in process.stderr:
                        text = line.decode("utf-8", errors="replace")
                        stderr_data.append(text)
                        if options.on_stderr:
                            options.on_stderr(text)

            # Start reading output
            read_tasks = [read_stdout(), read_stderr()]

            # Write input if provided
            if options.input and process.stdin:
                process.stdin.write(options.input.encode("utf-8"))
                await process.stdin.drain()
                process.stdin.close()

            # Wait for completion with timeout
            try:
                await asyncio.wait_for(asyncio.gather(*read_tasks, process.wait()), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                execution_time = (time.time() - start_time) * 1000
                return CommandResult(
                    success=False,
                    exit_code=None,
                    stdout="".join(stdout_data).strip(),
                    stderr=f"Command timed out after {timeout}s",
                    execution_time=execution_time,
                )

            execution_time = (time.time() - start_time) * 1000

            return CommandResult(
                success=process.returncode == 0,
                exit_code=process.returncode,
                stdout="".join(stdout_data).strip(),
                stderr="".join(stderr_data).strip(),
                execution_time=execution_time,
            )

        except Exception as error:
            execution_time = (time.time() - start_time) * 1000
            return CommandResult(
                success=False, exit_code=None, stdout="", stderr=str(error), execution_time=execution_time
            )

    async def get_current_directory(self) -> str:
        """Get the current working directory.

        Returns:
            The current working directory path
        """
        result = await self.execute_command("pwd")
        if result.success:
            self.current_working_directory = result.stdout.strip()
        return self.current_working_directory

    async def change_directory(self, path: str) -> None:
        """Change the current working directory.

        Args:
            path: The target directory path

        Raises:
            Exception: If the directory change fails
        """
        # Resolve the path
        if os.path.isabs(path):
            resolved_path = path
        else:
            resolved_path = os.path.join(self.current_working_directory, path)

        # Test if directory exists and is accessible
        result = await self.execute_command(f'cd "{resolved_path}" && pwd')

        if result.success:
            self.current_working_directory = result.stdout.strip()
        else:
            raise Exception(f"Failed to change directory to {path}: {result.stderr}")

    async def get_environment_variables(self) -> Dict[str, str]:
        """Get environment variables.

        Returns:
            Dictionary of environment variables
        """
        return self.environment_variables.copy()

    async def set_environment_variable(self, key: str, value: str) -> None:
        """Set an environment variable.

        Args:
            key: The environment variable name
            value: The environment variable value
        """
        self.environment_variables[key] = value
