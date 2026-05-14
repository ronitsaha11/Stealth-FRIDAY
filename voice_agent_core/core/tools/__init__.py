"""
Tool registry — imports and registers all tool modules with the MCP server.
Add new tool modules here as you build them.
"""

from core.tools import automation, email, system, time_tools, utils, web
from core.tools import os as os_tool


def register_all_tools(mcp):
    """Register all tool groups onto the MCP server instance."""
    web.register(mcp)
    system.register(mcp)
    utils.register(mcp)
    os_tool.register(mcp)
    time_tools.register(mcp)
    automation.register(mcp)
    email.register(mcp)
