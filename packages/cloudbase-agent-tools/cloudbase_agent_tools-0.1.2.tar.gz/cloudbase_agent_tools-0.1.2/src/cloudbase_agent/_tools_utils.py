#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility classes and functions for Cloudbase Agent tools.

This module provides base classes and utilities for implementing tools
in the Cloudbase Agent framework, including error handling, validation, and
execution context management.
"""

import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, ValidationError


class ErrorType(str, Enum):
    """Tool error types."""

    VALIDATION = "validation"
    SECURITY = "security"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION = "permission"
    EXECUTION = "execution"
    UNKNOWN = "unknown"


class ToolResult(BaseModel, Generic[TypeVar("TOutput")]):
    """Tool execution result.

    This class encapsulates the result of a tool execution, including
    success status, data, errors, and execution time.

    :param success: Whether the tool execution was successful
    :type success: bool
    :param data: The output data from the tool execution
    :type data: Optional[Any]
    :param error: Error message if execution failed
    :type error: Optional[str]
    :param error_type: Type of error that occurred
    :type error_type: Optional[ErrorType]
    :param execution_time: Time taken to execute the tool in seconds
    :type execution_time: Optional[float]
    :param context: Optional context information for the operation
    :type context: Optional[str]
    """

    model_config = {"use_enum_values": True}

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    execution_time: Optional[float] = None
    context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for compatibility with FS tools.

        :return: Dictionary representation of the tool result
        :rtype: Dict[str, Any]
        """
        result = {"success": self.success}
        if self.success:
            result["data"] = self.data
        else:
            result["error"] = self.error
            if self.error_type:
                result["error_type"] = self.error_type
            if self.context:
                result["context"] = self.context
        return result


def handle_tool_error(
    error: Exception,
    context: Optional[str] = None,
    error_type: ErrorType = ErrorType.UNKNOWN,
    details: Optional[Dict[str, Any]] = None,
) -> ToolResult:
    """Generic error handler that converts exceptions to standardized error responses.

    :param error: The exception that occurred
    :type error: Exception
    :param context: Optional context description
    :type context: Optional[str]
    :param error_type: Type of error
    :type error_type: ErrorType
    :param details: Additional error details
    :type details: Optional[Dict[str, Any]]
    :return: Standardized tool result with error information
    :rtype: ToolResult
    """
    error_message = str(error)

    if details is None:
        details = {}

    details.update(
        {
            "name": type(error).__name__,
            "type": str(type(error)),
        }
    )

    # Add context if provided
    if context:
        error_message = f"{context}: {error_message}"

    return ToolResult(
        success=False,
        error=error_message,
        error_type=error_type,
        data=details,
        context=context,
    )


# Tool execution context type
ToolExecutionContext = Dict[str, Any]


