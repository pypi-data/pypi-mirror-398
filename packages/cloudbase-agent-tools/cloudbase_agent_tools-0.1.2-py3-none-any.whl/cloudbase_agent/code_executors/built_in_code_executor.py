#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Built-in code executor implementation using E2B sandbox.

This module provides a code executor that runs code in a secure E2B sandbox
environment, supporting multiple programming languages.
"""

import os
from typing import Optional

try:
    from e2b.connection_config import ConnectionConfig
    from e2b_code_interpreter import Execution, Sandbox
except ImportError:
    raise ImportError(
        "e2b_code_interpreter is required for BuiltInCodeExecutor. Install it with: pip install e2b-code-interpreter"
    )

from .._tools_utils import ToolExecutionContext
from .base_code_executor import BaseCodeExecutor, CodeExecutorInput


class BuiltInCodeExecutor(BaseCodeExecutor):
    """Code executor using E2B sandbox.

    This executor runs code in a secure E2B sandbox environment,
    providing isolation and security for code execution.

    :param sandbox: Optional existing E2B sandbox instance
    :type sandbox: Optional[Sandbox]
    :param api_key: Optional E2B API key (defaults to environment variables)
    :type api_key: Optional[str]
    :param domain: Optional E2B domain (defaults to environment variables)
    :type domain: Optional[str]
    :param timeout_ms: Sandbox timeout in milliseconds
    :type timeout_ms: int
    """

    def __init__(
        self,
        sandbox: Optional[Sandbox] = None,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        timeout_ms: int = 3600 * 1000,
    ):
        """Initialize the built-in code executor.

        :param sandbox: Optional existing E2B sandbox instance
        :type sandbox: Optional[Sandbox]
        :param api_key: Optional E2B API key
        :type api_key: Optional[str]
        :param domain: Optional E2B domain
        :type domain: Optional[str]
        :param timeout_ms: Sandbox timeout in milliseconds
        :type timeout_ms: int
        """
        super().__init__()
        self.sandbox = sandbox
        self.api_key = api_key or os.getenv("AG_KIT_SANDBOX_API_KEY") or os.getenv("E2B_API_KEY")
        self.domain = domain or os.getenv("AG_KIT_SANDBOX_DOMAIN") or os.getenv("E2B_DOMAIN")
        self.timeout_ms = timeout_ms

    async def _ensure_sandbox(self) -> Sandbox:
        """Ensure sandbox is initialized.

        :return: The sandbox instance
        :rtype: Sandbox
        """
        if self.sandbox is None:
            # Create ConnectionConfig with api_key and domain
            connection_config = ConnectionConfig(
                api_key=self.api_key,
                domain=self.domain,
            )

            # Create sandbox using Sandbox.create() with the connection config
            self.sandbox = Sandbox.create("code-interpreter-v1", **connection_config.get_api_params())

        return self.sandbox

    async def _invoke(
        self,
        input_data: CodeExecutorInput,
        context: Optional[ToolExecutionContext] = None,
    ) -> Execution:
        """Execute code in E2B sandbox.

        :param input_data: The code execution input
        :type input_data: CodeExecutorInput
        :param context: Optional execution context
        :type context: Optional[ToolExecutionContext]
        :return: Execution result
        :rtype: Execution
        """
        # Ensure we have a sandbox
        sandbox = await self._ensure_sandbox()

        # Parse input if it's a dict
        if isinstance(input_data, dict):
            input_data = CodeExecutorInput(**input_data)

        # Determine language
        language = input_data.language or "python"

        # Execute code in sandbox
        execution = sandbox.run_code(
            input_data.code,
            language=language,
        )

        return execution

    async def close(self):
        """Close the sandbox and cleanup resources."""
        if self.sandbox:
            self.sandbox.kill()
            self.sandbox = None

    def __del__(self):
        """Cleanup when object is destroyed."""
        if self.sandbox:
            try:
                self.sandbox.kill()
            except Exception:
                pass
