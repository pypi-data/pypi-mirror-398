#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LlamaIndex adapter for Cloudbase Agent tools.

This module provides utilities to convert Cloudbase Agent tools to LlamaIndex
compatible tool format, enabling seamless integration without manual wrapping.

Inspired by the LangChain adapter, this adapter provides bidirectional conversion:
Cloudbase Agent tools <-> LlamaIndex tools.
"""

from typing import Any, Optional

from pydantic import BaseModel

try:
    from llama_index.core.tools import BaseTool as LlamaIndexBaseTool
    from llama_index.core.tools import FunctionTool

    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False

    # Create dummy classes for type hints
    class LlamaIndexBaseTool:
        pass

    class FunctionTool:
        pass


from .._tools_utils import BaseTool, ToolExecutionContext


class LlamaIndexTool(BaseTool):
    """Wrapper class to convert LlamaIndex tools to Cloudbase Agent BaseTool.

    This class provides a clean interface for converting LlamaIndex BaseTool or
    FunctionTool instances to Cloudbase Agent-compatible BaseTool format. It preserves
    all tool metadata and provides seamless integration.

    This is the reverse of AGKitToolForLlamaIndex: LlamaIndex tools -> Cloudbase Agent tools.

    :param tool: The LlamaIndex tool to wrap
    :type tool: LlamaIndexBaseTool
    :param name: Optional override for tool name (defaults to tool.metadata.name)
    :type name: Optional[str]
    :param description: Optional override for tool description
    :type description: Optional[str]

    Example:
        Basic usage::

            from llama_index.core.tools import FunctionTool
            from cloudbase_agent.tools.adapters import LlamaIndexTool

            # Define a LlamaIndex tool
            def multiply(a: int, b: int) -> int:
                '''Multiply two numbers.'''
                return a * b

            llamaindex_tool = FunctionTool.from_defaults(
                fn=multiply,
                name="multiplier",
                description="Multiply two numbers"
            )

            # Wrap with LlamaIndexTool
            agkit_tool = LlamaIndexTool(tool=llamaindex_tool)

            # Use as Cloudbase Agent tool
            result = await agkit_tool.invoke({"a": 5, "b": 3})
            print(result.data)  # Output: 15
    """

    def __init__(
        self,
        tool: LlamaIndexBaseTool,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Initialize the LlamaIndexTool wrapper.

        :param tool: The LlamaIndex tool to wrap
        :type tool: LlamaIndexBaseTool
        :param name: Optional override for tool name
        :type name: Optional[str]
        :param description: Optional override for tool description
        :type description: Optional[str]
        """
        if not LLAMAINDEX_AVAILABLE:
            raise ImportError("LlamaIndex is not installed. Please install it with: pip install llama-index-core")

        self._llamaindex_tool = tool

        # Extract tool metadata
        metadata = getattr(tool, "metadata", None)
        tool_name = name or (metadata.name if metadata else "llamaindex_tool")
        tool_description = description or (metadata.description if metadata else "")

        # Extract schema if available (LlamaIndex uses fn_schema)
        tool_schema = None
        if metadata and hasattr(metadata, "fn_schema"):
            tool_schema = metadata.fn_schema

        # Initialize BaseTool
        super().__init__(
            name=tool_name,
            description=tool_description,
            schema=tool_schema,
        )

    def _parse_llamaindex_result(self, result: Any) -> Any:
        """Parse LlamaIndex tool result to Cloudbase Agent format.

        LlamaIndex tools typically return strings or simple values.
        This method handles the conversion to Cloudbase Agent's expected format.

        :param result: The LlamaIndex tool result
        :type result: Any
        :return: Parsed result data
        :rtype: Any
        """
        # Check if result is a ToolOutput object (LlamaIndex's return type)
        if hasattr(result, "raw_output"):
            result = result.raw_output

        # If result is already structured, return as-is
        if isinstance(result, (dict, list)):
            return result

        # If result is a string, try to parse as JSON
        if isinstance(result, str):
            # Try to parse as JSON if it looks like a dict/list
            if result.strip().startswith(("{", "[")):
                import json

                try:
                    return json.loads(result)
                except (json.JSONDecodeError, ValueError):
                    pass
            return result

        # For other types, convert to string
        return str(result)

    async def _invoke(
        self,
        input_data: Any,
        context: Optional[ToolExecutionContext] = None,
    ) -> Any:
        """Execute the LlamaIndex tool.

        This method handles the conversion between Cloudbase Agent's invoke convention
        and LlamaIndex's tool calling convention, including async/sync handling.

        :param input_data: The validated input data
        :type input_data: Any
        :param context: Optional execution context
        :type context: Optional[ToolExecutionContext]
        :return: Tool execution result
        :rtype: Any
        """
        try:
            # Convert Pydantic model to dict if needed
            if isinstance(input_data, BaseModel):
                input_dict = input_data.model_dump()
            elif isinstance(input_data, dict):
                input_dict = input_data
            else:
                # For simple inputs, wrap in a dict
                input_dict = {"input": input_data}

            # LlamaIndex tools have call and acall methods
            if hasattr(self._llamaindex_tool, "acall"):
                # Use async method
                result = await self._llamaindex_tool.acall(**input_dict)
            elif hasattr(self._llamaindex_tool, "call"):
                # Use sync method in executor
                import asyncio

                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._llamaindex_tool.call(**input_dict)
                )
            else:
                raise AttributeError(
                    f"LlamaIndex tool '{self.name}' does not have a recognized execution method (acall or call)"
                )

            # Parse and return result
            return self._parse_llamaindex_result(result)

        except Exception as e:
            # Re-raise exception to be handled by BaseTool.invoke
            raise RuntimeError(f"LlamaIndex tool execution failed: {str(e)}") from e

    def as_agkit_tool(self) -> BaseTool:
        """Convert to Cloudbase Agent BaseTool.

        Since LlamaIndexTool already extends BaseTool, this method simply
        returns self, providing a symmetric API with AGKitTool.

        :return: Cloudbase Agent BaseTool instance (self)
        :rtype: BaseTool

        Example::

            from llama_index.core.tools import FunctionTool
            from cloudbase_agent.tools.adapters import LlamaIndexTool

            # Create LlamaIndex tool
            llamaindex_tool = FunctionTool.from_defaults(...)

            # Convert to Cloudbase Agent (symmetric API)
            agkit_tool = LlamaIndexTool(tool=llamaindex_tool).as_agkit_tool()
        """
        return self


def from_llamaindex(
    llamaindex_tool: LlamaIndexBaseTool,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> BaseTool:
    """Convert a LlamaIndex tool to an Cloudbase Agent tool.

    This is a convenience function that creates a LlamaIndexTool wrapper.

    :param llamaindex_tool: The LlamaIndex tool to convert
    :type llamaindex_tool: LlamaIndexBaseTool
    :param name: Optional override for tool name
    :type name: Optional[str]
    :param description: Optional override for tool description
    :type description: Optional[str]
    :return: Cloudbase Agent compatible tool
    :rtype: BaseTool

    Example::

        from llama_index.core.tools import FunctionTool
        from cloudbase_agent.tools.adapters import from_llamaindex

        # Create LlamaIndex tool
        llamaindex_tool = FunctionTool.from_defaults(
            fn=lambda x: x * 2,
            name="doubler",
            description="Double a number"
        )

        # Convert to Cloudbase Agent tool
        agkit_tool = from_llamaindex(llamaindex_tool)

        # Use as Cloudbase Agent tool
        result = await agkit_tool.invoke({"x": 5})
    """
    return LlamaIndexTool(
        tool=llamaindex_tool,
        name=name,
        description=description,
    )
