"""
Configuration management module for the MCP Coordinator.

This module provides data models and validation logic for application configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LLMConfig:
    """Configuration for LLM client."""

    api_key: str
    base_url: str = "https://api.siliconflow.cn/v1"
    model: str = "moonshotai/Kimi-K2-Instruct"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: float = 30.0

    def __post_init__(self):
        """Validate LLM configuration after initialization."""
        self._validate()

    def _validate(self):
        """Validate LLM configuration parameters."""
        if not self.api_key:
            raise ValueError("LLM API key is required")

        if not self.base_url:
            raise ValueError("LLM base URL is required")

        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("LLM base URL must start with http:// or https://")

        if not self.model:
            raise ValueError("LLM model is required")

        if not isinstance(self.temperature, (int, float)) or not (
            0.0 <= self.temperature <= 2.0
        ):
            raise ValueError("Temperature must be a number between 0.0 and 2.0")

        if self.max_tokens is not None and (
            not isinstance(self.max_tokens, int) or self.max_tokens <= 0
        ):
            raise ValueError("max_tokens must be a positive integer or None")

        if not isinstance(self.timeout, (int, float)) or self.timeout <= 0:
            raise ValueError("Timeout must be a positive number")


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""

    transport: str = None

    # For stdio transport
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None

    # For HTTP transport
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

    # Common settings
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0

    def __post_init__(self):
        """Validate MCP server configuration after initialization."""
        self._validate()

    def _validate(self):
        """Validate MCP server configuration parameters."""
        if self.transport not in ["stdio", "streamable_http"]:
            raise ValueError(f"Unsupported transport type: {self.transport}")

        if self.transport == "stdio":
            if not self.command:
                raise ValueError("MCP server command is required for stdio transport")
        elif self.transport == "streamable_http":
            if not self.url:
                raise ValueError(
                    "MCP server URL is required for streamable_http transport"
                )

            if not self.url.startswith(("http://", "https://")):
                raise ValueError("MCP server URL must start with http:// or https://")

        if not isinstance(self.timeout, (int, float)) or self.timeout <= 0:
            raise ValueError("Timeout must be a positive number")

        if not isinstance(self.retry_attempts, int) or self.retry_attempts < 0:
            raise ValueError("Retry attempts must be a non-negative integer")

        if not isinstance(self.retry_delay, (int, float)) or self.retry_delay < 0:
            raise ValueError("Retry delay must be a non-negative number")


@dataclass
class Config:
    """Main application configuration."""

    llm: LLMConfig
    mcp_servers: Dict[str, MCPServerConfig] = field(default_factory=dict)

    def __post_init__(self):
        """Validate main configuration after initialization."""
        self._validate()

    def _validate(self):
        """Validate main configuration parameters."""
        if not isinstance(self.llm, LLMConfig):
            raise ValueError("LLM configuration must be an LLMConfig instance")

        if not isinstance(self.mcp_servers, dict):
            raise ValueError("MCP servers must be a dictionary")

        # Validate each MCP server configuration
        for server_name, server_config in self.mcp_servers.items():
            if not isinstance(server_config, MCPServerConfig):
                raise ValueError(
                    f"MCP server '{server_name}' configuration must be an MCPServerConfig instance"
                )
