#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cloudbase Agent MCP Server.

This module provides an MCP server that exposes Cloudbase Agent tools.
"""

import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import anyio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .._tools_utils import BaseTool
from .types import MCPEvent, MCPEventListener, MCPEventType, MCPServerConfig, MCPToolRegistration
from .utils import pydantic_to_json_schema

# Type aliases for transport setup callbacks
SSETransportSetup = Callable[["AGKitMCPServer", Callable], Any]
StreamableHTTPTransportSetup = Callable[["AGKitMCPServer", Callable], Any]


# Note: AsyncQueueStream is no longer needed as we use anyio's MemoryObjectStream directly


class MemoryTransportRegistry:
    """Global registry for memory transports.

    This registry manages in-memory transport pairs for testing and
    same-process communication between MCP clients and servers.
    """

    _instance: Optional["MemoryTransportRegistry"] = None

    def __init__(self):
        """Initialize the registry."""
        self._transports: Dict[str, Tuple[Any, Any]] = {}
        self._servers: Dict[str, "AGKitMCPServer"] = {}

    @classmethod
    def get_instance(cls) -> "MemoryTransportRegistry":
        """Get the singleton instance.

        :return: Registry instance
        :rtype: MemoryTransportRegistry
        """
        if cls._instance is None:
            cls._instance = MemoryTransportRegistry()
        return cls._instance

    def register_server(self, memory_id: str, server: "AGKitMCPServer") -> None:
        """Register a server with a memory ID.

        :param memory_id: Memory transport identifier
        :type memory_id: str
        :param server: Server instance
        :type server: AGKitMCPServer
        """
        self._servers[memory_id] = server

    def unregister_server(self, memory_id: str) -> None:
        """Unregister a server.

        :param memory_id: Memory transport identifier
        :type memory_id: str
        """
        self._servers.pop(memory_id, None)
        self._transports.pop(memory_id, None)

    def get_server(self, memory_id: str) -> Optional["AGKitMCPServer"]:
        """Get a registered server.

        :param memory_id: Memory transport identifier
        :type memory_id: str
        :return: Server instance or None
        :rtype: Optional[AGKitMCPServer]
        """
        return self._servers.get(memory_id)

    def create_transport_pair(self, memory_id: str) -> Tuple[Any, Any]:
        """Create or get a transport pair for in-memory communication.

        :param memory_id: Memory transport identifier
        :type memory_id: str
        :return: Tuple of (server_transport, client_transport)
        :rtype: Tuple[Any, Any]
        """
        if memory_id not in self._transports:
            # Create in-memory transport pair using anyio memory streams
            # Server -> Client stream
            server_send, client_recv = anyio.create_memory_object_stream(max_buffer_size=100)
            # Client -> Server stream
            client_send, server_recv = anyio.create_memory_object_stream(max_buffer_size=100)

            # Create transport objects
            # Server uses: read from client, write to client
            server_transport = (server_recv, server_send)
            # Client uses: read from server, write to server
            client_transport = (client_recv, client_send)

            self._transports[memory_id] = (server_transport, client_transport)

        return self._transports[memory_id]

    def get_client_transport(self, memory_id: str) -> Any:
        """Get the client-side transport.

        :param memory_id: Memory transport identifier
        :type memory_id: str
        :return: Client transport
        :rtype: Any
        :raises ValueError: If transport pair not found
        """
        if memory_id not in self._transports:
            raise ValueError(f"No transport pair found with memory ID: {memory_id}")
        return self._transports[memory_id][1]

    def get_server_transport(self, memory_id: str) -> Any:
        """Get the server-side transport.

        :param memory_id: Memory transport identifier
        :type memory_id: str
        :return: Server transport
        :rtype: Any
        :raises ValueError: If transport pair not found
        """
        if memory_id not in self._transports:
            raise ValueError(f"No transport pair found with memory ID: {memory_id}")
        return self._transports[memory_id][0]

    async def call_tool(
        self,
        memory_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """Call a tool directly via memory transport.

        :param memory_id: Memory transport identifier
        :type memory_id: str
        :param tool_name: Tool name
        :type tool_name: str
        :param arguments: Tool arguments
        :type arguments: Dict[str, Any]
        :return: Tool result
        :rtype: Any
        :raises ValueError: If server not found
        """
        server = self._servers.get(memory_id)
        if not server:
            raise ValueError(f"No MCP server found with memory ID: {memory_id}")

        return await server._handle_call_tool(tool_name, arguments)

    async def list_tools(self, memory_id: str) -> List[Tool]:
        """List tools from a server via memory transport.

        :param memory_id: Memory transport identifier
        :type memory_id: str
        :return: List of tools
        :rtype: List[Tool]
        :raises ValueError: If server not found
        """
        server = self._servers.get(memory_id)
        if not server:
            raise ValueError(f"No MCP server found with memory ID: {memory_id}")

        return await server._handle_list_tools()


class AGKitMCPServer:
    """MCP server that exposes Cloudbase Agent tools.

    This server allows Cloudbase Agent tools to be used by any MCP client,
    enabling interoperability with other AI tool ecosystems.

    Example::

        # Create server
        server = AGKitMCPServer({
            "name": "my-tools",
            "version": "1.0.0",
            "description": "My custom tools"
        })

        # Register tools
        server.register_tool(calculator_tool)
        server.register_tool(search_tool)

        # Run with stdio transport
        await server.run({"type": "stdio"})
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Cloudbase Agent MCP server.

        :param config: Server configuration
        :type config: Dict[str, Any]
        """
        self.config = MCPServerConfig(**config)
        self._tools: Dict[str, BaseTool] = {}
        self._tool_registrations: Dict[str, MCPToolRegistration] = {}
        self._event_listeners: List[MCPEventListener] = []
        self._server: Optional[Server] = None
        self._is_running: bool = False
        self._transport_type: Optional[str] = None
        self._memory_id: Optional[str] = None
        self._current_transport: Optional[Any] = None

    def register_tool(
        self,
        tool: BaseTool,
        registration: Optional[MCPToolRegistration] = None,
    ) -> "AGKitMCPServer":
        """Register an Cloudbase Agent tool to be exposed via MCP.

        :param tool: Cloudbase Agent tool instance
        :type tool: BaseTool
        :param registration: Optional registration configuration
        :type registration: Optional[MCPToolRegistration]
        :return: Self for method chaining
        :rtype: AGKitMCPServer
        """
        registration = registration or MCPToolRegistration()

        # Use custom tool name if provided
        tool_name = registration.tool_name or tool.name

        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' is already registered")

        self._tools[tool_name] = tool
        self._tool_registrations[tool_name] = registration

        self._emit_event(
            MCPEvent(
                type=MCPEventType.TOOL_DISCOVERED,
                tool_name=tool_name,
                timestamp=time.time(),
            )
        )

        return self

    def register_tools(
        self,
        tools: List[BaseTool],
        registrations: Optional[Dict[str, MCPToolRegistration]] = None,
    ) -> "AGKitMCPServer":
        """Register multiple Cloudbase Agent tools.

        :param tools: List of Cloudbase Agent tool instances
        :type tools: List[BaseTool]
        :param registrations: Optional dict of tool_name to registration config
        :type registrations: Optional[Dict[str, MCPToolRegistration]]
        :return: Self for method chaining
        :rtype: AGKitMCPServer
        """
        registrations = registrations or {}

        for tool in tools:
            registration = registrations.get(tool.name)
            self.register_tool(tool, registration)

        return self

    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool.

        :param tool_name: Tool name
        :type tool_name: str
        :return: True if tool was unregistered
        :rtype: bool
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            del self._tool_registrations[tool_name]
            return True
        return False

    def add_event_listener(self, listener: MCPEventListener) -> "AGKitMCPServer":
        """Add an event listener.

        :param listener: Event listener function
        :type listener: MCPEventListener
        :return: Self for method chaining
        :rtype: AGKitMCPServer
        """
        self._event_listeners.append(listener)
        return self

    def remove_event_listener(self, listener: MCPEventListener) -> bool:
        """Remove an event listener.

        :param listener: Event listener function
        :type listener: MCPEventListener
        :return: True if listener was removed
        :rtype: bool
        """
        try:
            self._event_listeners.remove(listener)
            return True
        except ValueError:
            return False

    def _emit_event(self, event: MCPEvent) -> None:
        """Emit an event to all listeners.

        :param event: Event to emit
        :type event: MCPEvent
        """
        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception as e:
                if self.config.log_level == "debug":
                    print(f"Error in event listener: {e}")

    def _convert_tool_to_mcp(self, tool_name: str) -> Tool:
        """Convert an Cloudbase Agent tool to MCP Tool format.

        :param tool_name: Tool name
        :type tool_name: str
        :return: MCP Tool object
        :rtype: Tool
        """
        tool = self._tools[tool_name]
        registration = self._tool_registrations[tool_name]

        # Get description
        description = registration.description or tool.description or ""

        # Get input schema
        if registration.custom_schema:
            input_schema = registration.custom_schema
        elif tool.schema:
            input_schema = pydantic_to_json_schema(tool.schema)
        else:
            # Default schema
            input_schema = {
                "type": "object",
                "properties": {},
            }

        return Tool(
            name=tool_name,
            description=description,
            inputSchema=input_schema,
        )

    async def _handle_list_tools(self) -> List[Tool]:
        """Handle list_tools request.

        :return: List of MCP Tool objects
        :rtype: List[Tool]
        """
        return [self._convert_tool_to_mcp(tool_name) for tool_name in self._tools.keys()]

    async def _handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Handle call_tool request.

        :param name: Tool name
        :type name: str
        :param arguments: Tool arguments
        :type arguments: Dict[str, Any]
        :return: List of TextContent with results
        :rtype: Sequence[TextContent]
        """
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found")

        tool = self._tools[name]

        try:
            self._emit_event(
                MCPEvent(
                    type=MCPEventType.TOOL_CALLED,
                    tool_name=name,
                    data=arguments,
                    timestamp=time.time(),
                )
            )

            # Invoke the tool
            result = await tool.invoke(arguments)

            self._emit_event(
                MCPEvent(
                    type=MCPEventType.TOOL_RESULT,
                    tool_name=name,
                    data=result,
                    timestamp=time.time(),
                )
            )

            # Convert result to TextContent
            import json

            result_text = json.dumps(result, default=str, ensure_ascii=False)

            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            self._emit_event(
                MCPEvent(
                    type=MCPEventType.ERROR,
                    tool_name=name,
                    error=str(e),
                    timestamp=time.time(),
                )
            )

            # Return error as TextContent
            import json

            error_result = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }
            error_text = json.dumps(error_result, ensure_ascii=False)

            return [TextContent(type="text", text=error_text)]

    async def run(self, transport_config: Dict[str, Any]) -> None:
        """Run the MCP server.

        :param transport_config: Transport configuration
        :type transport_config: Dict[str, Any]
        """
        if self._is_running:
            raise RuntimeError("Server is already running")

        transport_type = transport_config.get("type", "stdio")
        self._transport_type = transport_type

        try:
            if self.config.log_level in ["info", "debug"]:
                print(
                    f"[AGKitMCPServer] Starting {self.config.name} v{self.config.version} with {transport_type} transport"
                )
                print(f"[AGKitMCPServer] Registered tools: {', '.join(self.get_registered_tools())}")

            self._is_running = True

            self._emit_event(
                MCPEvent(
                    type=MCPEventType.CONNECTED,
                    data={"transport": transport_type},
                    timestamp=time.time(),
                )
            )

            if transport_type == "stdio":
                await self._run_stdio()
            elif transport_type == "memory":
                await self._run_memory(transport_config)
            elif transport_type == "sse":
                await self._run_sse(transport_config)
            elif transport_type == "streamableHttp":
                await self._run_streamable_http(transport_config)
            else:
                raise ValueError(f"Unsupported transport type: {transport_type}")

        except Exception as e:
            self._is_running = False
            self._current_transport = None
            self._transport_type = None

            self._emit_event(
                MCPEvent(
                    type=MCPEventType.ERROR,
                    error=str(e),
                    data={"context": "server_start"},
                    timestamp=time.time(),
                )
            )

            if self.config.log_level in ["info", "debug"]:
                print(f"[AGKitMCPServer] Failed to start server: {e}")

            raise

    async def _run_stdio(self) -> None:
        """Run server with stdio transport."""
        # Create MCP server
        server = Server(self.config.name)
        self._server = server

        # Register handlers
        @server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return await self._handle_list_tools()

        @server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
            return await self._handle_call_tool(name, arguments)

        # Run with stdio
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    async def _run_memory(self, transport_config: Dict[str, Any]) -> None:
        """Run server with memory transport.

        :param transport_config: Transport configuration
        :type transport_config: Dict[str, Any]
        """
        memory_id = transport_config.get("memory_id", "default")
        self._memory_id = memory_id

        # Get registry
        registry = MemoryTransportRegistry.get_instance()

        # Create transport pair
        transport_pair = registry.create_transport_pair(memory_id)
        server_transport = transport_pair[0]

        # Register server
        registry.register_server(memory_id, self)

        # Store transport
        self._current_transport = server_transport

        # Create MCP server
        server = Server(self.config.name)
        self._server = server

        # Register handlers
        @server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return await self._handle_list_tools()

        @server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
            return await self._handle_call_tool(name, arguments)

        if self.config.log_level in ["info", "debug"]:
            print(f"[AGKitMCPServer] Memory transport ready with ID: {memory_id}")
            print(
                f"[AGKitMCPServer] Use MemoryTransportRegistry.get_instance().get_client_transport('{memory_id}') to get client transport"
            )

        # Run with memory transport
        read_stream, write_stream = server_transport
        await server.run(read_stream, write_stream, server.create_initialization_options())

    async def _run_sse(self, transport_config: Dict[str, Any]) -> None:
        """Run server with SSE transport.

        :param transport_config: Transport configuration
        :type transport_config: Dict[str, Any]
        """
        sse_setup = transport_config.get("sse_setup")

        if not sse_setup:
            raise ValueError("SSE transport requires 'sse_setup' callback")

        # Create MCP server
        server = Server(self.config.name)
        self._server = server

        # Register handlers
        @server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return await self._handle_list_tools()

        @server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
            return await self._handle_call_tool(name, arguments)

        # Create transport factory
        async def create_transport(endpoint: str, response: Any, options: Optional[Dict[str, Any]] = None):
            """Factory function to create SSE transport.

            :param endpoint: SSE endpoint path
            :type endpoint: str
            :param response: HTTP response object
            :type response: Any
            :param options: Optional transport options
            :type options: Optional[Dict[str, Any]]
            :return: SSE transport instance
            :rtype: Any
            """
            try:
                from mcp.server.sse import sse_server
            except ImportError:
                raise ImportError("SSE transport requires 'mcp[sse]' package")

            # Create SSE transport
            async with sse_server(response) as (read_stream, write_stream):
                self._current_transport = (read_stream, write_stream)

                if self.config.log_level in ["info", "debug"]:
                    print(f"[AGKitMCPServer] SSE transport created and connected for endpoint: {endpoint}")

                # Run server
                await server.run(read_stream, write_stream, server.create_initialization_options())

        # Call user setup callback
        await sse_setup(self, create_transport)

        if self.config.log_level in ["info", "debug"]:
            print("[AGKitMCPServer] SSE transport setup completed")

    async def _run_streamable_http(self, transport_config: Dict[str, Any]) -> None:
        """Run server with Streamable HTTP transport.

        :param transport_config: Transport configuration
        :type transport_config: Dict[str, Any]
        """
        streamable_http_setup = transport_config.get("streamable_http_setup")

        if not streamable_http_setup:
            raise ValueError("Streamable HTTP transport requires 'streamable_http_setup' callback")

        # Create MCP server
        server = Server(self.config.name)
        self._server = server

        # Register handlers
        @server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return await self._handle_list_tools()

        @server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
            return await self._handle_call_tool(name, arguments)

        # Create transport factory
        async def create_transport(options: Optional[Dict[str, Any]] = None):
            """Factory function to create Streamable HTTP transport.

            :param options: Optional transport options
            :type options: Optional[Dict[str, Any]]
            :return: Streamable HTTP transport instance
            :rtype: Any
            """
            try:
                # Note: Python MCP SDK may use different import path
                # This is a placeholder - adjust based on actual SDK
                from mcp.server.streamable_http import streamable_http_server
            except ImportError:
                raise ImportError("Streamable HTTP transport requires 'mcp[http]' package")

            # Create Streamable HTTP transport
            options = options or {}
            async with streamable_http_server(**options) as (read_stream, write_stream):
                self._current_transport = (read_stream, write_stream)

                if self.config.log_level in ["info", "debug"]:
                    print("[AGKitMCPServer] Streamable HTTP transport created and connected")

                # Run server
                await server.run(read_stream, write_stream, server.create_initialization_options())

        # Call user setup callback
        await streamable_http_setup(self, create_transport)

        if self.config.log_level in ["info", "debug"]:
            print("[AGKitMCPServer] Streamable HTTP transport setup completed")

    def get_registered_tools(self) -> List[str]:
        """Get list of registered tool names.

        :return: List of tool names
        :rtype: List[str]
        """
        return list(self._tools.keys())

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information.

        :return: Server info dictionary
        :rtype: Dict[str, Any]
        """
        return {
            "name": self.config.name,
            "version": self.config.version,
            "description": self.config.description,
            "tool_count": len(self._tools),
            "tools": self.get_registered_tools(),
        }

    # Convenience methods for different transports

    async def run_stdio(self) -> None:
        """Run server with stdio transport (convenience method).

        :return: None
        :rtype: None
        """
        await self.run({"type": "stdio"})

    async def run_memory(self, memory_id: str = "default") -> None:
        """Run server with memory transport (convenience method).

        :param memory_id: Memory transport identifier
        :type memory_id: str
        :return: None
        :rtype: None
        """
        await self.run({"type": "memory", "memory_id": memory_id})

    async def run_sse(
        self,
        setup: SSETransportSetup,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Run server with SSE transport (convenience method).

        :param setup: SSE setup callback
        :type setup: SSETransportSetup
        :param options: Optional transport options
        :type options: Optional[Dict[str, Any]]
        :return: None
        :rtype: None
        """
        await self.run({"type": "sse", "sse_setup": setup, **(options or {})})

    async def run_streamable_http(
        self,
        setup: StreamableHTTPTransportSetup,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Run server with Streamable HTTP transport (convenience method).

        :param setup: Streamable HTTP setup callback
        :type setup: StreamableHTTPTransportSetup
        :param options: Optional transport options
        :type options: Optional[Dict[str, Any]]
        :return: None
        :rtype: None
        """
        await self.run({"type": "streamableHttp", "streamable_http_setup": setup, **(options or {})})

    async def stop(self) -> None:
        """Stop the server.

        :return: None
        :rtype: None
        """
        if not self._is_running:
            return

        try:
            # Clean up based on transport type
            if self._transport_type == "memory" and self._memory_id:
                MemoryTransportRegistry.get_instance().unregister_server(self._memory_id)

            # Close transport if needed
            if self._current_transport:
                # Close anyio streams to make server.run() exit
                try:
                    read_stream, write_stream = self._current_transport
                    await read_stream.aclose()
                    await write_stream.aclose()
                except Exception as e:
                    if self.config.log_level in ["debug"]:
                        print(f"[AGKitMCPServer] Error closing streams: {e}")
                self._current_transport = None

            self._is_running = False

            self._emit_event(
                MCPEvent(
                    type=MCPEventType.DISCONNECTED,
                    data={"transport": self._transport_type},
                    timestamp=time.time(),
                )
            )

            if self.config.log_level in ["info", "debug"]:
                print(f"[AGKitMCPServer] Server stopped ({self._transport_type} transport)")

            self._transport_type = None
            self._memory_id = None

        except Exception as e:
            self._emit_event(
                MCPEvent(
                    type=MCPEventType.ERROR,
                    error=str(e),
                    data={"context": "server_stop"},
                    timestamp=time.time(),
                )
            )

            if self.config.log_level in ["info", "debug"]:
                print(f"[AGKitMCPServer] Error stopping server: {e}")

            raise

    def is_server_running(self) -> bool:
        """Check if server is running.

        :return: True if server is running
        :rtype: bool
        """
        return self._is_running

    def get_transport_type(self) -> Optional[str]:
        """Get current transport type.

        :return: Transport type or None
        :rtype: Optional[str]
        """
        return self._transport_type

    def get_memory_id(self) -> Optional[str]:
        """Get memory ID (for memory transport).

        :return: Memory ID or None
        :rtype: Optional[str]
        """
        return self._memory_id

    def get_connection_info(self) -> Dict[str, Any]:
        """Get server connection information.

        :return: Connection info dictionary
        :rtype: Dict[str, Any]
        """
        return {
            "is_running": self._is_running,
            "transport_type": self._transport_type,
            "memory_id": self._memory_id,
        }

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update server configuration.

        :param new_config: New configuration values
        :type new_config: Dict[str, Any]
        :return: None
        :rtype: None
        """
        # Update config fields
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration.

        :return: Configuration dictionary
        :rtype: Dict[str, Any]
        """
        return self.config.model_dump()

    def clear_tools(self) -> None:
        """Clear all registered tools.

        :return: None
        :rtype: None
        """
        self._tools.clear()
        self._tool_registrations.clear()

        if self.config.log_level in ["info", "debug"]:
            print("[AGKitMCPServer] Cleared all tools")

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics.

        :return: Statistics dictionary
        :rtype: Dict[str, Any]
        """
        tool_names = list(self._tools.keys())
        tool_types: Dict[str, int] = {}

        for tool in self._tools.values():
            tool_type = getattr(tool, "type", tool.name)
            tool_types[tool_type] = tool_types.get(tool_type, 0) + 1

        return {
            "total_tools": len(self._tools),
            "tool_names": tool_names,
            "tool_types": tool_types,
            "is_running": self._is_running,
            "server_info": {
                "name": self.config.name,
                "version": self.config.version,
                "description": self.config.description,
            },
        }


# Global memory transport registry instance
memory_transport_registry = MemoryTransportRegistry.get_instance()


def convert_agkit_tool_to_mcp_metadata(
    tool: BaseTool,
    config: Optional[Dict[str, Any]] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convert an Cloudbase Agent tool to MCP metadata format.

    :param tool: Cloudbase Agent tool instance
    :type tool: BaseTool
    :param config: Optional server configuration (not used, for API compatibility)
    :type config: Optional[Dict[str, Any]]
    :param tool_config: Optional tool configuration for name/description overrides
    :type tool_config: Optional[Dict[str, Any]]
    :return: MCP tool metadata dictionary
    :rtype: Dict[str, Any]
    """
    tool_config = tool_config or {}

    # Get tool metadata
    tool_metadata = tool.get_metadata()

    # Convert schema to JSON schema
    input_schema = {}
    if hasattr(tool, "schema") and tool.schema:
        input_schema = pydantic_to_json_schema(tool.schema)
    elif hasattr(tool, "input_schema") and tool.input_schema:
        # Handle case where input_schema is already a dict
        if isinstance(tool.input_schema, dict):
            input_schema = tool.input_schema
        else:
            input_schema = pydantic_to_json_schema(tool.input_schema)

    # Determine final name - tool_config.name takes precedence
    final_name = tool_metadata.get("name", tool.name)
    if "name" in tool_config:
        final_name = tool_config["name"]
    elif "namePrefix" in tool_config:
        final_name = f"{tool_config['namePrefix']}{final_name}"

    # Determine final description
    final_description = tool_metadata.get("description", tool.description or f"Cloudbase Agent tool: {tool.name}")
    if "description" in tool_config:
        final_description = tool_config["description"]

    return {
        "name": final_name,
        "description": final_description,
        "inputSchema": input_schema,
    }


async def create_agkit_mcp_server(
    config: Dict[str, Any],
    tools: Optional[List[BaseTool]] = None,
) -> AGKitMCPServer:
    """Create and configure an Cloudbase Agent MCP server.

    :param config: Server configuration
    :type config: Dict[str, Any]
    :param tools: Optional list of tools to register
    :type tools: Optional[List[BaseTool]]
    :return: Configured server instance
    :rtype: AGKitMCPServer
    """
    server = AGKitMCPServer(config)

    if tools:
        server.register_tools(tools)

    return server


__all__ = [
    "AGKitMCPServer",
    "MemoryTransportRegistry",
    "memory_transport_registry",
    "create_agkit_mcp_server",
    "convert_agkit_tool_to_mcp_metadata",
    "SSETransportSetup",
    "StreamableHTTPTransportSetup",
]
