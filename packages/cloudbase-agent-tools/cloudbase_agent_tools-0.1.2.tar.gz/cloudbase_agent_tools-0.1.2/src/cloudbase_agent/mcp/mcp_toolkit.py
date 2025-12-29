#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP Toolkit.

This module provides a toolkit for managing MCP tools from multiple servers.
"""

from typing import Any, Dict, List, Optional

from .._tools_utils import BaseToolkit, ToolExecutionContext
from .client_tool import MCPClientTool
from .mcp_client_manager import MCPClientManager
from .types import MCPAdapterConfig, MCPEventListener, MCPToolConfig


class MCPToolkit(BaseToolkit):
    """Toolkit for managing MCP tools from multiple servers.

    This toolkit wraps the MCPClientManager and provides a unified
    interface for working with tools from multiple MCP servers.

    Example::

        toolkit = MCPToolkit("mcp-tools")

        # Add server
        await toolkit.add_server("weather", {
            "name": "weather-service",
            "version": "1.0.0",
            "transport": {
                "type": "stdio",
                "command": "weather-mcp-server",
                "args": []
            }
        })

        # Initialize
        await toolkit.initialize()

        # Use tools
        tools = toolkit.get_tools()
        result = await toolkit.invoke_tool("weather_get_weather", {"city": "Beijing"})

        # Cleanup
        await toolkit.destroy()
    """

    def __init__(
        self,
        name: str = "mcp-toolkit",
        description: Optional[str] = None,
        context: Optional[ToolExecutionContext] = None,
        adapter_config: Optional[MCPAdapterConfig] = None,
    ):
        """Initialize the MCP toolkit.

        :param name: Toolkit name
        :type name: str
        :param description: Toolkit description
        :type description: Optional[str]
        :param context: Shared execution context
        :type context: Optional[ToolExecutionContext]
        :param adapter_config: Adapter configuration
        :type adapter_config: Optional[MCPAdapterConfig]
        """
        super().__init__(
            name=name,
            description=description or "Toolkit for MCP tools from multiple servers",
            context=context,
        )

        self.adapter_config = adapter_config or MCPAdapterConfig()
        self.manager = MCPClientManager()
        self._server_configs: Dict[str, Dict[str, Any]] = {}

    async def on_initialize(self) -> None:
        """Initialize the toolkit by connecting to all configured servers."""
        # Servers are added via add_server, which handles connection
        pass

    async def on_destroy(self) -> None:
        """Clean up by disconnecting from all servers."""
        await self.manager.disconnect_all()
        self._server_configs.clear()

    async def add_server(
        self,
        server_id: str,
        config: Dict[str, Any],
        tool_config: Optional[MCPToolConfig] = None,
    ) -> "MCPToolkit":
        """Add an MCP server and load its tools.

        :param server_id: Unique identifier for the server
        :type server_id: str
        :param config: Server configuration
        :type config: Dict[str, Any]
        :param tool_config: Optional tool configuration
        :type tool_config: Optional[MCPToolConfig]
        :return: Self for method chaining
        :rtype: MCPToolkit
        """
        # Store config
        self._server_configs[server_id] = {
            "config": config,
            "tool_config": tool_config or self.adapter_config.tool_config,
        }

        # Add to manager (returns None on success, raises on failure)
        await self.manager.add_server(server_id, config)

        # Load tools from this server
        await self._load_tools_from_server(server_id)

        return self

    async def remove_server(self, server_id: str) -> bool:
        """Remove an MCP server and its tools.

        :param server_id: Server identifier
        :type server_id: str
        :return: True if server was removed
        :rtype: bool
        """
        if server_id not in self._server_configs:
            return False

        # Remove all tools from this server
        tools_to_remove = [tool_name for tool_name in self.get_tool_names() if tool_name.startswith(f"{server_id}_")]

        for tool_name in tools_to_remove:
            self.remove_tool(tool_name)

        # Remove from manager
        await self.manager.remove_server(server_id)

        # Remove config
        del self._server_configs[server_id]

        return True

    async def _load_tools_from_server(self, server_id: str) -> None:
        """Load tools from a specific server.

        :param server_id: Server identifier
        :type server_id: str
        """
        # Get tools from manager
        tool_dicts = self.manager.get_server_tools(server_id)

        # Convert to metadata objects
        from .types import MCPToolMetadata

        tool_metadatas = [MCPToolMetadata(**tool_dict) for tool_dict in tool_dicts]

        # Get tool config for this server
        server_config = self._server_configs[server_id]
        tool_config = server_config["tool_config"]

        # Create MCPClientTool for each tool
        for metadata in tool_metadatas:
            # Create a client wrapper for this specific tool
            client_wrapper = MCPClientWrapper(self.manager, server_id)

            # Create tool
            tool = MCPClientTool(
                mcp_client=client_wrapper,
                mcp_tool_metadata=metadata,
                config=tool_config,
            )

            # Apply name prefix if configured
            if self.adapter_config.name_prefix:
                tool.name = f"{self.adapter_config.name_prefix}{tool.name}"

            # Apply description prefix if configured
            if self.adapter_config.description_prefix and tool.description:
                tool.description = f"{self.adapter_config.description_prefix}{tool.description}"

            # Add to toolkit
            try:
                self.add_tool(tool)
            except ValueError:
                # Tool already exists, skip
                pass

    async def refresh_tools(self, server_id: Optional[str] = None) -> None:
        """Refresh tools from servers.

        :param server_id: Optional server ID to refresh, or None for all
        :type server_id: Optional[str]
        """
        if server_id:
            # Refresh specific server
            if server_id in self._server_configs:
                # Remove existing tools
                tools_to_remove = [
                    tool_name for tool_name in self.get_tool_names() if tool_name.startswith(f"{server_id}_")
                ]
                for tool_name in tools_to_remove:
                    self.remove_tool(tool_name)

                # Reload tools
                await self._load_tools_from_server(server_id)
        else:
            # Refresh all servers
            for sid in list(self._server_configs.keys()):
                await self.refresh_tools(sid)

    def add_event_listener(self, listener: MCPEventListener) -> "MCPToolkit":
        """Add an event listener to the manager.

        :param listener: Event listener function
        :type listener: MCPEventListener
        :return: Self for method chaining
        :rtype: MCPToolkit
        """
        self.manager.add_event_listener(listener)
        return self

    def remove_event_listener(self, listener: MCPEventListener) -> bool:
        """Remove an event listener from the manager.

        :param listener: Event listener function
        :type listener: MCPEventListener
        :return: True if listener was removed
        :rtype: bool
        """
        return self.manager.remove_event_listener(listener)

    def get_server_ids(self) -> List[str]:
        """Get list of connected server IDs.

        :return: List of server IDs
        :rtype: List[str]
        """
        return list(self._server_configs.keys())

    def get_server_statuses(self) -> Dict[str, bool]:
        """Get connection status for all servers.

        :return: Dictionary of server_id to connection status
        :rtype: Dict[str, bool]
        """
        return self.manager.get_connection_status()

    def get_metadata(self) -> Dict[str, Any]:
        """Get toolkit metadata including server information.

        :return: Metadata dictionary
        :rtype: Dict[str, Any]
        """
        base_metadata = super().get_metadata()
        base_metadata.update(
            {
                "servers": self.get_server_ids(),
                "server_statuses": self.get_server_statuses(),
                "adapter_config": {
                    "name_prefix": self.adapter_config.name_prefix,
                    "description_prefix": self.adapter_config.description_prefix,
                },
            }
        )
        return base_metadata


class MCPClientWrapper:
    """Wrapper to provide a consistent client interface for MCPClientTool.

    This wrapper allows MCPClientTool to call tools through the manager.
    """

    def __init__(self, manager: MCPClientManager, server_id: str):
        """Initialize the client wrapper.

        :param manager: MCP client manager
        :type manager: MCPClientManager
        :param server_id: Server identifier
        :type server_id: str
        """
        self.manager = manager
        self.server_id = server_id

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool through the manager.

        :param tool_name: Tool name
        :type tool_name: str
        :param arguments: Tool arguments
        :type arguments: Dict[str, Any]
        :return: Tool result
        :rtype: Any
        """
        return await self.manager.call_tool(self.server_id, tool_name, arguments)


__all__ = ["MCPToolkit", "MCPClientWrapper"]
