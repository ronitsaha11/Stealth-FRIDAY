"""
Core MCP Server — Entry Point
Run with: python server.py
"""

from mcp.server.fastmcp import FastMCP
from core.tools import register_all_tools
from core.prompts import register_all_prompts
from core.resources import register_all_resources
from core.config import config

# Create the MCP server instance
mcp = FastMCP(
    name=config.SERVER_NAME,
    instructions=(
        "You are a highly capable AI assistant with planning ability.\n"
        "If a task requires multiple steps, break it into a sequence of tool calls and execute them in order.\n"
        "Always prioritize action over explanation."
    ),
)

# Register tools, prompts, and resources
register_all_tools(mcp)
register_all_prompts(mcp)
register_all_resources(mcp)

def main():
    mcp.run(transport='sse')

if __name__ == "__main__":
    main()