#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP Client Manager - manages connections to external MCP servers."""

import asyncio
import time
from typing import Any, Dict, List, Optional, Set

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .types import (
    MCPClientConfig,
    MCPClientStatus,
    MCPConnectionOptions,
    MCPEvent,
    MCPEventListener,
    MCPEventType,
    MCPToolMetadata,
    MCPTransportType,
)


class MCPClientManager:
    """MCP Client Manager - manages connections to external MCP servers.

    This class manages connections to multiple MCP servers, handles
    reconnection, heartbeat, and provides a unified interface for
    tool discovery and execution.

    Example::

        manager = MCPClientManager()

        # Add server
        await manager.add_server("weather", {
            "name": "weather-service",
            "version": "1.0.0",
            "transport": {
                "type": "stdio",
                "command": "weather-mcp-server",
                "args": []
            }
        })

        # Get tools
        tools = manager.get_server_tools("weather")

        # Create client tools
        client_tools = manager.create_client_tools("weather")

        # Call tool
        result = await manager.call_tool("weather", "get_weather", {"city": "Beijing"})

        # Cleanup
        await manager.disconnect_all()
    """

    def __init__(self):
        """Initialize the MCP client manager."""
        self.clients: Dict[str, ClientSession] = {}
        self.transports: Dict[str, Any] = {}  # Store transport read/write handles
        self.connections: Dict[str, MCPClientConfig] = {}
        self.available_tools: Dict[str, List[Dict[str, Any]]] = {}  # server_id -> list of MCP tools
        self.event_listeners: Set[MCPEventListener] = set()

        # Enhanced connection management
        self.connection_options: Dict[str, MCPConnectionOptions] = {}
        self.server_status: Dict[str, str] = {}  # server_id -> status string
        self.reconnect_timers: Dict[str, asyncio.Task] = {}
        self.heartbeat_timers: Dict[str, asyncio.Task] = {}

    async def add_server(
        self,
        server_id: str,
        config: Dict[str, Any],
        connection_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a new MCP server connection.

        :param server_id: Unique identifier for the server
        :type server_id: str
        :param config: Server configuration
        :type config: Dict[str, Any]
        :param connection_options: Connection options
        :type connection_options: Optional[Dict[str, Any]]
        :raises ValueError: If server already exists
        """
        if server_id in self.clients:
            raise ValueError(f"Server '{server_id}' is already registered")

        # Parse config
        client_config = MCPClientConfig(**config)

        # Set up connection options with defaults
        options = MCPConnectionOptions(**(connection_options or {}))

        # Initialize server status
        self.server_status[server_id] = MCPClientStatus.DISCONNECTED
        self.connections[server_id] = client_config
        self.connection_options[server_id] = options

        try:
            # Connect to server
            await self._connect_server(server_id)

            # Load server tools
            await self._load_server_tools(server_id)

            # Set up heartbeat if configured
            if options.heartbeat_interval > 0:
                self._setup_heartbeat(server_id)

        except Exception as error:
            # Clean up on failure
            self._cleanup_server(server_id)
            raise error

    async def _connect_server(self, server_id: str) -> None:
        """Connect to a specific server.

        :param server_id: Server identifier
        :type server_id: str
        """
        config = self.connections.get(server_id)
        if not config:
            raise ValueError(f"Server '{server_id}' not found")

        # Check if already connected
        if self.server_status.get(server_id) == MCPClientStatus.CONNECTED and server_id in self.transports:
            print(f"[MCPClientManager] Server '{server_id}' is already connected")
            return

        # Create transport based on configuration
        transport_type = config.transport.type

        if transport_type == MCPTransportType.STDIO:
            await self._connect_stdio(server_id)
        elif transport_type == MCPTransportType.MEMORY:
            await self._connect_memory(server_id)
        elif transport_type == MCPTransportType.SSE:
            raise NotImplementedError("SSE transport not yet implemented in Python SDK")
        elif transport_type == MCPTransportType.STREAMABLE_HTTP:
            raise NotImplementedError("StreamableHTTP transport not yet implemented in Python SDK")
        else:
            raise ValueError(f"Unknown transport type: {transport_type}")

        # Update status
        self.server_status[server_id] = MCPClientStatus.CONNECTED

        # Emit connected event
        self._emit(
            {
                "type": MCPEventType.CONNECTED,
                "server_id": server_id,
                "timestamp": time.time(),
            }
        )

    async def _connect_stdio(self, server_id: str) -> None:
        """Connect using stdio transport.

        :param server_id: Server identifier
        :type server_id: str
        """
        config = self.connections[server_id]
        transport = config.transport

        # Create stdio client
        server_params = StdioServerParameters(
            command=transport.command,
            args=transport.args or [],
            env=transport.env if hasattr(transport, "env") else None,
        )

        stdio = stdio_client(server_params)
        read, write = await stdio.__aenter__()

        # Create session
        session = ClientSession(read, write)
        await session.__aenter__()

        # Initialize session
        await session.initialize()

        # Store session and transport handles
        self.clients[server_id] = session
        self.transports[server_id] = (read, write, stdio)

    async def _connect_memory(self, server_id: str) -> None:
        """Connect using memory transport.

        :param server_id: Server identifier
        :type server_id: str
        """
        from .agkit_mcp_server import MemoryTransportRegistry

        config = self.connections[server_id]
        transport = config.transport
        memory_id = transport.memory_id

        # Get memory transport from registry
        registry = MemoryTransportRegistry.get_instance()
        read_stream, write_stream = registry.get_client_transport(memory_id)

        if not read_stream or not write_stream:
            raise ValueError(f"Memory transport '{memory_id}' not found in registry")

        # Create session
        session = ClientSession(read_stream, write_stream)
        await session.__aenter__()

        # Initialize session
        await session.initialize()

        # Store session
        self.clients[server_id] = session
        self.transports[server_id] = (read_stream, write_stream, None)

    async def _load_server_tools(self, server_id: str) -> None:
        """Load tools from a specific server.

        :param server_id: Server identifier
        :type server_id: str
        """
        client = self.clients.get(server_id)
        if not client:
            raise ValueError(f"Server '{server_id}' not found")

        try:
            # List tools from server
            response = await client.list_tools()

            # Store tools (as raw MCP tool objects)
            self.available_tools[server_id] = [
                {
                    "name": tool.name,
                    "description": tool.description if hasattr(tool, "description") else "",
                    "inputSchema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
                }
                for tool in response.tools
            ]

            # Emit tool discovered events
            for tool in response.tools:
                self._emit(
                    {
                        "type": MCPEventType.TOOL_DISCOVERED,
                        "tool_name": tool.name,
                        "data": {
                            "name": tool.name,
                            "description": tool.description if hasattr(tool, "description") else "",
                            "inputSchema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
                        },
                        "timestamp": time.time(),
                    }
                )

        except Exception as error:
            self._emit(
                {
                    "type": MCPEventType.ERROR,
                    "error": str(error),
                    "data": {"context": f"load_tools:{server_id}"},
                    "timestamp": time.time(),
                }
            )
            raise error

    def get_all_tools(self, server_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all available tools from all connected servers.

        :param server_id: Optional server ID to filter by
        :type server_id: Optional[str]
        :return: List of tools with server ID
        :rtype: List[Dict[str, Any]]
        """
        all_tools = []

        if server_id:
            tools = self.available_tools.get(server_id, [])
            for tool in tools:
                all_tools.append(
                    {
                        "serverId": server_id,
                        "tool": tool,
                    }
                )
        else:
            for _server_id, tools in self.available_tools.items():
                for tool in tools:
                    all_tools.append(
                        {
                            "serverId": _server_id,
                            "tool": tool,
                        }
                    )

        return all_tools

    def get_server_tools(self, server_id: str) -> List[Dict[str, Any]]:
        """Get tools from a specific server.

        :param server_id: Server identifier
        :type server_id: str
        :return: List of MCP tool objects
        :rtype: List[Dict[str, Any]]
        """
        return self.available_tools.get(server_id, [])

    def create_client_tools(self, server_id: Optional[str] = None) -> List["MCPClientTool"]:
        """Create MCPClientTool instances for all available tools.

        :param server_id: Optional server ID to filter by
        :type server_id: Optional[str]
        :return: List of MCPClientTool instances
        :rtype: List[MCPClientTool]
        """
        client_tools = []

        for tool_info in self.get_all_tools(server_id):
            _server_id = tool_info["serverId"]
            tool = tool_info["tool"]

            # Use server:tool format as Cloudbase Agent tool name
            agkit_tool_name = f"{_server_id}:{tool['name']}"

            client_tool = self.create_client_tool(_server_id, tool["name"], agkit_tool_name)
            client_tools.append(client_tool)

        return client_tools

    def create_client_tool(
        self,
        server_id: str,
        tool_name: str,
        agkit_tool_name: Optional[str] = None,
    ) -> "MCPClientTool":
        """Create a specific client tool.

        :param server_id: Server identifier
        :type server_id: str
        :param tool_name: MCP tool name
        :type tool_name: str
        :param agkit_tool_name: Optional custom Cloudbase Agent tool name
        :type agkit_tool_name: Optional[str]
        :return: MCPClientTool instance
        :rtype: MCPClientTool
        """
        from .client_tool import MCPClientTool

        tools = self.get_server_tools(server_id)
        tool = None

        for t in tools:
            if t["name"] == tool_name:
                tool = t
                break

        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found on server '{server_id}'")

        tool_metadata = MCPToolMetadata(
            name=tool["name"],
            description=tool.get("description", ""),
            input_schema=tool.get("inputSchema"),
        )

        # Create a client wrapper that uses this manager's client
        client_wrapper = _MCPClientWrapper(self, server_id)

        # Create tool config with custom name if provided
        config = {}
        if agkit_tool_name:
            config["name"] = agkit_tool_name

        return MCPClientTool(
            mcp_client=client_wrapper,
            mcp_tool_metadata=tool_metadata,
            config=config,
        )

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Call a tool on a specific server.

        :param server_id: Server identifier
        :type server_id: str
        :param tool_name: Tool name
        :type tool_name: str
        :param arguments: Tool arguments
        :type arguments: Optional[Dict[str, Any]]
        :return: Tool result
        :rtype: Any
        """
        client = self.clients.get(server_id)
        if not client:
            raise ValueError(f"Server '{server_id}' not found")

        if self.server_status.get(server_id) != MCPClientStatus.CONNECTED:
            raise RuntimeError(f"Server '{server_id}' is not connected")

        # Emit tool called event
        self._emit(
            {
                "type": MCPEventType.TOOL_CALLED,
                "tool_name": tool_name,
                "data": {"arguments": arguments or {}},
                "timestamp": time.time(),
            }
        )

        try:
            # Call tool
            result = await client.call_tool(tool_name, arguments or {})

            # Emit tool result event
            self._emit(
                {
                    "type": MCPEventType.TOOL_RESULT,
                    "tool_name": tool_name,
                    "data": {"result": result},
                    "timestamp": time.time(),
                }
            )

            return result

        except Exception as error:
            # Emit error event
            self._emit(
                {
                    "type": MCPEventType.ERROR,
                    "error": str(error),
                    "data": {"context": f"call_tool:{server_id}:{tool_name}"},
                    "timestamp": time.time(),
                }
            )
            raise error

    async def remove_server(self, server_id: str) -> bool:
        """Remove and disconnect from an MCP server.

        :param server_id: Server identifier
        :type server_id: str
        :return: True if server was removed
        :rtype: bool
        """
        if server_id not in self.clients:
            return False

        # Stop heartbeat
        if server_id in self.heartbeat_timers:
            self.heartbeat_timers[server_id].cancel()
            del self.heartbeat_timers[server_id]

        # Disconnect
        await self._disconnect_server(server_id)

        # Remove from registries
        self._cleanup_server(server_id)

        return True

    async def _disconnect_server(self, server_id: str) -> None:
        """Disconnect from a specific server.

        :param server_id: Server identifier
        :type server_id: str
        """
        if server_id not in self.clients:
            return

        try:
            # Get session and transport
            session = self.clients.get(server_id)
            transport_tuple = self.transports.get(server_id)

            # Close session
            if session:
                try:
                    await session.__aexit__(None, None, None)
                except:
                    pass

            # Close transport
            if transport_tuple:
                read, write, stdio = transport_tuple
                if stdio:
                    try:
                        await stdio.__aexit__(None, None, None)
                    except:
                        pass

            # Update status
            self.server_status[server_id] = MCPClientStatus.DISCONNECTED

            # Emit disconnected event
            self._emit(
                {
                    "type": MCPEventType.DISCONNECTED,
                    "server_id": server_id,
                    "timestamp": time.time(),
                }
            )

        except Exception as e:
            print(f"Error disconnecting from server {server_id}: {e}")

    def _cleanup_server(self, server_id: str) -> None:
        """Clean up server resources.

        :param server_id: Server identifier
        :type server_id: str
        """
        self.clients.pop(server_id, None)
        self.transports.pop(server_id, None)
        self.connections.pop(server_id, None)
        self.available_tools.pop(server_id, None)
        self.connection_options.pop(server_id, None)
        self.server_status.pop(server_id, None)
        self.reconnect_timers.pop(server_id, None)
        self.heartbeat_timers.pop(server_id, None)

    def _setup_heartbeat(self, server_id: str) -> None:
        """Set up heartbeat for a server.

        :param server_id: Server identifier
        :type server_id: str
        """

        async def heartbeat_loop():
            options = self.connection_options.get(server_id)
            if not options:
                return

            interval = options.heartbeat_interval / 1000.0  # Convert ms to seconds

            while True:
                try:
                    await asyncio.sleep(interval)

                    # Check if still connected
                    if self.server_status.get(server_id) == MCPClientStatus.CONNECTED:
                        # Ping server by listing tools
                        client = self.clients.get(server_id)
                        if client:
                            try:
                                await client.list_tools()
                            except Exception as e:
                                print(f"Heartbeat failed for server {server_id}: {e}")
                                # Attempt reconnect if configured
                                if options.auto_reconnect:
                                    await self._reconnect_server(server_id)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"Error in heartbeat for server {server_id}: {e}")

        task = asyncio.create_task(heartbeat_loop())
        self.heartbeat_timers[server_id] = task

    async def _reconnect_server(self, server_id: str) -> bool:
        """Reconnect to a server.

        :param server_id: Server identifier
        :type server_id: str
        :return: True if reconnection successful
        :rtype: bool
        """
        options = self.connection_options.get(server_id)
        if not options:
            return False

        # Update status
        self.server_status[server_id] = MCPClientStatus.RECONNECTING

        # Emit reconnecting event
        self._emit(
            {
                "type": MCPEventType.RECONNECTING,
                "server_id": server_id,
                "timestamp": time.time(),
            }
        )

        # Disconnect first
        await self._disconnect_server(server_id)

        # Try to reconnect
        try:
            await self._connect_server(server_id)
            await self._load_server_tools(server_id)
            return True
        except Exception as e:
            print(f"Reconnection failed for server {server_id}: {e}")
            return False

    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        for server_id in list(self.clients.keys()):
            await self._disconnect_server(server_id)

        # Clear all timers
        for task in self.heartbeat_timers.values():
            task.cancel()
        self.heartbeat_timers.clear()

        for task in self.reconnect_timers.values():
            task.cancel()
        self.reconnect_timers.clear()

    def add_event_listener(self, listener: MCPEventListener) -> None:
        """Add an event listener.

        :param listener: Event listener function
        :type listener: MCPEventListener
        """
        self.event_listeners.add(listener)

    def remove_event_listener(self, listener: MCPEventListener) -> None:
        """Remove an event listener.

        :param listener: Event listener function
        :type listener: MCPEventListener
        """
        self.event_listeners.discard(listener)

    def _emit(self, event: Dict[str, Any]) -> None:
        """Emit an event to all listeners.

        :param event: Event data
        :type event: Dict[str, Any]
        """
        mcp_event = MCPEvent(**event)
        for listener in self.event_listeners:
            try:
                listener(mcp_event)
            except Exception as e:
                print(f"Error in event listener: {e}")

    def is_server_connected(self, server_id: str) -> bool:
        """Check if a server is connected.

        :param server_id: Server identifier
        :type server_id: str
        :return: True if connected
        :rtype: bool
        """
        return self.server_status.get(server_id) == MCPClientStatus.CONNECTED

    def get_connection_status(self) -> Dict[str, bool]:
        """Get connection status for all servers.

        :return: Dictionary of server_id to connection status
        :rtype: Dict[str, bool]
        """
        return {server_id: self.is_server_connected(server_id) for server_id in self.clients.keys()}

    async def refresh(self) -> None:
        """Refresh all server connections."""
        server_ids = list(self.clients.keys())

        for server_id in server_ids:
            try:
                await self._disconnect_server(server_id)
                await self._connect_server(server_id)
                await self._load_server_tools(server_id)
            except Exception as e:
                print(f"Error refreshing server '{server_id}': {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about connected servers and tools.

        :return: Statistics dictionary
        :rtype: Dict[str, Any]
        """
        total_tools = sum(len(tools) for tools in self.available_tools.values())

        return {
            "connected_servers": len([sid for sid in self.clients.keys() if self.is_server_connected(sid)]),
            "total_servers": len(self.clients),
            "total_tools": total_tools,
            "server_status": self.get_connection_status(),
        }


class _MCPClientWrapper:
    """Wrapper for MCP client that forwards calls to the manager.

    This allows MCPClientTool to work with the manager's client pool.
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

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool via the manager.

        :param name: Tool name
        :type name: str
        :param arguments: Tool arguments
        :type arguments: Dict[str, Any]
        :return: Tool result
        :rtype: Any
        """
        return await self.manager.call_tool(self.server_id, name, arguments)
