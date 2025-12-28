"""
MCP client manager for handling multiple MCP server connections using MCP Python SDK
"""

import asyncio
import os
from contextlib import AsyncExitStack
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from bizyengine.bizybot.config import MCPServerConfig
from bizyengine.bizybot.exceptions import (
    MCPConnectionError,
    MCPError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolValidationError,
)
from bizyengine.bizybot.mcp.models import ServerStatus, Tool
from bizyengine.bizybot.mcp.registry import MCPToolRegistry
from bizyengine.bizybot.mcp.routing import MCPToolRouter, ToolCallBatch


class MCPServerConnection:
    """
    Individual MCP server connection using MCP Python SDK
    """

    def __init__(self, server_name: str, config: MCPServerConfig):
        self.server_name = server_name
        self.config = config
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.tools: List[Tool] = []
        self._connected = False
        self._cleanup_lock = asyncio.Lock()
        # Owner-task based lifecycle management for HTTP transport
        self._owner_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._ready_event = asyncio.Event()

    async def initialize(self) -> None:
        """Initialize MCP connection using appropriate transport"""
        try:
            transport_type = self.config.transport or "stdio"

            if transport_type == "stdio":
                await self._initialize_stdio()
            elif transport_type == "streamable_http":
                await self._initialize_http()
            else:
                raise MCPConnectionError(
                    f"Unsupported transport type: {transport_type}",
                    server_name=self.server_name,
                )

        except MCPConnectionError:
            raise
        except Exception as e:
            await self.cleanup()
            raise MCPConnectionError(
                f"Initialization failed: {e}", server_name=self.server_name
            ) from e

    async def _initialize_stdio(self) -> None:
        """Initialize stdio transport for local MCP servers"""
        command = self.config.command
        if not command:
            raise MCPConnectionError(
                "No command specified for stdio transport", server_name=self.server_name
            )

        # Handle command resolution (e.g., uvx, npx)
        if command in ["uvx", "npx"]:
            import shutil

            resolved_command = shutil.which(command)
            if not resolved_command:
                raise MCPConnectionError(
                    f"Command '{command}' not found in PATH",
                    server_name=self.server_name,
                )
            command = resolved_command

        server_params = StdioServerParameters(
            command=command,
            args=self.config.args or [],
            env={**os.environ, **(self.config.env or {})},
        )

        try:
            # Use MCP SDK's stdio client
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport

            # Create client session
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )

            # Initialize MCP protocol
            await session.initialize()
            self.session = session
            self._connected = True

            # Discover tools
            await self._discover_tools()

        except Exception:
            raise

    async def _http_owner(self) -> None:
        """Owner task that manages HTTP transport lifecycle in a single task.
        Ensures enter/exit of streamablehttp_client and ClientSession happen in the same task
        to satisfy AnyIO cancel scope requirements.
        """
        url = self.config.url
        timeout_seconds = (
            int(self.config.timeout) if self.config.timeout is not None else 30
        )
        timeout = timedelta(seconds=timeout_seconds)
        headers = self.config.headers
        try:
            async with streamablehttp_client(
                url=url, timeout=timeout, headers=headers
            ) as transport:
                read, write, get_session_id = transport
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.session = session
                    self._connected = True
                    if get_session_id:
                        try:
                            # Session id is optional; just trigger retrieval if available
                            get_session_id()
                        except Exception:
                            # Session id is optional; ignore retrieval errors
                            pass
                    # Discover tools
                    try:
                        await self._discover_tools()
                    finally:
                        # Signal ready regardless of discover success to unblock initializer
                        if not self._ready_event.is_set():
                            self._ready_event.set()
                    # Wait for stop signal
                    await self._stop_event.wait()
        except Exception:
            # Ensure initializer doesn't hang if failure happens before ready
            if not self._ready_event.is_set():
                self._ready_event.set()
        finally:
            # Reset connection state on exit
            self.session = None
            self._connected = False

    async def _initialize_http(self) -> None:
        """Initialize HTTP transport for remote MCP servers"""
        url = self.config.url
        if not url:
            raise MCPConnectionError(
                "No URL specified for HTTP transport", server_name=self.server_name
            )

        try:
            # Start owner task managing HTTP transport
            # Reset control events
            self._stop_event.clear()
            self._ready_event.clear()
            # Launch owner task
            self._owner_task = asyncio.create_task(self._http_owner())
            # Wait until the owner has initialized or errored
            await self._ready_event.wait()
            if not self._connected or not self.session:
                raise MCPConnectionError(
                    f"HTTP initialization failed for {self.server_name}",
                    server_name=self.server_name,
                )
        except Exception:
            # Ensure owner task is stopped if started
            if self._owner_task and not self._owner_task.done():
                self._stop_event.set()
                try:
                    await self._owner_task
                except Exception:
                    pass
                finally:
                    self._owner_task = None
            raise

    async def _discover_tools(self) -> None:
        """Discover available tools from the MCP server"""
        if not self.session:
            return

        try:
            # Use SDK's list_tools method
            tools_response = await self.session.list_tools()

            self.tools = []
            for tool_data in tools_response.tools:
                tool = Tool(
                    name=tool_data.name,
                    description=tool_data.description,
                    input_schema=tool_data.inputSchema,
                    server_name=self.server_name,
                    title=getattr(tool_data, "title", None),
                )
                self.tools.append(tool)

        except Exception:
            self.tools = []

    def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        if not self._connected:
            raise MCPConnectionError(f"Server {self.server_name} not connected")

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
                "title": tool.title,
            }
            for tool in self.tools
        ]

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a specific tool using MCP SDK with retry mechanism"""
        if not self.session or not self._connected:
            raise MCPConnectionError(
                f"Server {self.server_name} not connected", server_name=self.server_name
            )

        # Verify tool exists
        tool = next((t for t in self.tools if t.name == tool_name), None)
        if not tool:
            raise ToolNotFoundError(
                f"Tool '{tool_name}' not found on server {self.server_name}",
                tool_name=tool_name,
                server_name=self.server_name,
            )

        # Validate arguments against tool schema (basic validation)
        try:
            self._validate_tool_arguments(arguments, tool.input_schema)
        except Exception as e:
            raise ToolValidationError(
                f"Invalid arguments for tool '{tool_name}': {e}",
                tool_name=tool_name,
                server_name=self.server_name,
            ) from e

        try:
            # Use SDK's call_tool method
            result = await self.session.call_tool(tool_name, arguments)

            # Process result
            tool_result = {
                "content": result.content,
                "isError": getattr(result, "isError", False),
                "server_name": self.server_name,
                "tool_name": tool_name,
            }

            if tool_result["isError"]:
                raise ToolExecutionError(
                    f"Tool returned error: {result.content}",
                    tool_name=tool_name,
                    server_name=self.server_name,
                )

            return tool_result

        except ToolExecutionError:
            raise
        except Exception as e:
            raise ToolExecutionError(
                f"Tool execution failed: {e}",
                tool_name=tool_name,
                server_name=self.server_name,
            ) from e

    def _validate_tool_arguments(
        self, arguments: Dict[str, Any], schema: Dict[str, Any]
    ) -> None:
        """Basic validation of tool arguments against schema"""
        if not isinstance(arguments, dict):
            raise ToolValidationError("Arguments must be a dictionary")

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in arguments:
                raise ToolValidationError(
                    f"Required field '{field}' missing from arguments"
                )

        # Basic type checking for properties
        properties = schema.get("properties", {})
        for field_name, field_value in arguments.items():
            if field_name in properties:
                expected_type = properties[field_name].get("type")
                if expected_type and not self._check_json_type(
                    field_value, expected_type
                ):
                    raise ToolValidationError(
                        f"Field '{field_name}' has incorrect type. Expected {expected_type}"
                    )

    def _check_json_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches JSON schema type"""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }

        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type is None:
            return True  # Unknown type, skip validation

        return isinstance(value, expected_python_type)

    async def cleanup(self) -> None:
        """Clean up server connection resources"""
        async with self._cleanup_lock:
            try:
                # Stop owner task (HTTP transport) if running
                if self._owner_task and not self._owner_task.done():
                    self._stop_event.set()
                    try:
                        await self._owner_task
                    finally:
                        self._owner_task = None
                # Close any stdio resources managed by exit stack
                await self.exit_stack.aclose()
                self.session = None
                self._connected = False
            except Exception:
                pass

    def is_connected(self) -> bool:
        """Check if server connection is active"""
        return self._connected and self.session is not None


