#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP (Model Context Protocol) type definitions.

This module provides type definitions for MCP integration in Cloudbase Agent.
"""

from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class MCPTransportType(str, Enum):
    """MCP transport types."""

    STDIO = "stdio"
    MEMORY = "memory"
    SSE = "sse"
    STREAMABLE_HTTP = "streamableHttp"


class MCPClientStatus(str, Enum):
    """MCP client connection status."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class MCPStdioTransport(BaseModel):
    """Stdio transport configuration."""

    type: Literal["stdio"] = "stdio"
    command: str
    args: List[str] = Field(default_factory=list)
    env: Optional[Dict[str, str]] = None


class MCPMemoryTransport(BaseModel):
    """Memory transport configuration."""

    type: Literal["memory"] = "memory"
    memory_id: str = Field(alias="memoryId")


class MCPSSETransport(BaseModel):
    """SSE transport configuration."""

    type: Literal["sse"] = "sse"
    url: str


class MCPStreamableHttpTransport(BaseModel):
    """Streamable HTTP transport configuration."""

    type: Literal["streamableHttp"] = "streamableHttp"
    url: str


MCPTransport = Union[
    MCPStdioTransport,
    MCPMemoryTransport,
    MCPSSETransport,
    MCPStreamableHttpTransport,
]


class MCPConnectionOptions(BaseModel):
    """MCP connection options."""

    auto_reconnect: bool = Field(default=True, alias="autoReconnect")
    reconnect_delay: int = Field(default=5000, alias="reconnectDelay")  # milliseconds
    max_reconnect_attempts: int = Field(default=3, alias="maxReconnectAttempts")
    heartbeat_interval: int = Field(default=30000, alias="heartbeatInterval")  # milliseconds
    timeout: int = Field(default=30000)  # milliseconds


class MCPClientConfig(BaseModel):
    """MCP client configuration."""

    name: str
    version: str = "1.0.0"
    transport: MCPTransport
    options: MCPConnectionOptions = Field(default_factory=MCPConnectionOptions)


class MCPToolConfig(BaseModel):
    """MCP tool configuration."""

    timeout: int = Field(default=30000)  # milliseconds
    retry_count: int = Field(default=1, alias="retryCount")
    retry_delay: int = Field(default=1000, alias="retryDelay")  # milliseconds
    transform_input: Optional[Callable[[Any], Any]] = Field(default=None, alias="transformInput")
    transform_output: Optional[Callable[[Any], Any]] = Field(default=None, alias="transformOutput")

    class Config:
        arbitrary_types_allowed = True


class MCPAdapterConfig(BaseModel):
    """MCP adapter configuration."""

    name_prefix: Optional[str] = Field(default=None, alias="namePrefix")
    description_prefix: Optional[str] = Field(default=None, alias="descriptionPrefix")
    tool_config: MCPToolConfig = Field(default_factory=MCPToolConfig, alias="toolConfig")


class MCPToolMetadata(BaseModel):
    """MCP tool metadata (from MCP server)."""

    name: str
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = Field(default=None, alias="inputSchema")

    class Config:
        populate_by_name = True  # Allow access by both field name and alias


class MCPToolCallResult(BaseModel):
    """MCP tool call result."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = Field(default=None, alias="executionTime")


class MCPServerInfo(BaseModel):
    """MCP server information."""

    name: str
    version: str
    protocol_version: str = Field(default="1.0.0", alias="protocolVersion")
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class MCPEventType(str, Enum):
    """MCP event types."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    TOOL_DISCOVERED = "tool_discovered"
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class MCPEvent(BaseModel):
    """MCP event."""

    type: MCPEventType
    server_id: Optional[str] = Field(default=None, alias="serverId")
    tool_name: Optional[str] = Field(default=None, alias="toolName")
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: Optional[float] = None

    class Config:
        use_enum_values = True
        populate_by_name = True  # Allow access by both field name and alias


MCPEventListener = Callable[[MCPEvent], None]


class MCPServerConfig(BaseModel):
    """MCP server configuration."""

    name: str
    version: str = "1.0.0"
    description: Optional[str] = None
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    log_level: str = Field(default="info", alias="logLevel")


class MCPToolRegistration(BaseModel):
    """MCP tool registration configuration."""

    tool_name: Optional[str] = Field(default=None, alias="toolName")
    description: Optional[str] = None
    custom_schema: Optional[Dict[str, Any]] = Field(default=None, alias="customSchema")


__all__ = [
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
]
