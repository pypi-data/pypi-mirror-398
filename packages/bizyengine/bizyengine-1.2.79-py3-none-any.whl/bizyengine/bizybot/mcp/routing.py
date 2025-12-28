"""
MCP tool routing and format conversion utilities
"""

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from bizyengine.bizybot.mcp.models import Tool

if TYPE_CHECKING:
    # 仅用于类型检查，避免运行时循环依赖
    from bizyengine.bizybot.mcp.manager import MCPClientManager


class ToolFormatConverter:
    """Converts between MCP and OpenAI tool formats"""

    @staticmethod
    def mcp_to_openai(tool: Tool) -> Dict[str, Any]:
        """Convert MCP tool to OpenAI function calling format"""
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
            },
        }

        # Add title as description suffix if available and different from description
        if tool.title and tool.title != tool.description:
            openai_tool["function"]["description"] = f"{tool.title}: {tool.description}"

        return openai_tool

    @staticmethod
    def mcp_tools_to_openai(tools: List[Tool]) -> List[Dict[str, Any]]:
        """Convert list of MCP tools to OpenAI format"""
        return [ToolFormatConverter.mcp_to_openai(tool) for tool in tools]

    @staticmethod
    def validate_openai_tool_call(tool_call: Dict[str, Any]) -> bool:
        """Validate OpenAI tool call format"""
        try:
            required_fields = ["id", "type", "function"]
            if not all(field in tool_call for field in required_fields):
                return False

            if tool_call["type"] != "function":
                return False

            function = tool_call["function"]
            if not isinstance(function, dict):
                return False

            if "name" not in function or "arguments" not in function:
                return False

            return True

        except Exception:
            return False

    @staticmethod
    def extract_tool_call_info(
        tool_call: Dict[str, Any],
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Extract tool call information from OpenAI format"""
        if not ToolFormatConverter.validate_openai_tool_call(tool_call):
            raise ValueError("Invalid OpenAI tool call format")

        call_id = tool_call["id"]
        function = tool_call["function"]
        tool_name = function["name"]

        # Parse arguments (they come as JSON string)
        import json

        try:
            arguments = json.loads(function["arguments"])
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in tool arguments: {e}")

        return call_id, tool_name, arguments


class MCPToolRouter:
    """Routes tool calls to appropriate MCP servers"""

    def __init__(self, manager: "MCPClientManager"):
        self.manager = manager

    async def route_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Route a tool call to the appropriate MCP server"""
        try:
            # Extract tool call information
            call_id, tool_name, arguments = ToolFormatConverter.extract_tool_call_info(
                tool_call
            )

            # Find the server that provides this tool
            server_name, tool = self.manager.find_tool_server(tool_name)

            # Call the tool on the appropriate server
            result = await self.manager.call_tool_on_server(
                server_name, tool_name, arguments
            )

            # Format the result for OpenAI
            return self._format_tool_result(call_id, tool_name, server_name, result)

        except Exception as e:
            return self._format_tool_error(tool_call.get("id", "unknown"), str(e))

    async def route_multiple_tool_calls(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Route multiple tool calls concurrently"""
        import asyncio

        # Execute all tool calls concurrently
        tasks = [self.route_tool_call(tool_call) for tool_call in tool_calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        formatted_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                call_id = tool_calls[i].get("id", f"unknown_{i}")
                formatted_results.append(self._format_tool_error(call_id, str(result)))
            else:
                formatted_results.append(result)

        return formatted_results

    def _format_tool_result(
        self, call_id: str, tool_name: str, server_name: str, result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format MCP tool result for OpenAI"""
        if result.get("isError", False):
            return self._format_tool_error(
                call_id,
                f"Tool execution error: {result.get('content', 'Unknown error')}",
            )

        # Handle different result formats
        formatted_content = ""

        # Check if this is a standard MCP result with content array
        if "content" in result and isinstance(result["content"], (list, str)):
            # Standard MCP format
            formatted_content = self._format_mcp_content(result["content"])
        else:
            # Direct result format (like from Exa API)
            # Convert the entire result to a formatted string
            formatted_content = self._format_direct_result(result)

        formatted_result = {
            "tool_call_id": call_id,
            "role": "tool",
            "content": formatted_content,
            "name": tool_name,
            # Additional metadata (not part of OpenAI spec but useful for debugging)
            "_mcp_server": server_name,
            "_mcp_raw_result": result,
            "success": True,
        }

        return formatted_result

    def _format_tool_error(self, call_id: str, error_message: str) -> Dict[str, Any]:
        """Format tool error for OpenAI"""
        return {
            "tool_call_id": call_id,
            "role": "tool",
            "content": f"Error: {error_message}",
            "_error": True,
        }

    def _format_mcp_content(self, content) -> str:
        """Convert MCP content to string format"""
        if not content:
            return ""

        # Handle different content formats
        if isinstance(content, str):
            return content

        # Handle single content object (not in a list)
        if hasattr(content, "text"):
            # TextContent object
            return content.text
        elif hasattr(content, "type"):
            # Single content dict
            return self._format_single_content_item(content)

        # Handle list of content items
        if isinstance(content, list):
            formatted_parts = []
            for item in content:
                if hasattr(item, "text"):
                    # TextContent object
                    formatted_parts.append(item.text)
                elif isinstance(item, dict):
                    # Content dict
                    formatted_parts.append(self._format_single_content_item(item))
                else:
                    # Unknown format, convert to string
                    formatted_parts.append(str(item))
            return "\n".join(formatted_parts)

        # Fallback: convert to string
        return str(content)

    def _format_single_content_item(self, item) -> str:
        """Format a single content item (dict or object)"""
        # Handle dict format
        if isinstance(item, dict):
            content_type = item.get("type", "unknown")

            if content_type == "text":
                text_content = item.get("text", "")
                # Check if the text content is JSON that we should format nicely
                return self._format_text_content(text_content)
            elif content_type == "image":
                # For images, include metadata but not the actual data
                mime_type = item.get("mimeType", "unknown")
                return f"[Image: {mime_type}]"
            elif content_type == "resource":
                # For resources, include the URI and title
                resource = item.get("resource", {})
                uri = resource.get("uri", "unknown")
                title = resource.get("title", "")
                return f"[Resource: {title or uri}]"
            else:
                # For unknown types, convert to string
                return str(item)

        # Handle object format (like TextContent)
        if hasattr(item, "text"):
            return self._format_text_content(item.text)
        elif hasattr(item, "type"):
            if item.type == "text" and hasattr(item, "text"):
                return self._format_text_content(item.text)
            else:
                return f"[{item.type}]"

        # Fallback
        return str(item)

    def _format_text_content(self, text_content: str) -> str:
        """Format text content, handling JSON strings specially"""
        try:
            # Try to parse as JSON
            import json

            parsed_json = json.loads(text_content)

            # If it's a JSON object, format it nicely
            if isinstance(parsed_json, dict):
                # Check if it looks like Exa search results
                if "results" in parsed_json and isinstance(
                    parsed_json["results"], list
                ):
                    return self._format_exa_search_results(parsed_json)
                else:
                    # Format other JSON objects nicely
                    return json.dumps(parsed_json, indent=2, ensure_ascii=False)
            else:
                # If it's not a dict, just return the original text
                return text_content

        except (json.JSONDecodeError, TypeError):
            # If it's not valid JSON, return as-is
            return text_content

    def _format_direct_result(self, result: Dict[str, Any]) -> str:
        """Format direct JSON result (like from Exa API) into readable text"""
        try:
            # Handle Exa search results format
            if "results" in result and isinstance(result["results"], list):
                return self._format_exa_search_results(result)

            # Handle other direct JSON formats
            import json

            return json.dumps(result, indent=2, ensure_ascii=False)

        except Exception:
            return str(result)

    def _format_exa_search_results(self, result: Dict[str, Any]) -> str:
        """Format Exa search results into readable text"""
        try:
            results = result.get("results", [])
            search_info = []

            # Add search metadata
            if "autopromptString" in result:
                search_info.append(f"Search Query: {result['autopromptString']}")

            if "searchTime" in result:
                search_info.append(f"Search Time: {result['searchTime']}ms")

            if len(results) > 0:
                search_info.append(f"Found {len(results)} results:")

            # Format each result
            formatted_results = []
            for i, item in enumerate(results[:5], 1):  # Limit to first 5 results
                result_text = f"\n{i}. **{item.get('title', 'No title')}**"

                if item.get("url"):
                    result_text += f"\n   URL: {item['url']}"

                if item.get("publishedDate"):
                    result_text += f"\n   Published: {item['publishedDate']}"

                if item.get("author"):
                    result_text += f"\n   Author: {item['author']}"

                # Add a snippet of the text content
                if item.get("text"):
                    text_snippet = (
                        item["text"][:300] + "..."
                        if len(item["text"]) > 300
                        else item["text"]
                    )
                    result_text += f"\n   Content: {text_snippet}"

                formatted_results.append(result_text)

            # Combine all parts
            full_response = "\n".join(search_info)
            if formatted_results:
                full_response += "\n" + "\n".join(formatted_results)

            # Add cost information if available
            if "costDollars" in result:
                cost = result["costDollars"].get("total", 0)
                full_response += f"\n\nSearch cost: ${cost:.4f}"

            return full_response

        except Exception:
            import json

            return json.dumps(result, indent=2, ensure_ascii=False)


class ToolCallBatch:
    """Manages a batch of tool calls for efficient processing"""

    def __init__(self, tool_calls: List[Dict[str, Any]]):
        self.tool_calls = tool_calls
        self.results: List[Dict[str, Any]] = []
        self.completed = False

    async def execute(self, router: MCPToolRouter) -> List[Dict[str, Any]]:
        """Execute all tool calls in the batch"""
        if self.completed:
            return self.results

        self.results = await router.route_multiple_tool_calls(self.tool_calls)
        self.completed = True

        return self.results

    def get_results_by_call_id(self) -> Dict[str, Dict[str, Any]]:
        """Get results indexed by tool call ID"""
        return {result["tool_call_id"]: result for result in self.results}

    def get_successful_results(self) -> List[Dict[str, Any]]:
        """Get only successful results"""
        return [result for result in self.results if not result.get("_error", False)]

    def get_error_results(self) -> List[Dict[str, Any]]:
        """Get only error results"""
        return [result for result in self.results if result.get("_error", False)]