class MCPClientManager:
    """
    Manager for multiple MCP server connections using MCP Python SDK
    """

    def __init__(self):
        self.connections: Dict[str, MCPServerConnection] = {}
        self.tool_registry = MCPToolRegistry()
        self.server_status: Dict[str, ServerStatus] = {}

        # Tool routing
        self.router = MCPToolRouter(self)

    async def initialize_servers(self, config: Dict[str, MCPServerConfig]) -> None:
        """Initialize connections to all configured MCP servers

        Args:
            config: Mapping of server name to global MCPServerConfig dataclass
        """

        for server_name, server_cfg in config.items():
            # Re-validate using dataclass validation method if available
            if hasattr(server_cfg, "_validate"):
                server_cfg._validate()

            # Validate transport
            if server_cfg.transport not in ("stdio", "streamable_http"):
                raise MCPConnectionError(
                    f"Unsupported transport type: {server_cfg.transport}",
                    server_name=server_name,
                )
            try:
                # Create and initialize server connection with dataclass directly
                connection = MCPServerConnection(server_name, server_cfg)
                await connection.initialize()

                self.connections[server_name] = connection

                # Register tools in the registry
                self.tool_registry.register_server_tools(server_name, connection.tools)

                # Update server status
                self.server_status[server_name] = ServerStatus(
                    name=server_name,
                    connected=True,
                    session_id=None,  # SDK handles session management internally
                    last_error=None,
                    capabilities={},  # Could be populated from session info
                    tools_count=len(connection.tools),
                )

            except Exception as e:
                self.server_status[server_name] = ServerStatus(
                    name=server_name,
                    connected=False,
                    session_id=None,
                    last_error=str(e),
                    capabilities={},
                    tools_count=0,
                )

    def list_all_tools(self) -> List[Tool]:
        """Get all available tools from all connected servers"""
        return self.tool_registry.get_all_tools()

    def find_tool_server(self, tool_name: str) -> Tuple[str, Tool]:
        """Find which server provides a specific tool"""
        try:
            return self.tool_registry.find_tool_server(tool_name)
        except ValueError as e:
            raise MCPError(str(e))

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool by name (automatically finds the correct server)"""
        try:
            server_name, tool = self.find_tool_server(tool_name)
            return await self.call_tool_on_server(server_name, tool_name, arguments)
        except Exception:
            raise

    async def call_tool_on_server(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on a specific MCP server"""
        if server_name not in self.connections:
            raise MCPConnectionError(f"MCP server '{server_name}' not found")

        connection = self.connections[server_name]
        if not connection.is_connected():
            raise MCPConnectionError(f"MCP server '{server_name}' not connected")

        return await connection.call_tool(tool_name, arguments)

    def get_connection(self, server_name: str) -> MCPServerConnection:
        """Get MCP server connection"""
        if server_name not in self.connections:
            raise MCPConnectionError(f"MCP server '{server_name}' not found")

        connection = self.connections[server_name]
        if not connection.is_connected():
            raise MCPConnectionError(f"MCP server '{server_name}' not connected")

        return connection

    def get_server_status(self) -> Dict[str, ServerStatus]:
        """Get status of all MCP servers"""
        # Update connection status
        for server_name, connection in self.connections.items():
            if server_name in self.server_status:
                self.server_status[server_name].connected = connection.is_connected()

        return self.server_status.copy()

    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI function calling format for LLM"""
        return self.tool_registry.get_tools_for_llm()

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the tool registry"""
        return self.tool_registry.get_registry_stats()

    def search_tools(self, query: str) -> List[Tuple[str, Tool]]:
        """Search for tools by name or description"""
        return self.tool_registry.search_tools(query)

    def get_tool_conflicts(self) -> Dict[str, List[str]]:
        """Get information about tool name conflicts"""
        return self.tool_registry.get_tool_conflicts()

    async def execute_tool_calls(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute multiple tool calls using the router"""
        if not tool_calls:
            return []

        batch = ToolCallBatch(tool_calls)
        return await batch.execute(self.router)

    async def execute_single_tool_call(
        self, tool_call: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single tool call using the router"""
        return await self.router.route_tool_call(tool_call)

    async def cleanup(self) -> None:
        """Cleanup all MCP connections"""

        # Cleanup all connections
        for connection in self.connections.values():
            try:
                await connection.cleanup()
            except Exception:
                pass

        self.connections.clear()
        self.tool_registry.clear()
        self.server_status.clear()
