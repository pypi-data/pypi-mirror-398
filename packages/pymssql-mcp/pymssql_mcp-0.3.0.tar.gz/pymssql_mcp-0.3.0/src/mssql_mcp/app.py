"""FastMCP application instance for mssql-mcp.

This module exists to avoid circular import issues when running
the server with `python -m mssql_mcp.server`. By having the mcp
instance in a separate module, all tools import from the same
instance regardless of how the server is started.
"""

from mcp.server.fastmcp import FastMCP

# Create FastMCP server instance
mcp = FastMCP("MS SQL MCP Server")