class BaseTool(ABC, Generic[TypeVar("TInput"), TypeVar("TOutput")]):
    """Base tool class with generic support.

    This abstract class provides the foundation for all tools in the Cloudbase Agent
    framework. Subclasses must implement the _invoke method to provide
    tool-specific functionality.

    :param name: The name of the tool
    :type name: str
    :param description: Human-readable description of the tool
    :type description: Optional[str]
    :param schema: Pydantic model class for input validation
    :type schema: Optional[type[BaseModel]]
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        schema: Optional[type[BaseModel]] = None,
    ):
        """Initialize the base tool.

        :param name: The name of the tool
        :type name: str
        :param description: Human-readable description of the tool
        :type description: Optional[str]
        :param schema: Pydantic model class for input validation
        :type schema: Optional[type[BaseModel]]
        """
        self.name = name
        self.description = description
        self.schema = schema

    def get_display(self, name: str, input_data: Any) -> str:
        """Get tool display information.

        :param name: The tool name
        :type name: str
        :param input_data: The input data
        :type input_data: Any
        :return: Display string
        :rtype: str
        """
        import json

        return f"{self.name}: {json.dumps(input_data, default=str)}"

    def validate_input(self, input_data: Any) -> ToolResult:
        """Validate input parameters.

        :param input_data: The input data to validate
        :type input_data: Any
        :return: Validation result
        :rtype: ToolResult
        """
        if self.schema:
            try:
                if isinstance(input_data, dict):
                    self.schema(**input_data)
                else:
                    self.schema.model_validate(input_data)
                return ToolResult(success=True)
            except ValidationError as e:
                return ToolResult(
                    success=False,
                    error=f"Input validation failed: {str(e)}",
                    error_type=ErrorType.VALIDATION,
                )
        return ToolResult(success=True)

    @abstractmethod
    async def _invoke(
        self,
        input_data: Any,
        context: Optional[ToolExecutionContext] = None,
    ) -> Any:
        """Abstract method: must be implemented by subclasses.

        :param input_data: The validated input data
        :type input_data: Any
        :param context: Optional execution context
        :type context: Optional[ToolExecutionContext]
        :return: The tool execution result
        :rtype: Any
        """
        pass

    async def invoke(
        self,
        input_data: Any,
        context: Optional[ToolExecutionContext] = None,
    ) -> ToolResult:
        """Public invocation method with validation and error handling.

        :param input_data: The input data
        :type input_data: Any
        :param context: Optional execution context
        :type context: Optional[ToolExecutionContext]
        :return: Tool execution result
        :rtype: ToolResult
        """
        start_time = time.time()

        try:
            # Validate input
            validation_result = self.validate_input(input_data)
            if not validation_result.success:
                return validation_result

            # Execute tool
            result = await self._invoke(input_data, context)

            # If result is already a ToolResult, return it
            if isinstance(result, ToolResult):
                return result

            # Otherwise, wrap it in a ToolResult
            return ToolResult(
                success=True,
                data=result,
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                data=getattr(e, "details", None),
                execution_time=time.time() - start_time,
                error_type=ErrorType.EXECUTION,
            )

    def get_metadata(self) -> Dict[str, Any]:
        """Get tool metadata.

        :return: Tool metadata dictionary
        :rtype: Dict[str, Any]
        """
        return {
            "name": self.name,
            "description": self.description,
            "schema": self.schema.model_json_schema() if self.schema else None,
        }

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert tool to JSON schema format for agent consumption.

        This method returns the tool's schema in a format that can be consumed
        by LLM agents for function calling. The format follows the OpenAI function
        calling schema specification.

        :return: JSON schema representation of the tool
        :rtype: Dict[str, Any]
        """
        schema_dict = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description or "",
            },
        }

        if self.schema:
            # Get the JSON schema from Pydantic model
            json_schema = self.schema.model_json_schema()
            # Add parameters to the function schema
            schema_dict["function"]["parameters"] = {
                "type": "object",
                "properties": json_schema.get("properties", {}),
                "required": json_schema.get("required", []),
            }
            # Add descriptions from the schema if available
            if "description" in json_schema:
                schema_dict["function"]["description"] = json_schema["description"]

        return schema_dict


class DynamicTool(BaseTool):
    """Dynamic tool class for creating tools from functions.

    This class allows creating tools dynamically from functions without
    needing to create a new class for each tool.

    :param name: The name of the tool
    :type name: str
    :param func: The function to execute
    :type func: Callable
    :param description: Human-readable description of the tool
    :type description: Optional[str]
    :param schema: Pydantic model class for input validation
    :type schema: Optional[type[BaseModel]]
    """

    def __init__(
        self,
        name: str,
        func: Callable,
        description: Optional[str] = None,
        schema: Optional[type[BaseModel]] = None,
    ):
        """Initialize the dynamic tool.

        :param name: The name of the tool
        :type name: str
        :param func: The function to execute
        :type func: Callable
        :param description: Human-readable description of the tool
        :type description: Optional[str]
        :param schema: Pydantic model class for input validation
        :type schema: Optional[type[BaseModel]]
        """
        super().__init__(name=name, description=description, schema=schema)
        self.func = func

    async def _invoke(
        self,
        input_data: Any,
        context: Optional[ToolExecutionContext] = None,
    ) -> Any:
        """Execute the tool function.

        :param input_data: The validated input data
        :type input_data: Any
        :param context: Optional execution context
        :type context: Optional[ToolExecutionContext]
        :return: The function result
        :rtype: Any
        """
        return await self.func(input_data, context)


