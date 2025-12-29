#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Base code executor implementation for Cloudbase Agent.

This module provides the abstract base class for code executors,
which enable execution of code in various programming languages.
"""

from abc import abstractmethod
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from .._tools_utils import BaseTool, ToolExecutionContext


class CodeExecutorInput(BaseModel):
    """Input schema for code executor.

    :param code: The code to execute
    :type code: str
    :param language: The programming language (optional)
    :type language: Optional[Literal["python", "js", "ts", "java", "r", "bash"]]
    """

    code: str = Field(..., description="code to execute")
    language: Optional[Literal["python", "js", "ts", "java", "r", "bash"]] = Field(
        None, description="programming language"
    )


class BaseCodeExecutor(BaseTool):
    """Abstract base class for code executors.

    This class provides the foundation for implementing code execution
    tools that can run code in various programming languages.
    """

    def __init__(self):
        """Initialize the base code executor."""
        super().__init__(
            name="CodeExecutor",
            description="Executes code snippets",
            schema=CodeExecutorInput,
        )

    @abstractmethod
    async def _invoke(
        self,
        input_data: CodeExecutorInput,
        context: Optional[ToolExecutionContext] = None,
    ) -> Any:
        """Execute code.

        :param input_data: The validated input data
        :type input_data: CodeExecutorInput
        :param context: Optional execution context
        :type context: Optional[ToolExecutionContext]
        :return: Execution result
        :rtype: Any
        """
        pass
