"""
LLM客户端模块 - 封装OpenAI API调用
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import aiohttp
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from bizyengine.bizybot.exceptions import (
    LLMAPIError,
    LLMResponseError,
    LLMTimeoutError,
    ToolValidationError,
)
from bizyengine.core.common.env_var import BIZYAIR_X_SERVER


@dataclass
class LLMConfig:
    """LLM配置"""

    api_key: str
    base_url: str = BIZYAIR_X_SERVER
    model: str = "moonshotai/Kimi-K2-Instruct"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: float = 30.0


@dataclass
class ToolFunction:
    """工具函数定义"""

    name: str
    arguments: str  # JSON字符串格式


@dataclass
class ToolCall:
    """工具调用"""

    id: str
    type: str  # 目前只支持 "function"
    function: ToolFunction
    result: Optional[dict] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "type": self.type,
            "function": {
                "name": self.function.name,
                "arguments": self.function.arguments,
            },
        }


@dataclass
class Message:
    """消息"""

    role: str  # "user", "assistant", "system", "tool"
    content: Optional[str] = None
    reasoning_content: Optional[str] = None  # 支持推理模型
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_openai_format(self) -> dict:
        """转换为OpenAI API格式"""
        msg = {"role": self.role}

        if self.content is not None:
            msg["content"] = self.content

        if self.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in self.tool_calls
            ]

        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id

        return msg


@dataclass
class Usage:
    """使用统计"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class LLMResponse:
    """LLM响应"""

    id: str
    choices: List["ResponseChoice"]
    usage: Optional[Usage] = None
    created: Optional[int] = None
    model: Optional[str] = None
    object: str = "chat.completion"


@dataclass
class ResponseChoice:
    """响应选择"""

    message: Message
    finish_reason: Optional[str] = None  # "stop", "eos", "length", "tool_calls"


