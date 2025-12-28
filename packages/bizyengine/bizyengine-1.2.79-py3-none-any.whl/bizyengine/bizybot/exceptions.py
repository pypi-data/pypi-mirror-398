"""
统一异常处理模块

定义了协调器系统中使用的所有自定义异常类型，
提供了错误处理的基础架构和优雅降级机制。
"""

from typing import Any, Dict, Optional


class CoordinatorError(Exception):
    """基础协调器异常

    所有协调器相关异常的基类，提供统一的错误处理接口。
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """将异常转换为字典格式，用于API响应"""
        result = {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }

        if self.cause:
            result["cause"] = str(self.cause)

        return result

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class LLMError(CoordinatorError):
    """LLM相关错误

    包括API调用失败、响应解析错误、模型不可用等。
    """

    pass


class LLMAPIError(LLMError):
    """LLM API调用错误"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.response_body = response_body

        if status_code:
            self.details["status_code"] = status_code
        if response_body:
            self.details["response_body"] = response_body


class LLMResponseError(LLMError):
    """LLM响应解析错误"""

    pass


class LLMTimeoutError(LLMError):
    """LLM请求超时错误"""

    pass


class MCPError(CoordinatorError):
    """MCP相关错误

    包括连接失败、协议错误、工具调用失败等。
    """

    pass


class MCPConnectionError(MCPError):
    """MCP连接错误"""

    def __init__(self, message: str, server_name: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.server_name = server_name

        if server_name:
            self.details["server_name"] = server_name


class MCPToolError(MCPError):
    """MCP工具调用错误"""

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        server_name: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.tool_name = tool_name
        self.server_name = server_name

        if tool_name:
            self.details["tool_name"] = tool_name
        if server_name:
            self.details["server_name"] = server_name


class ToolNotFoundError(MCPToolError):
    """工具未找到错误"""

    pass


class ToolExecutionError(MCPToolError):
    """工具执行错误"""

    pass


class ToolValidationError(MCPToolError):
    """工具参数验证错误"""

    pass


class ConfigurationError(CoordinatorError):
    """配置相关错误

    包括配置文件格式错误、必需参数缺失、环境变量错误等。
    """

    pass


class ConfigFileError(ConfigurationError):
    """配置文件错误"""

    pass


class ConfigValidationError(ConfigurationError):
    """配置验证错误"""

    pass


class ValidationError(CoordinatorError):
    """数据验证错误"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value

        if field:
            self.details["field"] = field
        if value is not None:
            self.details["value"] = str(value)
