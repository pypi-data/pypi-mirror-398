"""MCP resources for SQL Server."""

# Import resource modules to register them with the FastMCP instance
from . import knowledge, syntax_help

__all__ = ["knowledge", "syntax_help"]
