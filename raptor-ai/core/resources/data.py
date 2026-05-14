"""
Data resources — expose static content or dynamic data via MCP resources.
"""


def register(mcp):

    @mcp.resource("core://info")
    def server_info() -> str:
        """Returns basic info about this MCP server."""
        return (
            "Core MCP Server\n"
            "A highly capable AI assistant.\n"
            "Built with FastMCP."
        )