def tool(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    schema: Optional[type[BaseModel]] = None,
    get_display: Optional[Callable[[str, Any], str]] = None,
) -> DynamicTool:
    """Tool creation factory function (TypeScript SDK compatible).

    This function creates a DynamicTool from a function, similar to the
    TypeScript SDK's tool() function. This allows bash and fs tools to
    return BaseTool instances that can be converted via adapters.

    Can be used as a decorator or a direct function call:

    As a decorator::

        @tool(name="my_tool", description="My tool")
        async def my_func(input_data, context=None):
            return {"result": "success"}

    As a function::

        def create_bash_tool(context):
            return tool(
                func=lambda input, ctx: execute_bash(input, context),
                name="BashTool",
                description="Execute bash commands",
                schema=BashToolSchema,
            )

    :param func: The async function to wrap as a tool
    :type func: Optional[Callable]
    :param name: The name of the tool
    :type name: Optional[str]
    :param description: Human-readable description of the tool
    :type description: Optional[str]
    :param schema: Pydantic model class for input validation
    :type schema: Optional[type[BaseModel]]
    :param get_display: Optional custom display function
    :type get_display: Optional[Callable[[str, Any], str]]
    :return: DynamicTool instance or decorator function
    :rtype: DynamicTool
    """

    def create_tool(f: Callable) -> DynamicTool:
        """Create the DynamicTool instance."""
        tool_name = name or f.__name__
        dynamic_tool = DynamicTool(
            name=tool_name,
            func=f,
            description=description,
            schema=schema,
        )

        if get_display:
            dynamic_tool.get_display = get_display

        return dynamic_tool

    # If func is provided, create tool directly (function call mode)
    if func is not None:
        return create_tool(func)

    # Otherwise, return decorator (decorator mode)
    return create_tool


def tool_decorator(
    name: str,
    description: Optional[str] = None,
    schema: Optional[type[BaseModel]] = None,
    get_display: Optional[Callable[[str, Any], str]] = None,
) -> Callable:
    """Tool creation helper decorator.

    This decorator makes it easy to create tools from functions.

    :param name: The name of the tool
    :type name: str
    :param description: Human-readable description of the tool
    :type description: Optional[str]
    :param schema: Pydantic model class for input validation
    :type schema: Optional[type[BaseModel]]
    :param get_display: Optional custom display function
    :type get_display: Optional[Callable[[str, Any], str]]
    :return: Decorator function
    :rtype: Callable
    """

    def decorator(func: Callable) -> DynamicTool:
        return tool(
            func=func,
            name=name,
            description=description,
            schema=schema,
            get_display=get_display,
        )

    return decorator


def tools_to_json_schemas(tools: list[BaseTool]) -> list[Dict[str, Any]]:
    """Convert a list of tools to JSON schema format for agent consumption.

    This helper function converts multiple Cloudbase Agent tools to JSON schemas that can
    be used by LLM agents for function calling. Each tool is converted using its
    to_json_schema() method.

    :param tools: List of BaseTool instances to convert
    :type tools: list[BaseTool]
    :return: List of JSON schema representations
    :rtype: list[Dict[str, Any]]

    Example:
        Convert tools for use with an LLM agent::

            from cloudbase_agent.tools import UnsafeLocalCodeExecutor, tools_to_json_schemas

            tools = [
                UnsafeLocalCodeExecutor(),
                # ... other tools
            ]

            schemas = tools_to_json_schemas(tools)
            # Pass schemas to your LLM agent
    """
    return [tool.to_json_schema() for tool in tools]


# Toolkit event types
class ToolkitEvent(BaseModel):
    """Toolkit event model.

    :param type: Event type
    :type type: str
    :param tool: Tool instance (for tool_added events)
    :type tool: Optional[BaseTool]
    :param tool_name: Tool name (for tool_removed/tool_executed events)
    :type tool_name: Optional[str]
    :param result: Tool execution result (for tool_executed events)
    :type result: Optional[ToolResult]
    :param toolkit: Toolkit instance (for toolkit_initialized/toolkit_destroyed events)
    :type toolkit: Optional['BaseToolkit']
    """

    type: str
    tool: Optional[BaseTool] = None
    tool_name: Optional[str] = None
    result: Optional[ToolResult] = None
    toolkit: Optional["BaseToolkit"] = None

    model_config = {"arbitrary_types_allowed": True}


# Event listener type
ToolkitEventListener = Callable[[ToolkitEvent], None]


