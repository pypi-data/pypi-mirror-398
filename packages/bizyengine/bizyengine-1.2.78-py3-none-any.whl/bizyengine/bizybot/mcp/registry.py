"""
MCP tool registry for managing tools across multiple servers
"""

from typing import Any, Dict, List, Tuple

from bizyengine.bizybot.mcp.models import Tool


class MCPToolRegistry:
    """Registry for managing MCP tools across multiple servers"""

    def __init__(self):
        self.tools_by_name: Dict[str, Tuple[str, Tool]] = (
            {}
        )  # tool_name -> (server_name, tool)
        self.tools_by_server: Dict[str, List[Tool]] = {}  # server_name -> [tools]
        self.tool_conflicts: Dict[str, List[str]] = (
            {}
        )  # tool_name -> [server_names] for conflicts

    def register_server_tools(self, server_name: str, tools: List[Tool]) -> None:
        """Register all tools from a specific server"""
        # Clear existing tools for this server
        self.unregister_server_tools(server_name)

        # Register new tools
        self.tools_by_server[server_name] = tools

        for tool in tools:
            if tool.name in self.tools_by_name:
                # Handle tool name conflicts
                existing_server = self.tools_by_name[tool.name][0]
                if tool.name not in self.tool_conflicts:
                    self.tool_conflicts[tool.name] = [existing_server]
                self.tool_conflicts[tool.name].append(server_name)

                # For now, keep the first registered tool (could implement priority system)
                continue

            self.tools_by_name[tool.name] = (server_name, tool)

    def unregister_server_tools(self, server_name: str) -> None:
        """Unregister all tools from a specific server"""
        if server_name not in self.tools_by_server:
            return

        # Remove tools from main registry
        tools_to_remove = []
        for tool_name, (srv_name, _) in self.tools_by_name.items():
            if srv_name == server_name:
                tools_to_remove.append(tool_name)

        for tool_name in tools_to_remove:
            del self.tools_by_name[tool_name]

            # Clean up conflicts
            if tool_name in self.tool_conflicts:
                if server_name in self.tool_conflicts[tool_name]:
                    self.tool_conflicts[tool_name].remove(server_name)
                if len(self.tool_conflicts[tool_name]) <= 1:
                    del self.tool_conflicts[tool_name]

        # Remove server from tools_by_server
        del self.tools_by_server[server_name]

    def find_tool_server(self, tool_name: str) -> Tuple[str, Tool]:
        """Find which server provides a specific tool"""
        if tool_name not in self.tools_by_name:
            available_tools = list(self.tools_by_name.keys())
            raise ValueError(
                f"Tool '{tool_name}' not found. Available tools: {available_tools}"
            )

        return self.tools_by_name[tool_name]

    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools"""
        return [tool for _, tool in self.tools_by_name.values()]

    def get_server_tools(self, server_name: str) -> List[Tool]:
        """Get all tools from a specific server"""
        return self.tools_by_server.get(server_name, [])

    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI function calling format"""
        tools = []
        for tool in self.get_all_tools():
            tools.append(tool.to_openai_schema())
        return tools

    def get_tool_conflicts(self) -> Dict[str, List[str]]:
        """Get information about tool name conflicts"""
        return self.tool_conflicts.copy()

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the tool registry"""
        return {
            "total_tools": len(self.tools_by_name),
            "total_servers": len(self.tools_by_server),
            "conflicts": len(self.tool_conflicts),
            "tools_by_server": {
                server: len(tools) for server, tools in self.tools_by_server.items()
            },
        }

    def search_tools(self, query: str) -> List[Tuple[str, Tool]]:
        """Search for tools by name or description"""
        query_lower = query.lower()
        results = []

        for server_name, tool in self.tools_by_name.values():
            if (
                query_lower in tool.name.lower()
                or query_lower in tool.description.lower()
            ):
                results.append((server_name, tool))

        return results

    def validate_tool_availability(self, tool_names: List[str]) -> Dict[str, bool]:
        """Check if a list of tools are available"""
        return {tool_name: tool_name in self.tools_by_name for tool_name in tool_names}

    def clear(self) -> None:
        """Clear all registered tools"""
        self.tools_by_name.clear()
        self.tools_by_server.clear()
        self.tool_conflicts.clear()
