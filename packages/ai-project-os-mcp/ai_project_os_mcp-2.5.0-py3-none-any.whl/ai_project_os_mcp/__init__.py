"""
AI Project OS MCP SDK

工程级AI行为控制协议SDK，用于将AI自动编程约束进真实软件工程流程。
"""

from ai_project_os_mcp.server import MCPServer
from ai_project_os_mcp import tools
from ai_project_os_mcp import core
from ai_project_os_mcp import adapters

__version__ = "2.5.0"
__author__ = "AI Project OS"
__license__ = "MIT"

__all__ = [
    "MCPServer",
    "tools",
    "core",
    "adapters",
]