class ToolCallProcessor:
    """工具调用处理器"""

    def extract_tool_calls(self, message: Message) -> List[ToolCall]:
        """从消息中提取工具调用"""
        if not message.tool_calls:
            return []

        tool_calls = []
        for tc in message.tool_calls:
            try:
                # 验证工具调用格式
                if tc.type != "function":
                    continue

                # 解析和验证参数JSON（仅校验，不保留变量以避免未使用告警）
                self._parse_and_validate_arguments(tc.function.arguments)

                tool_call = ToolCall(
                    id=tc.id,
                    type=tc.type,
                    function=ToolFunction(
                        name=tc.function.name, arguments=tc.function.arguments
                    ),
                )
                tool_calls.append(tool_call)

            except Exception:
                # 解析错误但继续处理其他工具调用
                continue

        return tool_calls

    def _parse_and_validate_arguments(self, arguments_str: str) -> dict:
        """解析和验证工具参数"""
        try:
            arguments = json.loads(arguments_str)
            if not isinstance(arguments, dict):
                raise ToolValidationError("Arguments must be a JSON object")
            return arguments
        except json.JSONDecodeError as e:
            raise ToolValidationError(f"Invalid JSON in tool arguments: {e}") from e

    def validate_tool_arguments(self, tool_call: ToolCall, tool_schema: dict) -> dict:
        """验证工具参数是否符合工具模式"""
        try:
            arguments = json.loads(tool_call.function.arguments)

            # 基本类型检查
            if not isinstance(arguments, dict):
                raise ToolValidationError("Tool arguments must be a JSON object")

            # 如果有schema，进行更详细的验证
            if tool_schema and "parameters" in tool_schema:
                self._validate_against_schema(arguments, tool_schema["parameters"])

            return arguments

        except json.JSONDecodeError as e:
            raise ToolValidationError(f"Invalid JSON in tool arguments: {e}") from e
        except ToolValidationError:
            raise
        except Exception as e:
            raise ToolValidationError(f"Tool argument validation failed: {e}") from e

    def _validate_against_schema(self, arguments: dict, schema: dict) -> None:
        """根据JSON Schema验证参数"""
        # 基础验证 - 检查必需参数
        if "required" in schema:
            for required_field in schema["required"]:
                if required_field not in arguments:
                    raise ToolValidationError(
                        f"Missing required parameter: {required_field}"
                    )

        # 检查参数类型（简化版本）
        if "properties" in schema:
            for param_name, param_value in arguments.items():
                if param_name in schema["properties"]:
                    expected_type = schema["properties"][param_name].get("type")
                    if expected_type and not self._check_type(
                        param_value, expected_type
                    ):
                        raise ToolValidationError(
                            f"Parameter {param_name} has wrong type, expected {expected_type}"
                        )

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查值的类型是否符合预期"""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)

        return True  # 未知类型，跳过检查


class StreamingToolCallHandler:
    """流式工具调用处理器"""

    def __init__(self):
        self.partial_tool_calls = {}  # 存储部分工具调用数据
        self.tool_processor = ToolCallProcessor()

    def process_streaming_tool_calls(self, chunk: dict) -> Optional[List[ToolCall]]:
        """处理流式响应中的工具调用"""
        # 处理工具调用数据
        if "tool_calls" in chunk:
            tool_calls_delta = chunk["tool_calls"]

            for tc_delta in tool_calls_delta:
                # 获取工具调用的索引，用于匹配（OpenAI流式响应中的关键字段）
                call_index = tc_delta.get("index", 0)
                call_id = tc_delta.get("id")

                # 使用索引作为主要标识符，因为在流式响应中ID可能为空
                primary_key = f"call_{call_index}"

                # 累积工具调用数据
                if primary_key not in self.partial_tool_calls:
                    self.partial_tool_calls[primary_key] = {
                        "id": call_id or "",  # 初始化为空字符串，等待真实ID
                        "index": call_index,
                        "type": tc_delta.get("type", "function"),
                        "function": {"name": "", "arguments": ""},
                    }

                # 更新真实ID（如果提供了）- 这通常在第一个chunk中出现
                if call_id and call_id != "":
                    self.partial_tool_calls[primary_key]["id"] = call_id

                # 更新函数名称
                if (
                    "function" in tc_delta
                    and "name" in tc_delta["function"]
                    and tc_delta["function"]["name"]
                ):
                    self.partial_tool_calls[primary_key]["function"][
                        "name"
                    ] += tc_delta["function"]["name"]

                # 累积参数
                if (
                    "function" in tc_delta
                    and "arguments" in tc_delta["function"]
                    and tc_delta["function"]["arguments"]
                ):
                    self.partial_tool_calls[primary_key]["function"][
                        "arguments"
                    ] += tc_delta["function"]["arguments"]

        # 检查是否有完整的工具调用 - 当收到finish_reason时完成工具调用
        if chunk.get("finish_reason") == "tool_calls":
            return self._finalize_tool_calls()

        return None

    def _finalize_tool_calls(self) -> Optional[List[ToolCall]]:
        """
        完成部分工具调用 - 将之前累积的工具调用数据转换为完整的工具调用对象执行
        工具调用 - 通过 MCP 服务器执行这些工具
        继续对话 - 将工具执行结果返回给 LLM 继续生成响应
        """
        if not self.partial_tool_calls:
            return None

        completed_calls = []
        for primary_key, call_data in self.partial_tool_calls.items():
            try:
                # 验证参数是否为完整的JSON
                # 确保有有效的ID
                # 创建完整的ToolCall对象
                arguments_str = call_data["function"]["arguments"]
                if arguments_str:  # 只有当参数不为空时才验证
                    self.tool_processor._parse_and_validate_arguments(arguments_str)

                # 确保有有效的ID，如果没有则使用primary_key
                tool_id = call_data["id"] if call_data["id"] else primary_key

                # 创建工具调用对象
                tool_call = ToolCall(
                    id=tool_id,
                    type=call_data["type"],
                    function=ToolFunction(
                        name=call_data["function"]["name"], arguments=arguments_str
                    ),
                )
                completed_calls.append(tool_call)

            except (json.JSONDecodeError, ValueError):
                pass

        # 清理已完成的调用
        self.partial_tool_calls.clear()

        return completed_calls if completed_calls else None

    def get_partial_tool_calls(self) -> Dict[str, dict]:
        """获取当前部分工具调用状态（用于调试）"""
        return self.partial_tool_calls.copy()

    def clear_partial_calls(self) -> None:
        """清理部分工具调用数据"""
        self.partial_tool_calls.clear()


class LLMClient:
    """LLM客户端 - 封装OpenAI API调用"""

    def __init__(self, config: LLMConfig):
        """初始化LLM客户端"""
        self.config = config
        self._client = None
        self._session = None
        self._streaming_handler = StreamingToolCallHandler()
        self._tool_processor = ToolCallProcessor()

    @property
    def client(self) -> AsyncOpenAI:
        """获取OpenAI客户端实例"""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
        return self._client

    @property
    def session(self) -> aiohttp.ClientSession:
        """获取aiohttp会话实例"""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def chat_completion(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Union[LLMResponse, AsyncIterator[dict]]:
        """
        发送聊天完成请求

        Args:
            messages: 消息列表
            tools: 可用工具列表
            stream: 是否使用流式响应
            **kwargs: 其他参数

        Returns:
            LLMResponse或流式响应迭代器
        """
        try:
            # 合并配置参数
            params = {
                "model": kwargs.get("model", self.config.model),
                "messages": messages,
                "temperature": kwargs.get("temperature", self.config.temperature),
                "stream": stream,
            }

            if self.config.max_tokens:
                params["max_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)

            if tools:
                params["tools"] = tools

            try:
                if stream:
                    # 流式响应
                    stream_response = await self.client.chat.completions.create(
                        **params
                    )
                    result = self._process_streaming_response(stream_response)
                    return result
                else:
                    # 非流式响应
                    response = await self.client.chat.completions.create(**params)
                    result = self._parse_completion_response(response)
                    return result
            except Exception:
                raise

        except asyncio.TimeoutError as e:
            raise LLMTimeoutError(
                f"Request timeout after {self.config.timeout}s"
            ) from e
        except Exception as e:
            # Determine if it's an API error with status code
            status_code = getattr(e, "status_code", None)
            response_body = getattr(e, "response", None)
            if response_body:
                response_body = str(response_body)

            raise LLMAPIError(
                f"API call failed: {str(e)}",
                status_code=status_code,
                response_body=response_body,
            ) from e

    def _parse_completion_response(self, response: ChatCompletion) -> LLMResponse:
        """非流式解析完整响应"""
        choices = []
        for choice in response.choices:
            # 解析工具调用
            tool_calls = None
            if choice.message.tool_calls:
                tool_calls = [
                    ToolCall(
                        id=tc.id,
                        type=tc.type,
                        function=ToolFunction(
                            name=tc.function.name, arguments=tc.function.arguments
                        ),
                    )
                    for tc in choice.message.tool_calls
                ]

            message = Message(
                role=choice.message.role,
                content=choice.message.content,
                tool_calls=tool_calls,
            )

            choices.append(
                ResponseChoice(message=message, finish_reason=choice.finish_reason)
            )

        usage = None
        if response.usage:
            usage = Usage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )

        return LLMResponse(
            id=response.id,
            choices=choices,
            usage=usage,
            created=response.created,
            model=response.model,
            object=response.object,
        )

    async def _process_streaming_response(self, stream) -> AsyncIterator[dict]:
        """接收原始、复杂的数据流，然后把它实时地翻译和整理成一种更干净、更标准化的格式，但是不对参数进行整理积累，而是返回增量参数"""
        try:
            async for chunk in stream:

                if chunk.choices:
                    choice = chunk.choices[0]
                    delta = choice.delta

                    result = {
                        "type": "chunk",
                        "id": chunk.id,
                        "created": chunk.created,
                        "model": chunk.model,
                    }

                    # 处理内容增量
                    if delta.content:
                        result["content"] = delta.content

                    # 处理推理内容增量（如果支持）
                    if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                        result["reasoning_content"] = delta.reasoning_content

                    # 处理工具调用 - 支持delta中的tool_calls
                    if hasattr(delta, "tool_calls") and delta.tool_calls:
                        result["tool_calls"] = [
                            {
                                "id": tc.id if tc.id else "",
                                "index": getattr(tc, "index", 0),  # 添加index字段
                                "type": tc.type if tc.type else "function",
                                "function": {
                                    "name": (
                                        tc.function.name
                                        if tc.function and tc.function.name
                                        else ""
                                    ),
                                    "arguments": (
                                        tc.function.arguments
                                        if tc.function and tc.function.arguments
                                        else ""
                                    ),
                                },
                            }
                            for tc in delta.tool_calls
                        ]

                    # 处理完整消息中的工具调用（某些API可能在这里返回）
                    if (
                        hasattr(choice, "message")
                        and hasattr(choice.message, "tool_calls")
                        and choice.message.tool_calls
                    ):
                        result["tool_calls"] = [
                            {
                                "id": tc.id if tc.id else "",
                                "type": tc.type if tc.type else "function",
                                "function": {
                                    "name": (
                                        tc.function.name
                                        if tc.function and tc.function.name
                                        else ""
                                    ),
                                    "arguments": (
                                        tc.function.arguments
                                        if tc.function and tc.function.arguments
                                        else ""
                                    ),
                                },
                            }
                            for tc in choice.message.tool_calls
                        ]

                    # 处理结束原因
                    if choice.finish_reason:
                        result["finish_reason"] = choice.finish_reason

                    yield result

        except Exception as e:
            raise LLMResponseError(f"Streaming response error: {str(e)}") from e

    async def parse_streaming_response(
        self, stream: AsyncIterator[bytes]
    ) -> AsyncIterator[dict]:
        """
        解析SSE流式响应

        Args:
            stream: 字节流迭代器

        Yields:
            解析后的响应数据
        """
        try:
            buffer = ""
            async for chunk in stream:
                if isinstance(chunk, bytes):
                    chunk = chunk.decode("utf-8")

                buffer += chunk
                lines = buffer.split("\n")
                buffer = lines[-1]  # 保留最后一行（可能不完整）

                for line in lines[:-1]:
                    line = line.strip()
                    if line.startswith("data: "):
                        data_str = line[6:].strip()

                        if data_str == "[DONE]":
                            return

                        try:
                            chunk_data = json.loads(data_str)

                            # 解析流式chunk
                            if chunk_data.get("object") == "chat.completion.chunk":
                                yield self._process_sse_chunk(chunk_data)

                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            raise LLMResponseError(f"Streaming parse error: {str(e)}") from e

    def _process_sse_chunk(self, chunk_data: dict) -> dict:
        """处理单个SSE数据块"""
        choice = chunk_data["choices"][0]
        delta = choice.get("delta", {})

        result = {
            "type": "chunk",
            "id": chunk_data["id"],
            "created": chunk_data.get("created"),
            "model": chunk_data.get("model"),
        }

        # 处理内容增量
        if "content" in delta and delta["content"]:
            result["content"] = delta["content"]

        # 处理推理内容增量
        if "reasoning_content" in delta and delta["reasoning_content"]:
            result["reasoning_content"] = delta["reasoning_content"]

        # 处理工具调用
        if "tool_calls" in delta and delta["tool_calls"]:
            result["tool_calls"] = delta["tool_calls"]

        # 处理结束原因
        if choice.get("finish_reason"):
            result["finish_reason"] = choice["finish_reason"]

        return result

    async def handle_streaming_with_reconnect(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        max_retries: int = 3,
        **kwargs,
    ) -> AsyncIterator[dict]:
        """
        带重连机制的流式响应处理

        Args:
            messages: 消息列表
            tools: 可用工具列表
            max_retries: 最大重试次数
            **kwargs: 其他参数

        Yields:
            流式响应数据
        """
        retry_count = 0

        while retry_count <= max_retries:
            try:
                stream = await self.chat_completion(
                    messages=messages, tools=tools, stream=True, **kwargs
                )

                async for chunk in stream:
                    yield chunk

                # 成功完成，退出重试循环
                break

            except (LLMTimeoutError,):
                retry_count += 1
                if retry_count > max_retries:
                    raise

                wait_time = min(2**retry_count, 30)  # 指数退避，最大30秒
                await asyncio.sleep(wait_time)

            except Exception:
                raise

    async def parse_tool_calls(self, response: LLMResponse) -> List[ToolCall]:
        """
        解析LLM响应中的工具调用

        Args:
            response: LLM响应对象

        Returns:
            工具调用列表
        """
        tool_calls = []

        for choice in response.choices:
            if choice.message.tool_calls:
                extracted_calls = self._tool_processor.extract_tool_calls(
                    choice.message
                )
                tool_calls.extend(extracted_calls)

        return tool_calls

    async def validate_tool_arguments(
        self, tool_call: ToolCall, tool_schema: dict
    ) -> dict:
        """
        验证工具调用参数

        Args:
            tool_call: 工具调用对象
            tool_schema: 工具的JSON Schema

        Returns:
            验证后的参数字典

        Raises:
            ValueError: 参数验证失败
        """
        return self._tool_processor.validate_tool_arguments(tool_call, tool_schema)

    def extract_tool_calls_from_message(self, message: Message) -> List[ToolCall]:
        """
        从消息中提取工具调用

        Args:
            message: 消息对象

        Returns:
            工具调用列表
        """
        return self._tool_processor.extract_tool_calls(message)

    def process_streaming_tool_calls_incremental(
        self, chunk: dict
    ) -> Optional[List[ToolCall]]:
        """
        增量处理流式工具调用

        Args:
            chunk: 流式响应块

        Returns:
            完成的工具调用列表（如果有）
        """
        return self._streaming_handler.process_streaming_tool_calls(chunk)

    def get_streaming_tool_call_status(self) -> Dict[str, dict]:
        """获取当前流式工具调用的状态"""
        return self._streaming_handler.get_partial_tool_calls()

    def clear_streaming_tool_calls(self) -> None:
        """清理流式工具调用状态"""
        self._streaming_handler.clear_partial_calls()

    def update_config(self, config: LLMConfig) -> None:
        """更新配置"""
        self.config = config
        # 重置客户端以使用新配置
        self._client = None

    async def close(self) -> None:
        """关闭客户端连接"""
        if self._client:
            await self._client.close()
            self._client = None

        if self._session:
            await self._session.close()
            self._session = None
