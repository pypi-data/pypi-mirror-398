"""
MCP Coordinator - A lightweight AI application coordinator
"""

__version__ = "0.1.0"

from .config import Config, LLMConfig

# Import main modules to make them available
from .coordinator import Coordinator

__all__ = ["Coordinator", "Config", "LLMConfig"]
