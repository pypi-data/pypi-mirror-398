"""
适配器模块 - 适配不同AI Agent
"""

from ai_project_os_mcp.adapters.claude import ClaudeAdapter
from ai_project_os_mcp.adapters.cursor import CursorAdapter
from ai_project_os_mcp.adapters.trae import TraeAdapter

__all__ = [
    "ClaudeAdapter",
    "CursorAdapter",
    "TraeAdapter"
]
