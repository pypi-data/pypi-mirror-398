#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP Client Tool - Wraps MCP tools to work within Cloudbase Agent's tool system."""

import asyncio
import json
import time
from typing import Any, Dict, Optional

from .._tools_utils import BaseTool, ErrorType, ToolExecutionContext, ToolResult, handle_tool_error
from .types import MCPAdapterConfig, MCPToolConfig, MCPToolMetadata
from .utils import safe_json_dumps


class MCPClientTool(BaseTool):
    """MCPClientTool wraps an external MCP tool to work within Cloudbase Agent's tool system.

    This class adapts tools from external MCP servers to work seamlessly
    with Cloudbase Agent's tool system. It handles:

    - Schema conversion between MCP and Cloudbase Agent formats
    - Timeout and retry logic
    - Error handling and reporting
    - Optional input/output transformation

    Example::

        from mcp import Client

        # Create MCP tool wrapper
        mcp_tool = MCPClientTool(
            mcp_client=client,
            mcp_tool_metadata={
                "name": "get_weather",
                "description": "Get current weather for a location",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        )

        # Use like any Cloudbase Agent tool
        result = await mcp_tool.invoke({"location": "Beijing"})
    """

    def __init__(
        self,
        mcp_client: Any,
        mcp_tool_metadata: Dict[str, Any] or MCPToolMetadata,
        config: Optional[Dict[str, Any] or MCPToolConfig] = None,
        adapter_config: Optional[Dict[str, Any] or MCPAdapterConfig] = None,
    ):
        """Initialize MCP client tool.

        :param mcp_client: MCP client instance (from @modelcontextprotocol/sdk)
        :param mcp_tool_metadata: MCP tool metadata
        :type mcp_tool_metadata: Dict[str, Any] or MCPToolMetadata
        :param config: Tool configuration with timeout and retries
        :type config: Optional[Dict[str, Any] or MCPToolConfig]
        :param adapter_config: Adapter configuration
        :type adapter_config: Optional[Dict[str, Any] or MCPAdapterConfig]
        """
        # Convert metadata to Pydantic model if it's a dict
        if isinstance(mcp_tool_metadata, dict):
            self.mcp_tool_metadata = MCPToolMetadata(**mcp_tool_metadata)
        else:
            self.mcp_tool_metadata = mcp_tool_metadata

        # Set config with defaults
        if config is None:
            self.config = MCPToolConfig(timeout=30000, retry_count=1)
        elif isinstance(config, dict):
            self.config = MCPToolConfig(timeout=30000, retry_count=1, **config)
        else:
            self.config = config

        # Set adapter config with defaults
        if adapter_config is None:
            self.adapter_config = MCPAdapterConfig()
        elif isinstance(adapter_config, dict):
            self.adapter_config = MCPAdapterConfig(**adapter_config)
        else:
            self.adapter_config = adapter_config

        # Convert MCP input schema to JSON schema for Cloudbase Agent
        input_schema = self._convert_mcp_schema_to_json_schema(self.mcp_tool_metadata.input_schema)

        # Determine tool name (allow override from config)
        tool_name = config.get("name") if isinstance(config, dict) and "name" in config else self.mcp_tool_metadata.name
        tool_description = (
            config.get("description")
            if isinstance(config, dict) and "description" in config
            else self.mcp_tool_metadata.description or f"MCP tool: {self.mcp_tool_metadata.name}"
        )

        # Initialize base tool
        super().__init__(
            name=tool_name,
            description=tool_description,
            schema=None,  # Schema will be handled by _invoke
        )

        self.mcp_client = mcp_client

    def _convert_mcp_schema_to_json_schema(self, mcp_schema: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert MCP JSON Schema to Cloudbase Agent compatible schema.

        Basic conversion - can be expanded for more complex schemas.

        :param mcp_schema: MCP input schema
        :type mcp_schema: Optional[Dict[str, Any]]
        :return: JSON schema compatible with Cloudbase Agent
        :rtype: Dict[str, Any]
        """
        if not mcp_schema:
            return {"type": "object", "properties": {}}

        # MCP already uses JSON Schema format, so we can mostly pass through
        # Just ensure it has the basic structure
        if mcp_schema.get("type") != "object":
            return {"type": "object", "properties": {}}

        return mcp_schema

    async def _invoke(
        self,
        input_data: Any,
        context: Optional[ToolExecutionContext] = None,
    ) -> ToolResult:
        """Execute the MCP tool.

        :param input_data: Input data for the tool
        :type input_data: Any
        :param context: Execution context
        :type context: Optional[ToolExecutionContext]
        :return: Tool execution result
        :rtype: ToolResult
        """
        start_time = time.time()

        try:
            # Transform input if configured
            transformed_input = (
                self.adapter_config.tool_config.transform_input(input_data)
                if self.adapter_config.tool_config.transform_input
                else input_data
            )

            # Call the MCP tool with retry logic
            last_error: Optional[Exception] = None
            result = None

            for attempt in range(self.config.retry_count + 1):
                try:
                    # Create timeout task
                    timeout_seconds = self.config.timeout / 1000.0

                    # Call MCP tool
                    result = await asyncio.wait_for(
                        self.mcp_client.call_tool(name=self.mcp_tool_metadata.name, arguments=transformed_input),
                        timeout=timeout_seconds,
                    )
                    break  # Success, exit retry loop

                except asyncio.TimeoutError:
                    last_error = Exception("MCP tool call timeout")
                    if attempt < self.config.retry_count:
                        # Wait before retry
                        await asyncio.sleep((attempt + 1) * 1.0)

                except Exception as error:
                    last_error = error
                    if attempt < self.config.retry_count:
                        # Wait before retry
                        await asyncio.sleep((attempt + 1) * 1.0)

            if result is None:
                raise last_error or Exception("MCP tool call failed after retries")

            # Handle MCP error response
            if hasattr(result, "isError") and result.isError:
                error_text = "\n".join(c.text for c in result.content if hasattr(c, "type") and c.type == "text")

                return handle_tool_error(
                    Exception(error_text),
                    f"MCP tool '{self.mcp_tool_metadata.name}' execution",
                    ErrorType.EXECUTION,
                )

            # Process successful result
            text_content = "\n".join(c.text for c in result.content if hasattr(c, "type") and c.type == "text")

            processed_output: Any = text_content

            # Try to parse JSON if it looks like JSON
            if text_content.strip().startswith("{") or text_content.strip().startswith("["):
                try:
                    processed_output = json.loads(text_content)
                except:
                    # Keep as text if JSON parsing fails
                    pass

            # Transform output if configured
            if self.adapter_config.tool_config.transform_output:
                processed_output = self.adapter_config.tool_config.transform_output(processed_output)

            # Include metadata if configured (not in adapter_config anymore, always include)
            execution_time = time.time() - start_time
            result_data = {
                "output": processed_output,
                "metadata": {
                    "mcpTool": self.mcp_tool_metadata.name,
                    "executionTime": execution_time * 1000,  # Convert to ms
                    "contentTypes": [c.type for c in result.content if hasattr(c, "type")],
                },
            }

            return ToolResult(
                success=True,
                data=result_data,
                execution_time=execution_time,
            )

        except Exception as error:
            execution_time = time.time() - start_time
            return handle_tool_error(
                error,
                f"MCP tool '{self.mcp_tool_metadata.name}' execution",
                ErrorType.EXECUTION,
                metadata={
                    "mcpTool": self.mcp_tool_metadata.name,
                    "input": input_data,
                    "executionTime": execution_time * 1000,
                },
            )

    def get_display(self, params: Dict[str, Any]) -> str:
        """Get display information for the tool.

        :param params: Parameters including name and input
        :type params: Dict[str, Any]
        :return: Display string
        :rtype: str
        """
        input_data = params.get("input", {})
        return f"> Using MCP tool '{self.mcp_tool_metadata.name}': {safe_json_dumps(input_data)}"

    def get_mcp_metadata(self) -> MCPToolMetadata:
        """Get MCP-specific metadata.

        :return: MCP tool metadata
        :rtype: MCPToolMetadata
        """
        return MCPToolMetadata(
            name=self.mcp_tool_metadata.name,
            description=self.mcp_tool_metadata.description,
            input_schema=self.mcp_tool_metadata.input_schema,
        )

    def get_metadata(self) -> Dict[str, Any]:
        """Get combined metadata (Cloudbase Agent + MCP).

        :return: Combined metadata
        :rtype: Dict[str, Any]
        """
        base_metadata = super().get_metadata()
        return {
            **base_metadata,
            "mcp": {
                "originalName": self.mcp_tool_metadata.name,
                "originalDescription": self.mcp_tool_metadata.description,
                "inputSchema": self.mcp_tool_metadata.input_schema,
                "config": {
                    "timeout": self.config.timeout,
                    "retries": self.config.retry_count,
                },
            },
        }

    def is_connected(self) -> bool:
        """Check if the MCP client is connected.

        :return: True if client is connected
        :rtype: bool
        """
        return self.mcp_client is not None and hasattr(self.mcp_client, "call_tool")

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update tool configuration.

        :param new_config: New configuration values
        :type new_config: Dict[str, Any]
        """
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def update_adapter_config(self, new_adapter_config: Dict[str, Any]) -> None:
        """Update adapter configuration.

        :param new_adapter_config: New adapter configuration values
        :type new_adapter_config: Dict[str, Any]
        """
        for key, value in new_adapter_config.items():
            if hasattr(self.adapter_config, key):
                setattr(self.adapter_config, key, value)
