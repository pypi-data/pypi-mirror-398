#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sandbox bash operator implementation using E2B."""

import time
from typing import Dict, Optional

try:
    from e2b_code_interpreter import Sandbox

    HAS_E2B = True
except ImportError:
    HAS_E2B = False
    Sandbox = None

from .base_operator import BaseBashOperator, CommandOptions, CommandResult

if not HAS_E2B:

    class SandboxBashOperator:
        """Placeholder for SandboxBashOperator when E2B is not available."""

        def __init__(self, *args, **kwargs):
            raise ImportError(
                "E2B is required for SandboxBashOperator. Install it with: pip install e2b-code-interpreter"
            )
else:

    class SandboxBashOperator(BaseBashOperator):
        """Bash operator that executes commands in E2B sandbox."""

        def __init__(self, sandbox: Sandbox, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None):
            """Initialize the sandbox bash operator.

            Args:
                sandbox: E2B Sandbox instance
                cwd: Working directory (defaults to /home/user)
                env: Environment variables
            """
            super().__init__()
            self.sandbox = sandbox
            self.current_working_directory = cwd or "/home/user"
            self.environment_variables = env or {}

        async def execute_command(self, command: str, options: Optional[CommandOptions] = None) -> CommandResult:
            """Execute a command in the sandbox.

            Args:
                command: The command to execute
                options: Command execution options

            Returns:
                CommandResult with execution details
            """
            start_time = time.time()
            options = options or CommandOptions()
            command_handle = None

            try:
                # Prepare environment variables
                env = {**self.environment_variables, **(options.env or {})}

                # Build the full command with environment and working directory
                full_command = command

                # Set working directory if different from current
                target_cwd = options.cwd or self.current_working_directory
                if target_cwd != "/home/user":
                    full_command = f'cd "{target_cwd}" && {command}'

                # Execute the command
                command_handle = self.sandbox.commands.run(
                    full_command,
                    envs=env,
                    cwd=target_cwd,
                    background=True,
                    on_stdout=options.on_stdout,
                    on_stderr=options.on_stderr,
                )

                # Handle input if provided
                if options.input:
                    self.sandbox.commands.send_stdin(command_handle.pid, options.input)

                # Wait for completion
                command_result = command_handle.wait()
                execution_time = (time.time() - start_time) * 1000

                exit_code = command_result.exit_code
                stdout = command_result.stdout
                stderr = command_result.stderr

                return CommandResult(
                    success=exit_code == 0,
                    exit_code=exit_code,
                    stdout=stdout.strip(),
                    stderr=stderr.strip(),
                    execution_time=execution_time,
                )

            except Exception as error:
                execution_time = (time.time() - start_time) * 1000

                # Try to kill the process if it's still running
                if command_handle:
                    try:
                        self.sandbox.commands.kill(command_handle.pid)
                    except:
                        pass

                # Default error-derived values
                error_message = str(error)
                exit_code = None
                stdout = ""
                stderr = error_message

                # Prefer structured result if present
                if hasattr(error, "result") and error.result is not None:
                    # Support both snake_case and camelCase from SDKs
                    exit_code = getattr(error.result, "exit_code", None)
                    if exit_code is None:
                        exit_code = getattr(error.result, "exitCode", None)
                    stdout = getattr(error.result, "stdout", stdout)
                    stderr = getattr(error.result, "stderr", stderr)
                else:
                    # Some SDK errors may expose attributes directly
                    if hasattr(error, "exit_code"):
                        try:
                            exit_code = int(error.exit_code)
                        except Exception:
                            pass
                    # As a fallback, parse from the error message: "Command exited with code XXX"
                    if exit_code is None and "Command exited with code" in error_message:
                        import re

                        m = re.search(r"Command exited with code\s+(\d+)", error_message)
                        if m:
                            try:
                                exit_code = int(m.group(1))
                            except Exception:
                                exit_code = None

                return CommandResult(
                    success=False,
                    exit_code=exit_code,
                    stdout=stdout.strip() if isinstance(stdout, str) else stdout,
                    stderr=stderr.strip() if isinstance(stderr, str) else stderr,
                    execution_time=execution_time,
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
            # Test if directory exists and is accessible
            result = await self.execute_command(f'cd "{path}" && pwd')

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

        def get_sandbox(self) -> Sandbox:
            """Get sandbox instance for advanced operations.

            Returns:
                The E2B Sandbox instance
            """
            return self.sandbox
