"""
Main coordinator class that orchestrates LLM and MCP interactions
"""

from typing import Any, AsyncIterator, Dict, List, Optional

from bizyengine.bizybot.client import LLMClient, ToolCall
from bizyengine.bizybot.config import Config
from bizyengine.bizybot.exceptions import (
    CoordinatorError,
    LLMError,
    MCPError,
    ValidationError,
)
from bizyengine.bizybot.mcp.manager import MCPClientManager
from bizyengine.bizybot.models import Conversation


class CoordinatorInitializationError(CoordinatorError):
    """Coordinator initialization error"""

    pass


class CoordinatorProcessingError(CoordinatorError):
    """Coordinator message processing error"""

    pass


class Coordinator:
    """
    Main coordinator that orchestrates interactions between LLM and MCP servers.

    The coordinator is the central component that:
    1. Manages conversation state and context
    2. Coordinates between LLM client and MCP servers
    3. Handles tool discovery and execution
    4. Processes streaming responses and tool calls
    """

    def __init__(self, config: Config):
        """
        Initialize coordinator with configuration

        Args:
            config: Application configuration containing LLM and MCP settings
        """
        self.config = config
        self.llm_client = LLMClient(config.llm)
        self.mcp_manager = MCPClientManager()
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize all coordinator components

        This method:
        1. Initializes MCP server connections
        2. Discovers available tools from all servers
        4. Validates the configuration

        Raises:
            CoordinatorInitializationError: If initialization fails
        """
        if self._initialized:
            return

        try:

            # Initialize MCP connections first
            if self.config.mcp_servers:
                await self.mcp_manager.initialize_servers(self.config.mcp_servers)

            else:
                pass

            self._initialized = True

        except Exception as e:
            # Cleanup any partial initialization
            try:
                await self.cleanup()
            except Exception:
                pass

            raise CoordinatorInitializationError(f"Initialization failed: {e}")

    async def process_message(
        self,
        message: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        llm_config_override: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process a user message and return streaming responses (stateless mode)

        This is the main entry point for message processing. It:
        1. Creates a Conversation object from conversation_history
        2. Adds the current user message (if provided)
        3. Gets available tools from MCP servers
        4. Streams LLM response with tool call handling

        Args:
            message: Current user input message (optional if conversation_history provided)
            conversation_history: Complete conversation history in OpenAI format
            llm_config_override: Optional LLM configuration overrides

        Yields:
            dict: Streaming response events with types:
                - content_delta: Incremental content from LLM
                - reasoning_delta: Reasoning content (for reasoning models)
                - tool_calls: Tool calls requested by LLM
                - tool_result: Results from tool execution
                - tool_error: Tool execution errors
                - done: Processing complete

        Raises:
            CoordinatorProcessingError: If message processing fails
        """
        if not self._initialized:
            raise CoordinatorProcessingError("Coordinator not initialized")

        # 验证输入
        if not message and not conversation_history:
            raise ValidationError(
                "Either message or conversation_history must be provided"
            )

        # 如果没有提供conversation_history，创建空列表
        if conversation_history is None:
            conversation_history = []

        try:
            # 创建Conversation对象
            from bizyengine.bizybot.models import (
                Conversation,
                ConversationValidationError,
            )

            try:
                conversation = Conversation.from_openai_format(conversation_history)

                # 添加当前用户消息
                if message and message.strip():
                    conversation.add_user_message(message.strip())

            except ConversationValidationError as e:
                raise ValidationError(f"Invalid conversation_history format: {e}")

            # Get available tools from MCP servers
            tool_schemas = self.mcp_manager.get_tools_for_llm()

            # Process the conversation with streaming
            async for event in self._process_llm_stream(
                conversation, tool_schemas, llm_config_override
            ):
                yield event

        except Exception as e:
            yield {"type": "error", "error": str(e), "error_type": type(e).__name__}
            raise CoordinatorProcessingError(f"Message processing failed: {e}")

    async def _process_llm_stream(
        self,
        conversation: "Conversation",
        tool_schemas: List[Dict[str, Any]],
        llm_config_override: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process LLM streaming response and handle tool calls

        This method implements the core conversation loop:
        1. Send conversation context to LLM with available tools
        2. Stream LLM response, handling content and tool calls
        3. Execute any requested tool calls via MCP
        4. Continue conversation with tool results until completion

        Args:
            conversation: Current conversation context (Conversation object)
            tool_schemas: Available tools in OpenAI format
            llm_config_override: Optional LLM configuration overrides

        Yields:
            dict: Streaming response events
        """
        try:
            system_prompt = """# 角色和目标
                    你是一个专业的AI图像助手。你的核心任务是精确理解用户的请求，并智能地调用合适的工具来完成 “生成新图片” 或 “从现有图片中提取对象” 或 “编辑图片” 的任务。你的决策必须准确无误。
                    # 工作流程与决策逻辑
                    你的工作流程必须遵循以下逻辑：

                    意图识别 (最重要):

                    生成意图: 用户的请求是凭空创造内容吗？（例如：“画一只戴着帽子的狗”） -> 使用 text2image。

                    提取意图: 用户的请求是基于一张已经存在的图片进行操作吗？（例如：“把这张图里的狗抠出来”） -> 使用 extract_image。

                    处理模糊请求:

                    如果用户的请求非常模糊（例如：“我想要一辆车”），你 绝不能猜测。

                    你必须主动提问以澄清用户的真实意图。标准问法：“请问您是想让我生成一张新的关于‘车’的图片，还是您已经有一张图片，需要我从中提取出‘车’？”

                    参数检查:

                    在调用任何工具之前，必须在内心确认所有 必需 参数都已具备。

                    调用 extract_image 前，必须确认你 同时拥有 用户的图片和要提取的对象名称。

                    回复：在调用工具前先提示用户你即将调用工具，在拿到工具的结果之后再进行总结，并将工具结果返回给用户

                    # 示例
                    示例 1: 正确使用 text2image
                    用户: “给我画一张赛博朋克风格的东京夜景，要有很多霓虹灯。”

                    你的思考: 用户的意图是“画”，是创造新图片。我应该使用 text2image。

                    工具调用: print(text2image(user_prompt="赛博朋克风格的东京夜景，有很多霓虹灯", width=1024, height=1024))

                    示例 2: 正确使用 extract_image
                    用户: [上传一张家庭聚会照片] “把照片里那个穿红色裙子的小女孩提取出来。”

                    你的思考: 用户提供了一张图片，并要求“提取”其中的特定人物。我应该使用 extract_image。

                    工具调用: print(extract_image(image=[上传的图片数据], value="穿红色裙子的小女孩"))

                    示例 3: 正确处理模糊请求
                    用户: “帮我弄一只猫。”

                    你的思考: “弄”这个词太模糊了。我不知道是生成还是提取。我必须提问。

                    你的回复 (对用户): “好的！请问您是想让我为您画一只全新的猫，还是您有一张包含猫的图片，需要我帮您把猫提取出来？”

                    converation_history中保存的是与用户会话的历史记录，里面可能包含需要编辑的图片的url

                    """
            conversation.add_system_message(system_prompt)
            # Prepare messages for LLM
            messages = conversation.get_openai_messages_for_llm()

            # Prepare LLM parameters
            llm_params = {}
            if llm_config_override:
                llm_params.update(llm_config_override)

            # Start streaming from LLM
            stream = await self.llm_client.chat_completion(
                messages=messages,
                tools=tool_schemas if tool_schemas else None,
                stream=True,
                **llm_params,
            )

            # Process streaming response
            accumulated_content = ""
            accumulated_reasoning = ""
            tool_calls_completed = []

            # 重置流式工具调用处理器状态，确保每次对话开始时状态干净
            self.llm_client.clear_streaming_tool_calls()

            async for chunk in stream:
                # Debug: Log chunk structure (using INFO for visibility)
                # logger.info(f"Received chunk: {chunk}")

                # Handle content deltas
                if chunk.get("content"):
                    accumulated_content += chunk["content"]
                    yield {"type": "content_delta", "content": chunk["content"]}

                # Handle reasoning content (for reasoning models)
                if chunk.get("reasoning_content"):
                    accumulated_reasoning += chunk["reasoning_content"]
                    yield {
                        "type": "reasoning_delta",
                        "reasoning_content": chunk["reasoning_content"],
                    }

                # Handle tool calls - 累积工具调用数据；在结束帧收敛
                tool_calls_completed = (
                    self.llm_client.process_streaming_tool_calls_incremental(chunk)
                )

                # Handle completion - 只在这里完成和处理工具调用
                if chunk.get("finish_reason"):

                    # 第一个判断 - 完成工具调用解析
                    if chunk["finish_reason"] == "tool_calls":
                        """
                        将流式传输中累积的部分数据（ID、函数名、参数片段）组装成完整的工具调用对象
                        验证JSON参数格式是否正确
                        创建 ToolCall 对象
                        并不执行任何实际的工具功能
                        """
                        if tool_calls_completed:

                            yield {
                                "type": "tool_calls",
                                "tool_calls": [
                                    tc.to_dict() for tc in tool_calls_completed
                                ],
                            }
                        # else:
                        # 如果没有完成工具调用，可以在此处读取当前状态用于调试
                        # 若工具命令不完全可以在这里拿到传回给llm重试
                        # self.llm_client.get_streaming_tool_call_status()

                    # 第二个判断 - 执行工具调用或完成对话
                    if chunk["finish_reason"] == "tool_calls" and tool_calls_completed:
                        # 执行工具调用并继续对话
                        async for tool_event in self._execute_tool_calls_and_continue(
                            conversation,
                            tool_calls_completed,
                            accumulated_content,
                            accumulated_reasoning,
                            tool_schemas,
                            llm_config_override,
                        ):
                            yield tool_event
                    else:
                        # 常规完成 - 添加助手消息到对话
                        if accumulated_content or accumulated_reasoning:
                            conversation.add_assistant_message(
                                content=accumulated_content or None
                            )

                        yield {"type": "done", "finish_reason": chunk["finish_reason"]}
                    break

        except LLMError as e:
            yield {
                "type": "error",
                "error": f"LLM error: {str(e)}",
                "error_type": "LLMError",
            }
        except Exception as e:
            yield {
                "type": "error",
                "error": f"Streaming error: {str(e)}",
                "error_type": type(e).__name__,
            }

    async def _execute_tool_calls_and_continue(
        self,
        conversation: Conversation,
        tool_calls: List[ToolCall],
        assistant_content: str,
        assistant_reasoning: str,
        tool_schemas: List[Dict[str, Any]],
        llm_config_override: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute tool calls and continue the conversation

        This method:
        1. Adds the assistant message with tool calls to conversation
        2. Executes all tool calls (potentially in parallel)
        3. Adds tool results to conversation
        4. Continues LLM conversation to generate final response

        Args:
            conversation: Current conversation
            tool_calls: List of tool calls to execute
            assistant_content: Assistant's content before tool calls
            assistant_reasoning: Assistant's reasoning content
            tool_schemas: Available tool schemas
            llm_config_override: Optional LLM config overrides

        Yields:
            dict: Tool execution and continuation events
        """
        try:
            # Add assistant message with tool calls to conversation
            from bizyengine.bizybot.models import Message

            assistant_message = Message(
                role="assistant",
                content=assistant_content if assistant_content else None,
                reasoning_content=assistant_reasoning if assistant_reasoning else None,
                tool_calls=tool_calls,
            )
            conversation.add_message(assistant_message)

            # Execute tool calls
            tool_call_dicts = [tc.to_dict() for tc in tool_calls]

            # Execute tool calls via MCP manager (supports parallel execution)
            tool_results = await self.mcp_manager.execute_tool_calls(tool_call_dicts)

            # Process tool results and add to conversation
            for i, result in enumerate(tool_results):
                tool_call = tool_calls[i]

                if result.get("success", False):
                    # Successful tool execution
                    tool_content = result.get("content", "")

                    yield {
                        "type": "tool_result",
                        "tool_call_id": tool_call.id,
                        "result": tool_content,
                        "server_name": result.get("_mcp_server"),
                    }

                    # Add tool result to conversation - 使用格式化后的内容
                    conversation.add_tool_result(tool_call.id, tool_content)

                else:
                    # Tool execution error
                    error_msg = result.get("content", "Unknown tool execution error")
                    yield {
                        "type": "tool_error",
                        "tool_call_id": tool_call.id,
                        "error": error_msg,
                    }

                    # Add error result to conversation
                    conversation.add_tool_result(tool_call.id, f"Error: {error_msg}")

            # Stream response from LLM - 可能包含更多工具调用
            # 使用递归调用_process_llm_stream来处理可能的多轮工具调用
            async for event in self._process_llm_stream(
                conversation, tool_schemas, llm_config_override
            ):
                yield event

        except MCPError as e:
            yield {
                "type": "error",
                "error": f"Tool execution error: {str(e)}",
                "error_type": "MCPError",
            }
        except Exception as e:
            yield {
                "type": "error",
                "error": f"Tool execution error: {str(e)}",
                "error_type": type(e).__name__,
            }

    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of all available tools from MCP servers

        Returns:
            List of tool definitions in OpenAI format
        """
        if not self._initialized:
            return []

        return self.mcp_manager.get_tools_for_llm()

    def get_server_status(self) -> Dict[str, Any]:
        """
        Get status of all MCP servers and coordinator

        Returns:
            Status dictionary with server and coordinator information
        """
        server_status = self.mcp_manager.get_server_status()

        return {
            "coordinator": {
                "initialized": self._initialized,
                "llm_model": self.config.llm.model,
                "llm_base_url": self.config.llm.base_url,
                "mode": "stateless",
            },
            "mcp_servers": server_status,
            "conversations": {
                "mode": "stateless",
                "note": "Conversations are managed by client in stateless mode",
            },
        }

    async def cleanup(self) -> None:
        """
        Cleanup all coordinator resources

        This method:
        1. Closes LLM client connections
        2. Cleans up all MCP connections
        3. Resets initialization status
        """

        try:
            # Cleanup LLM client
            if self.llm_client:
                await self.llm_client.close()

            # Cleanup MCP manager
            if self.mcp_manager:
                await self.mcp_manager.cleanup()

            self._initialized = False

        except Exception as e:
            raise CoordinatorError(f"Cleanup failed: {e}")

    def is_initialized(self) -> bool:
        """Check if coordinator is initialized"""
        return self._initialized

    def format_streaming_event(self, event: dict) -> dict:
        """
        Format streaming event according to design specification

        Ensures all streaming events follow the correct format:
        - content_delta: {"type": "content_delta", "content": "..."}
        - reasoning_delta: {"type": "reasoning_delta", "reasoning_content": "..."}
        - tool_calls: {"type": "tool_calls", "tool_calls": [...]}
        - tool_result: {"type": "tool_result", "tool_call_id": "...", "result": {...}}
        - tool_error: {"type": "tool_error", "tool_call_id": "...", "error": "..."}
        - done: {"type": "done", "finish_reason": "..."}
        """
        event_type = event.get("type")

        # Validate and format based on event type
        if event_type == "content_delta":
            return {"type": "content_delta", "content": event.get("content", "")}
        elif event_type == "reasoning_delta":
            return {
                "type": "reasoning_delta",
                "reasoning_content": event.get("reasoning_content", ""),
            }
        elif event_type == "tool_calls":
            return {"type": "tool_calls", "tool_calls": event.get("tool_calls", [])}
        elif event_type == "tool_result":
            return {
                "type": "tool_result",
                "tool_call_id": event.get("tool_call_id"),
                "result": event.get("result"),
                "server_name": event.get("server_name"),
            }
        elif event_type == "tool_error":
            return {
                "type": "tool_error",
                "tool_call_id": event.get("tool_call_id"),
                "error": event.get("error"),
            }
        elif event_type == "done":
            return {"type": "done", "finish_reason": event.get("finish_reason", "stop")}
        elif event_type == "error":
            return {
                "type": "error",
                "error": event.get("error"),
                "error_type": event.get("error_type"),
            }
        elif event_type == "conversation_started":
            return {
                "type": "conversation_started",
                "conversation_id": event.get("conversation_id"),
            }
        else:
            # Pass through unknown event types
            return event
