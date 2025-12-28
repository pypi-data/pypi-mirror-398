"""
Data models for conversation management
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


class ConversationValidationError(Exception):
    """对话验证错误"""

    pass


@dataclass
class ToolCall:
    """Represents a tool call from LLM"""

    id: str
    type: str  # Currently only "function"
    function: "ToolFunction"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "id": self.id,
            "type": self.type,
            "function": {
                "name": self.function.name,
                "arguments": self.function.arguments,
            },
        }


@dataclass
class ToolFunction:
    """Represents a function call within a tool call"""

    name: str
    arguments: str  # JSON string format


@dataclass
class Message:
    """Represents a conversation message"""

    role: str  # "user", "assistant", "system", "tool"
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    reasoning_content: Optional[str] = None  # For reasoning models like deepseek-R1

    def __post_init__(self):
        """Validate message after initialization"""
        if self.role not in ["user", "assistant", "system", "tool"]:
            raise ValueError(f"Invalid role: {self.role}")

        if self.role == "tool" and not self.tool_call_id:
            raise ValueError("Tool messages must have a tool_call_id")

        if self.role == "tool" and not self.content:
            raise ValueError("Tool messages must have content")

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI API format"""
        msg = {"role": self.role}

        # Only include content if it's not None
        if self.content is not None:
            msg["content"] = self.content

        if self.tool_calls:
            msg["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]

        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id

        # Note: reasoning_content is not included in OpenAI format
        # as it's handled separately in the conversation flow

        return msg


@dataclass
class Conversation:
    """Represents a conversation with message history"""

    id: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation"""
        message = Message(role="user", content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()

    def add_assistant_message(
        self, content: str, tool_calls: Optional[List[ToolCall]] = None
    ) -> None:
        """Add an assistant message to the conversation"""
        message = Message(role="assistant", content=content, tool_calls=tool_calls)
        self.messages.append(message)
        self.updated_at = datetime.now()

    def add_tool_result(self, tool_call_id: str, result: Any) -> None:
        """Add a tool result message to the conversation"""
        # Handle different result types
        if isinstance(result, str):
            content = result
        elif isinstance(result, dict):
            # 如果是字典，尝试提取有用信息
            content = str(result)
        else:
            content = str(result)

        message = Message(role="tool", content=content, tool_call_id=tool_call_id)
        self.messages.append(message)
        self.updated_at = datetime.now()

    def add_system_message(self, content: str) -> None:
        """Add a system message to the conversation"""
        message = Message(role="system", content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()

    def add_message(self, message: Message) -> None:
        """Add a message to the conversation"""
        self.messages.append(message)
        self.updated_at = datetime.now()

    def to_openai_format(self) -> List[Dict[str, Any]]:
        """Convert conversation to OpenAI API format"""
        return [msg.to_openai_format() for msg in self.messages]

    def get_message_count(self) -> int:
        """Get total number of messages"""
        return len(self.messages)

    def get_last_message(self) -> Optional[Message]:
        """Get the last message in the conversation"""
        return self.messages[-1] if self.messages else None

    def get_messages_by_role(self, role: str) -> List[Message]:
        """Get all messages with a specific role"""
        return [msg for msg in self.messages if msg.role == role]

    def get_recent_messages(self, count: int) -> List[Message]:
        """Get the most recent N messages"""
        return self.messages[-count:] if count > 0 else []

    def clear_messages(self) -> None:
        """Clear all messages from the conversation"""
        self.messages.clear()
        self.updated_at = datetime.now()

    def has_tool_calls(self) -> bool:
        """Check if the conversation has any pending tool calls"""
        last_message = self.get_last_message()
        return (
            last_message
            and last_message.role == "assistant"
            and last_message.tool_calls is not None
            and len(last_message.tool_calls) > 0
        )

    @classmethod
    def from_openai_format(
        cls,
        conversation_history: List[Dict[str, Any]],
        conversation_id: Optional[str] = None,
    ) -> "Conversation":
        """
        从OpenAI格式的对话历史创建Conversation实例

        Args:
            conversation_history: OpenAI格式的消息列表
            conversation_id: 可选的对话ID，如果不提供则生成新的

        Returns:
            Conversation实例

        Raises:
            ConversationValidationError: 如果消息格式无效
        """
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        messages = []
        current_time = datetime.now()

        for i, msg_data in enumerate(conversation_history):
            try:
                message = cls._parse_message_from_dict(msg_data)
                messages.append(message)
            except Exception as e:
                raise ConversationValidationError(
                    f"Invalid message format at index {i}: {e}"
                ) from e

        return cls(
            id=conversation_id,
            messages=messages,
            created_at=current_time,
            updated_at=current_time,
        )

    @staticmethod
    def _parse_message_from_dict(msg_data: Dict[str, Any]) -> Message:
        """解析单个消息字典为Message对象"""

        # 验证必需字段
        if "role" not in msg_data:
            raise ConversationValidationError("Message must have 'role' field")

        role = msg_data["role"]
        if role not in ["user", "assistant", "system", "tool"]:
            raise ConversationValidationError(f"Invalid role: {role}")

        content = msg_data.get("content")

        # 解析工具调用（如果存在）
        tool_calls = None
        if "tool_calls" in msg_data and msg_data["tool_calls"]:
            tool_calls = []
            for tc_data in msg_data["tool_calls"]:
                if not isinstance(tc_data, dict):
                    raise ConversationValidationError(
                        "Each tool_call must be a dictionary"
                    )

                if "id" not in tc_data or "function" not in tc_data:
                    raise ConversationValidationError(
                        "tool_call must have 'id' and 'function' fields"
                    )

                function = tc_data["function"]
                if "name" not in function or "arguments" not in function:
                    raise ConversationValidationError(
                        "function must have 'name' and 'arguments' fields"
                    )

                # 验证arguments是否为有效JSON
                try:
                    json.loads(function["arguments"])
                except json.JSONDecodeError as e:
                    raise ConversationValidationError(
                        f"Invalid JSON in function arguments: {e}"
                    )

                tool_call = ToolCall(
                    id=str(tc_data["id"]),
                    type=tc_data.get("type", "function"),
                    function=ToolFunction(
                        name=str(function["name"]), arguments=str(function["arguments"])
                    ),
                )
                tool_calls.append(tool_call)

        # 获取工具调用ID（用于tool角色消息）
        tool_call_id = msg_data.get("tool_call_id")
        if role == "tool" and not tool_call_id:
            raise ConversationValidationError("Tool messages must have a tool_call_id")

        # 处理推理内容（如果存在）
        reasoning_content = msg_data.get("reasoning_content")

        return Message(
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=str(tool_call_id) if tool_call_id else None,
            reasoning_content=reasoning_content,
        )

    @staticmethod
    def validate_conversation_history(
        conversation_history: List[Dict[str, Any]],
    ) -> bool:
        """验证对话历史格式是否正确"""
        try:
            if not isinstance(conversation_history, list):
                return False

            for msg_data in conversation_history:
                # 基本字段验证
                if not isinstance(msg_data, dict):
                    return False

                if "role" not in msg_data:
                    return False

                role = msg_data["role"]
                if role not in ["user", "assistant", "system", "tool"]:
                    return False

                # 角色特定验证
                if role == "tool":
                    if "tool_call_id" not in msg_data or not msg_data["tool_call_id"]:
                        return False
                    if "content" not in msg_data:
                        return False

                # 工具调用格式验证
                if "tool_calls" in msg_data and msg_data["tool_calls"]:
                    tool_calls = msg_data["tool_calls"]
                    if not isinstance(tool_calls, list):
                        return False

                    for tc in tool_calls:
                        if not isinstance(tc, dict):
                            return False
                        if "id" not in tc or "function" not in tc:
                            return False
                        if (
                            "name" not in tc["function"]
                            or "arguments" not in tc["function"]
                        ):
                            return False

                        # 验证arguments是否为有效JSON
                        try:
                            json.loads(tc["function"]["arguments"])
                        except json.JSONDecodeError:
                            return False

            return True
        except Exception:
            return False

    def add_user_message_from_request(self, message: str) -> None:
        """从请求中添加用户消息"""
        self.add_user_message(message)

    def get_openai_messages_for_llm(self) -> List[Dict[str, Any]]:
        """获取用于LLM调用的OpenAI格式消息"""
        return self.to_openai_format()
