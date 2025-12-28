"""
Data models for MCP client functionality
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Tool:
    """Represents an MCP tool"""

    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str
    title: Optional[str] = None

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format"""
        from bizyengine.bizybot.mcp.routing import ToolFormatConverter

        return ToolFormatConverter.mcp_to_openai(self)


@dataclass
class ServerStatus:
    """Status information for an MCP server"""

    name: str
    connected: bool
    session_id: Optional[str]
    last_error: Optional[str]
    capabilities: Dict[str, Any]
    tools_count: int


@dataclass
class MCPSession:
    """MCP session information"""

    session_id: Optional[str]
    protocol_version: str
    server_capabilities: Dict[str, Any]
    client_capabilities: Dict[str, Any]
    initialized: bool = False
