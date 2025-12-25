"""OAuth authentication module for mssql-mcp.

This module provides OAuth 2.0 authentication support for Claude.ai Integrations,
implementing the MCP SDK's OAuthAuthorizationServerProvider protocol with support
for external identity providers (Duo, Auth0, generic OIDC).
"""

from .provider import MSSQLOAuthProvider
from .storage import InMemoryAuthStorage

__all__ = ["MSSQLOAuthProvider", "InMemoryAuthStorage"]
