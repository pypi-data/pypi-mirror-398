#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP (Model Context Protocol) integration for Cloudbase Agent.

This package provides MCP client and server implementations for Cloudbase Agent,
enabling interoperability with other AI tool ecosystems.

Client Usage::

    from cloudbase_agent.tools.mcp import MCPToolkit

    # Create toolkit
    toolkit = MCPToolkit("my-mcp-tools")

    # Add MCP server
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

Server Usage::

    from cloudbase_agent.tools.mcp import AGKitMCPServer

    # Create server
    server = AGKitMCPServer({
        "name": "my-tools",
        "version": "1.0.0"
    })

    # Register tools
    server.register_tool(my_calculator_tool)
    server.register_tool(my_search_tool)

    # Run server
    await server.run({"type": "stdio"})
"""

from .agkit_mcp_server import (
    AGKitMCPServer,
    MemoryTransportRegistry,
    SSETransportSetup,
    StreamableHTTPTransportSetup,
    convert_agkit_tool_to_mcp_metadata,
    create_agkit_mcp_server,
    memory_transport_registry,
)
from .client_tool import MCPClientTool
from .mcp_client_manager import MCPClientManager
from .mcp_toolkit import MCPClientWrapper, MCPToolkit
from .types import (
    MCPAdapterConfig,
    MCPClientConfig,
    MCPClientStatus,
    MCPConnectionOptions,
    MCPEvent,
    MCPEventListener,
    MCPEventType,
    MCPMemoryTransport,
    MCPServerConfig,
    MCPServerInfo,
    MCPSSETransport,
    MCPStdioTransport,
    MCPStreamableHttpTransport,
    MCPToolCallResult,
    MCPToolConfig,
    MCPToolMetadata,
    MCPToolRegistration,
    MCPTransport,
    MCPTransportType,
)
from .utils import (
    create_dynamic_model,
    format_tool_name,
    json_schema_to_pydantic_fields,
    merge_schemas,
    parse_tool_name,
    pydantic_to_json_schema,
    safe_json_dumps,
    safe_json_loads,
)

__all__ = [
    # Types
    "MCPTransportType",
    "MCPClientStatus",
    "MCPStdioTransport",
    "MCPMemoryTransport",
    "MCPSSETransport",
    "MCPStreamableHttpTransport",
    "MCPTransport",
    "MCPConnectionOptions",
    "MCPClientConfig",
    "MCPToolConfig",
    "MCPAdapterConfig",
    "MCPToolMetadata",
    "MCPToolCallResult",
    "MCPServerInfo",
    "MCPEventType",
    "MCPEvent",
    "MCPEventListener",
    "MCPServerConfig",
    "MCPToolRegistration",
    # Utils
    "pydantic_to_json_schema",
    "json_schema_to_pydantic_fields",
    "create_dynamic_model",
    "format_tool_name",
    "parse_tool_name",
    "safe_json_dumps",
    "safe_json_loads",
    "merge_schemas",
    # Client
    "MCPClientTool",
    "MCPClientManager",
    "MCPToolkit",
    "MCPClientWrapper",
    # Server
    "AGKitMCPServer",
    "MemoryTransportRegistry",
    "memory_transport_registry",
    "create_agkit_mcp_server",
    "convert_agkit_tool_to_mcp_metadata",
    "SSETransportSetup",
    "StreamableHTTPTransportSetup",
]
