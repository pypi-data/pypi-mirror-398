#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LangGraph adapter for Cloudbase Agent tools.

This module provides utilities to convert Cloudbase Agent tools to LangGraph/LangChain
compatible tool format, enabling seamless integration without manual wrapping.

Inspired by Google ADK's LangchainTool implementation, this adapter provides
bidirectional conversion: Cloudbase Agent tools <-> LangChain tools.
"""

from typing import Any, Dict, Optional, Union

from langchain_core.tools import BaseTool as LangChainBaseTool
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model

from .._tools_utils import BaseTool, ToolExecutionContext, ToolResult


class AGKitTool:
    """Wrapper class to convert Cloudbase Agent tools to LangChain StructuredTool.

    This class provides a clean interface for converting Cloudbase Agent BaseTool instances
    to LangChain-compatible StructuredTool format. It preserves all tool metadata
    and provides flexible customization options.

    Inspired by Google ADK's LangchainTool, this provides the reverse conversion:
    Cloudbase Agent tools -> LangChain tools.

    :param tool: The Cloudbase Agent tool to wrap
    :type tool: BaseTool
    :param name: Optional override for tool name (defaults to tool.name)
    :type name: Optional[str]
    :param description: Optional override for tool description
    :type description: Optional[str]
    :param return_direct: Whether to return tool output directly to user
    :type return_direct: bool

    Example:
        Basic usage::

            from cloudbase_agent.tools import UnsafeLocalCodeExecutor
            from cloudbase_agent.tools.adapters import AGKitTool
            from langgraph.prebuilt import ToolNode

            # Create Cloudbase Agent tool
            executor = UnsafeLocalCodeExecutor()

            # Wrap with AGKitTool
            wrapped_tool = AGKitTool(tool=executor)

            # Get LangChain tool
            langchain_tool = wrapped_tool.as_langchain_tool()

            # Use directly in LangGraph
            tool_node = ToolNode([langchain_tool])

        Customizing tool metadata::

            from cloudbase_agent.tools import UnsafeLocalCodeExecutor
            from cloudbase_agent.tools.adapters import AGKitTool

            # Override name and description
            wrapped_tool = AGKitTool(
                tool=UnsafeLocalCodeExecutor(),
                name="custom_executor",
                description="Custom code executor with enhanced features",
                return_direct=True
            )

            langchain_tool = wrapped_tool.as_langchain_tool()
    """

    def __init__(
        self,
        tool: BaseTool,
        name: Optional[str] = None,
        description: Optional[str] = None,
        return_direct: bool = False,
    ):
        """Initialize the AGKitTool wrapper.

        :param tool: The Cloudbase Agent tool to wrap
        :type tool: BaseTool
        :param name: Optional override for tool name
        :type name: Optional[str]
        :param description: Optional override for tool description
        :type description: Optional[str]
        :param return_direct: Whether to return tool output directly to user
        :type return_direct: bool
        """
        self._tool = tool
        self._name = name or tool.name
        self._description = description or tool.description or f"Tool: {tool.name}"
        self._return_direct = return_direct
        self._schema = tool.schema

    @property
    def name(self) -> str:
        """Get the tool name."""
        return self._name

    @property
    def description(self) -> str:
        """Get the tool description."""
        return self._description

    @property
    def schema(self) -> Optional[type[BaseModel]]:
        """Get the tool schema."""
        return self._schema

    def _format_result(self, result: ToolResult) -> str:
        """Format Cloudbase Agent ToolResult to string output.

        This method handles different types of tool results and formats them
        appropriately for LangChain consumption.

        :param result: The Cloudbase Agent tool result
        :type result: ToolResult
        :return: Formatted string output
        :rtype: str
        """
        if not result.success:
            return f"Error: {result.error}"

        # If data is already a string, return it directly
        if isinstance(result.data, str):
            return result.data

        # If data has logs attribute (like code execution results)
        if hasattr(result.data, "logs"):
            logs = result.data.logs
            stdout = getattr(logs, "stdout", "") if logs else ""
            stderr = getattr(logs, "stderr", "") if logs else ""

            output = []
            if stdout:
                output.append(f"Output:\n{stdout}")
            if stderr:
                output.append(f"Stderr:\n{stderr}")

            return "\n\n".join(output) if output else "Execution successful (no output)"

        # For other data types, try JSON serialization
        import json

        try:
            return json.dumps(result.data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            return str(result.data)

    async def _invoke_wrapper(self, **kwargs: Any) -> str:
        """Wrapper function that calls Cloudbase Agent tool and formats output.

        This function handles the conversion between LangChain's tool calling
        convention and Cloudbase Agent's invoke method, including error handling and
        result formatting.

        :param kwargs: Tool input arguments
        :type kwargs: Any
        :return: Formatted tool output
        :rtype: str
        """
        try:
            # If tool has no schema, wrap kwargs in input_data
            if not self._schema:
                input_data = kwargs.get("input_data", kwargs)
            else:
                input_data = kwargs

            # Call Cloudbase Agent tool
            result = await self._tool.invoke(input_data)

            # Format and return result
            return self._format_result(result)

        except Exception as e:
            return f"Tool execution error: {str(e)}"

    def as_langchain_tool(self) -> StructuredTool:
        """Convert to LangChain StructuredTool.

        :return: LangChain StructuredTool instance
        :rtype: StructuredTool
        """
        # Create args schema for LangChain
        if self._schema:
            args_schema = self._schema
        else:
            # Create a generic schema that accepts any dict
            args_schema = create_model(
                f"{self._name}Input", **{"input_data": (Dict[str, Any], Field(description="Tool input data"))}
            )

        # Create and return StructuredTool
        return StructuredTool(
            name=self._name,
            description=self._description,
            args_schema=args_schema,
            coroutine=self._invoke_wrapper,
            return_direct=self._return_direct,
        )

    def as_llamaindex_tool(self):
        """Convert to LlamaIndex FunctionTool.

        :return: LlamaIndex FunctionTool instance
        :rtype: FunctionTool
        :raises ImportError: If LlamaIndex is not installed
        """
        try:
            from llama_index.core.tools import FunctionTool
        except ImportError:
            raise ImportError("LlamaIndex is not installed. Please install it with: pip install llama-index-core")

        # Create FunctionTool from async function
        return FunctionTool.from_defaults(
            async_fn=self._invoke_wrapper,
            name=self._name,
            description=self._description,
            return_direct=self._return_direct,
        )


class LangChainTool(BaseTool):
    """Wrapper class to convert LangChain tools to Cloudbase Agent BaseTool.

    This class provides a clean interface for converting LangChain BaseTool or
    StructuredTool instances to Cloudbase Agent-compatible BaseTool format. It preserves
    all tool metadata and provides seamless integration.

    This is the reverse of AGKitTool: LangChain tools -> Cloudbase Agent tools.

    :param tool: The LangChain tool to wrap
    :type tool: Union[LangChainBaseTool, StructuredTool]
    :param name: Optional override for tool name (defaults to tool.name)
    :type name: Optional[str]
    :param description: Optional override for tool description
    :type description: Optional[str]

    Example:
        Basic usage::

            from langchain_core.tools import StructuredTool
            from cloudbase_agent.tools.adapters import LangChainTool
            from pydantic import BaseModel, Field

            # Define a LangChain tool
            class CalculatorInput(BaseModel):
                a: int = Field(description="First number")
                b: int = Field(description="Second number")

            def add(a: int, b: int) -> int:
                return a + b

            langchain_tool = StructuredTool.from_function(
                func=add,
                name="calculator",
                description="Add two numbers",
                args_schema=CalculatorInput
            )

            # Wrap with LangChainTool
            agkit_tool = LangChainTool(tool=langchain_tool)

            # Use as Cloudbase Agent tool
            result = await agkit_tool.invoke({"a": 5, "b": 3})
            print(result.data)  # Output: 8

        Using with existing LangChain tools::

            from langchain_community.tools import DuckDuckGoSearchRun
            from cloudbase_agent.tools.adapters import LangChainTool

            # Wrap existing LangChain tool
            search_tool = DuckDuckGoSearchRun()
            agkit_search = LangChainTool(search_tool)

            # Use in Cloudbase Agent workflow
            result = await agkit_search.invoke({"query": "Python programming"})
    """

    def __init__(
        self,
        tool: Union[LangChainBaseTool, StructuredTool],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Initialize the LangChainTool wrapper.

        :param tool: The LangChain tool to wrap
        :type tool: Union[LangChainBaseTool, StructuredTool]
        :param name: Optional override for tool name
        :type name: Optional[str]
        :param description: Optional override for tool description
        :type description: Optional[str]
        """
        self._langchain_tool = tool

        # Extract tool metadata
        tool_name = name or getattr(tool, "name", "langchain_tool")
        tool_description = description or getattr(tool, "description", "")

        # Extract schema if available
        tool_schema = None
        if hasattr(tool, "args_schema") and tool.args_schema:
            tool_schema = tool.args_schema

        # Initialize BaseTool
        super().__init__(
            name=tool_name,
            description=tool_description,
            schema=tool_schema,
        )

    def _parse_langchain_result(self, result: Any) -> Any:
        """Parse LangChain tool result to Cloudbase Agent format.

        LangChain tools typically return strings or simple values.
        This method handles the conversion to Cloudbase Agent's expected format.

        :param result: The LangChain tool result
        :type result: Any
        :return: Parsed result data
        :rtype: Any
        """
        # If result is already structured, return as-is
        if isinstance(result, (dict, list)):
            return result

        # If result is a string, return it directly
        if isinstance(result, str):
            return result

        # For other types, convert to string
        return str(result)

    async def _invoke(
        self,
        input_data: Any,
        context: Optional[ToolExecutionContext] = None,
    ) -> Any:
        """Execute the LangChain tool.

        This method handles the conversion between Cloudbase Agent's invoke convention
        and LangChain's tool calling convention, including async/sync handling.

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

            # Check if tool has async support
            # Try ainvoke first (newer LangChain API)
            if hasattr(self._langchain_tool, "ainvoke"):
                # Use ainvoke method (newer LangChain versions)
                # ainvoke expects a dict, not **kwargs
                result = await self._langchain_tool.ainvoke(input_dict)
            elif hasattr(self._langchain_tool, "arun"):
                # Use async method (older API)
                # arun expects **kwargs
                result = await self._langchain_tool.arun(**input_dict)
            elif hasattr(self._langchain_tool, "invoke"):
                # Use invoke method (newer LangChain versions, sync)
                import asyncio

                # invoke expects a dict, not **kwargs
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._langchain_tool.invoke(input_dict)
                )
            elif hasattr(self._langchain_tool, "run"):
                # Fall back to sync method (older API)
                import asyncio

                # run expects **kwargs
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._langchain_tool.run(**input_dict)
                )
            else:
                raise AttributeError(
                    f"LangChain tool '{self.name}' does not have a recognized "
                    "execution method (ainvoke, arun, invoke, or run)"
                )

            # Parse and return result
            return self._parse_langchain_result(result)

        except Exception as e:
            # Re-raise exception to be handled by BaseTool.invoke
            raise RuntimeError(f"LangChain tool execution failed: {str(e)}") from e

    def as_agkit_tool(self) -> BaseTool:
        """Convert to Cloudbase Agent BaseTool.

        Since LangChainTool already extends BaseTool, this method simply
        returns self, providing a symmetric API with AGKitTool.

        :return: Cloudbase Agent BaseTool instance (self)
        :rtype: BaseTool

        Example::

            from langchain_core.tools import StructuredTool
            from cloudbase_agent.tools.adapters import LangChainTool

            # Create LangChain tool
            langchain_tool = StructuredTool.from_function(...)

            # Convert to Cloudbase Agent (symmetric API)
            agkit_tool = LangChainTool(tool=langchain_tool).as_agkit_tool()
        """
        return self


def from_langchain(
    langchain_tool: Union[LangChainBaseTool, StructuredTool],
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> BaseTool:
    """Convert a LangChain tool to an Cloudbase Agent tool.

    This is a convenience function that creates a LangChainTool wrapper.

    :param langchain_tool: The LangChain tool to convert
    :type langchain_tool: Union[LangChainBaseTool, StructuredTool]
    :param name: Optional override for tool name
    :type name: Optional[str]
    :param description: Optional override for tool description
    :type description: Optional[str]
    :return: Cloudbase Agent compatible tool
    :rtype: BaseTool

    Example::

        from langchain_core.tools import StructuredTool
        from cloudbase_agent.tools.adapters import from_langchain

        # Create LangChain tool
        langchain_tool = StructuredTool.from_function(
            func=lambda x: x * 2,
            name="doubler",
            description="Double a number"
        )

        # Convert to Cloudbase Agent tool
        agkit_tool = from_langchain(langchain_tool)

        # Use as Cloudbase Agent tool
        result = await agkit_tool.invoke({"x": 5})
    """
    return LangChainTool(
        tool=langchain_tool,
        name=name,
        description=description,
    )
