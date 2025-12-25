"""MCP server initialization."""
from fastmcp import FastMCP
from .conf import config
from ..middleware.tool_middeware import ToolMiddleware


# Create MCP server instance
mcp_server = FastMCP(
    name=config.name,
    version=config.version,
    instructions=config.instructions,
)


mcp_server.add_middleware(ToolMiddleware())
