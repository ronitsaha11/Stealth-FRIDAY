"""
MCP Resources — expose static or dynamic data to the client.
"""

from core.resources import data


def register_all_resources(mcp):
    data.register(mcp)