class BaseToolkit:
    """Base toolkit class for organizing and managing tools.

    This class provides a container for organizing related tools together,
    with support for lifecycle management, event handling, and context sharing.

    :param name: The name of the toolkit
    :type name: str
    :param description: Human-readable description of the toolkit
    :type description: Optional[str]
    :param context: Shared execution context for all tools
    :type context: Optional[ToolExecutionContext]

    Example:
        Create a custom toolkit::

            class WeatherToolkit(BaseToolkit):
                def __init__(self):
                    super().__init__(
                        name="weather",
                        description="Weather-related tools"
                    )
                    self.add_tool(get_location_tool)
                    self.add_tool(get_weather_tool)

                async def on_initialize(self):
                    # Initialize API connections
                    self.api_client = WeatherAPI()

                async def on_destroy(self):
                    # Clean up resources
                    await self.api_client.close()
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        context: Optional[ToolExecutionContext] = None,
    ):
        """Initialize the toolkit.

        :param name: The name of the toolkit
        :type name: str
        :param description: Human-readable description of the toolkit
        :type description: Optional[str]
        :param context: Shared execution context for all tools
        :type context: Optional[ToolExecutionContext]
        """
        self.name = name
        self.description = description
        self._tools: Dict[str, BaseTool] = {}
        self._context = context or {}
        self._event_listeners: list[ToolkitEventListener] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the toolkit.

        This method should be called before using the toolkit. It calls the
        on_initialize hook for subclasses to perform custom initialization.

        :raises RuntimeError: If toolkit is already initialized
        """
        if self._initialized:
            raise RuntimeError(f"Toolkit '{self.name}' is already initialized")

        await self.on_initialize()
        self._initialized = True
        self._emit(ToolkitEvent(type="toolkit_initialized", toolkit=self))

    async def destroy(self) -> None:
        """Destroy the toolkit and clean up resources.

        This method calls the on_destroy hook for subclasses to perform
        custom cleanup, then clears all tools and event listeners.
        """
        if not self._initialized:
            return

        await self.on_destroy()
        self._emit(ToolkitEvent(type="toolkit_destroyed", toolkit=self))
        self._tools.clear()
        self._event_listeners.clear()
        self._initialized = False

    async def on_initialize(self) -> None:
        """Hook for subclasses to perform custom initialization.

        Override this method to initialize resources like database connections,
        API clients, etc.
        """
        pass

    async def on_destroy(self) -> None:
        """Hook for subclasses to perform custom cleanup.

        Override this method to clean up resources like closing connections,
        releasing file handles, etc.
        """
        pass

    def add_tool(self, tool: BaseTool) -> "BaseToolkit":
        """Add a tool to the toolkit.

        :param tool: Tool instance to add
        :type tool: BaseTool
        :return: Self for method chaining
        :rtype: BaseToolkit
        :raises ValueError: If tool with same name already exists
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already exists in toolkit '{self.name}'")

        self._tools[tool.name] = tool
        self._emit(ToolkitEvent(type="tool_added", tool=tool))
        return self

    def add_tools(self, tools: list[BaseTool]) -> "BaseToolkit":
        """Add multiple tools to the toolkit.

        :param tools: List of tool instances to add
        :type tools: list[BaseTool]
        :return: Self for method chaining
        :rtype: BaseToolkit
        """
        for tool in tools:
            self.add_tool(tool)
        return self

    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool from the toolkit.

        :param tool_name: Name of the tool to remove
        :type tool_name: str
        :return: True if tool was removed, False if not found
        :rtype: bool
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            self._emit(ToolkitEvent(type="tool_removed", tool_name=tool_name))
            return True
        return False

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name.

        :param name: Tool name
        :type name: str
        :return: Tool instance or None if not found
        :rtype: Optional[BaseTool]
        """
        return self._tools.get(name)

    def get_tools(self) -> list[BaseTool]:
        """Get all tools in the toolkit.

        :return: List of all tool instances
        :rtype: list[BaseTool]
        """
        return list(self._tools.values())

    def get_tool_names(self) -> list[str]:
        """Get names of all tools in the toolkit.

        :return: List of tool names
        :rtype: list[str]
        """
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """Check if a tool exists in the toolkit.

        :param name: Tool name
        :type name: str
        :return: True if tool exists
        :rtype: bool
        """
        return name in self._tools

    def search_tools(self, query: str) -> list[BaseTool]:
        """Search for tools by name or description.

        :param query: Search query string
        :type query: str
        :return: List of matching tools
        :rtype: list[BaseTool]
        """
        lower_query = query.lower()
        return [
            tool
            for tool in self._tools.values()
            if lower_query in tool.name.lower() or (tool.description and lower_query in tool.description.lower())
        ]

    async def invoke_tool(
        self,
        tool_name: str,
        input_data: Any,
        context: Optional[ToolExecutionContext] = None,
    ) -> ToolResult:
        """Execute a tool by name.

        :param tool_name: Name of the tool to execute
        :type tool_name: str
        :param input_data: Input data for the tool
        :type input_data: Any
        :param context: Optional execution context (merged with toolkit context)
        :type context: Optional[ToolExecutionContext]
        :return: Tool execution result
        :rtype: ToolResult
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found in toolkit '{self.name}'",
            )

        # Merge toolkit context with provided context
        merged_context = {**self._context, **(context or {})}
        result = await tool.invoke(input_data, merged_context)

        self._emit(
            ToolkitEvent(
                type="tool_executed",
                tool_name=tool_name,
                result=result,
            )
        )
        return result

    async def invoke_tools(
        self,
        invocations: list[Dict[str, Any]],
    ) -> list[ToolResult]:
        """Execute multiple tools in parallel.

        :param invocations: List of invocation configs with tool_name, input, and optional context
        :type invocations: list[Dict[str, Any]]
        :return: List of tool execution results
        :rtype: list[ToolResult]

        Example::

            results = await toolkit.invoke_tools([
                {"tool_name": "tool1", "input": {"param": "value1"}},
                {"tool_name": "tool2", "input": {"param": "value2"}},
            ])
        """
        import asyncio

        tasks = [
            self.invoke_tool(
                inv["tool_name"],
                inv["input"],
                inv.get("context"),
            )
            for inv in invocations
        ]
        return await asyncio.gather(*tasks)

    def set_context(self, context: ToolExecutionContext) -> "BaseToolkit":
        """Set or update the shared execution context.

        :param context: Context dictionary to merge with existing context
        :type context: ToolExecutionContext
        :return: Self for method chaining
        :rtype: BaseToolkit
        """
        self._context.update(context)
        return self

    def get_context(self) -> ToolExecutionContext:
        """Get the current execution context.

        :return: Current context dictionary
        :rtype: ToolExecutionContext
        """
        return self._context.copy()

    def add_event_listener(self, listener: ToolkitEventListener) -> "BaseToolkit":
        """Add an event listener.

        :param listener: Event listener function
        :type listener: ToolkitEventListener
        :return: Self for method chaining
        :rtype: BaseToolkit
        """
        self._event_listeners.append(listener)
        return self

    def remove_event_listener(self, listener: ToolkitEventListener) -> bool:
        """Remove an event listener.

        :param listener: Event listener function to remove
        :type listener: ToolkitEventListener
        :return: True if listener was removed
        :rtype: bool
        """
        try:
            self._event_listeners.remove(listener)
            return True
        except ValueError:
            return False

    def _emit(self, event: ToolkitEvent) -> None:
        """Emit an event to all listeners.

        :param event: Event to emit
        :type event: ToolkitEvent
        """
        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"Error in toolkit event listener: {e}")

    def get_metadata(self) -> Dict[str, Any]:
        """Get toolkit metadata.

        :return: Metadata dictionary
        :rtype: Dict[str, Any]
        """
        return {
            "name": self.name,
            "description": self.description,
            "tool_count": len(self._tools),
            "tools": [tool.get_metadata() for tool in self._tools.values()],
            "initialized": self._initialized,
        }

    def validate(self) -> Dict[str, Any]:
        """Validate toolkit integrity.

        :return: Validation result with valid flag and error list
        :rtype: Dict[str, Any]
        """
        errors = []

        if not self._initialized:
            errors.append("Toolkit is not initialized")

        if len(self._tools) == 0:
            errors.append("Toolkit has no tools")

        # Check for duplicate tool names (shouldn't happen with dict, but for safety)
        tool_names = self.get_tool_names()
        if len(tool_names) != len(set(tool_names)):
            duplicates = [name for name in tool_names if tool_names.count(name) > 1]
            errors.append(f"Duplicate tool names: {', '.join(set(duplicates))}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    def clone(self, new_name: Optional[str] = None) -> "BaseToolkit":
        """Clone the toolkit with a new name.

        :param new_name: Name for the cloned toolkit
        :type new_name: Optional[str]
        :return: Cloned toolkit instance
        :rtype: BaseToolkit
        """
        cloned = BaseToolkit(
            name=new_name or f"{self.name}_clone",
            description=self.description,
            context=self._context.copy(),
        )

        # Copy all tools
        for tool in self._tools.values():
            cloned.add_tool(tool)

        return cloned


class ToolkitManager:
    """Manager for multiple toolkits.

    This class provides centralized management of multiple toolkits,
    allowing you to register, search, and manage toolkits globally.

    Example::

        manager = ToolkitManager()

        # Register toolkits
        manager.register(weather_toolkit)
        manager.register(file_toolkit)

        # Initialize all
        await manager.initialize_all()

        # Find tools
        tools = manager.find_tool("get_weather")

        # Clean up
        await manager.destroy_all()
    """

    def __init__(self):
        """Initialize the toolkit manager."""
        self._toolkits: Dict[str, BaseToolkit] = {}

    def register(self, toolkit: BaseToolkit) -> "ToolkitManager":
        """Register a toolkit.

        :param toolkit: Toolkit instance to register
        :type toolkit: BaseToolkit
        :return: Self for method chaining
        :rtype: ToolkitManager
        :raises ValueError: If toolkit with same name already registered
        """
        if toolkit.name in self._toolkits:
            raise ValueError(f"Toolkit '{toolkit.name}' is already registered")

        self._toolkits[toolkit.name] = toolkit
        return self

    async def unregister(self, toolkit_name: str) -> bool:
        """Unregister a toolkit.

        :param toolkit_name: Name of toolkit to unregister
        :type toolkit_name: str
        :return: True if toolkit was unregistered
        :rtype: bool
        """
        toolkit = self._toolkits.get(toolkit_name)
        if toolkit:
            await toolkit.destroy()
            del self._toolkits[toolkit_name]
            return True
        return False

    def get_toolkit(self, name: str) -> Optional[BaseToolkit]:
        """Get a toolkit by name.

        :param name: Toolkit name
        :type name: str
        :return: Toolkit instance or None if not found
        :rtype: Optional[BaseToolkit]
        """
        return self._toolkits.get(name)

    def get_toolkits(self) -> list[BaseToolkit]:
        """Get all registered toolkits.

        :return: List of all toolkit instances
        :rtype: list[BaseToolkit]
        """
        return list(self._toolkits.values())

    def get_all_tools(self) -> list[Dict[str, Any]]:
        """Get all tools from all toolkits.

        :return: List of dicts with toolkit name and tool instance
        :rtype: list[Dict[str, Any]]
        """
        all_tools = []
        for toolkit_name, toolkit in self._toolkits.items():
            for tool in toolkit.get_tools():
                all_tools.append(
                    {
                        "toolkit": toolkit_name,
                        "tool": tool,
                    }
                )
        return all_tools

    def find_tool(self, tool_name: str) -> list[Dict[str, Any]]:
        """Find tools by name across all toolkits.

        :param tool_name: Tool name to search for
        :type tool_name: str
        :return: List of dicts with toolkit name and tool instance
        :rtype: list[Dict[str, Any]]
        """
        return [item for item in self.get_all_tools() if item["tool"].name == tool_name]

    async def initialize_all(self) -> None:
        """Initialize all registered toolkits.

        :raises Exception: If any toolkit initialization fails
        """
        import asyncio

        tasks = [toolkit.initialize() for toolkit in self._toolkits.values()]
        await asyncio.gather(*tasks)

    async def destroy_all(self) -> None:
        """Destroy all registered toolkits and clear the registry."""
        import asyncio

        tasks = [toolkit.destroy() for toolkit in self._toolkits.values()]
        await asyncio.gather(*tasks)
        self._toolkits.clear()


# Singleton toolkit manager instance
toolkit_manager = ToolkitManager()
