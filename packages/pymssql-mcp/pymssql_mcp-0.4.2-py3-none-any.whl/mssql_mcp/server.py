"""Main MCP server entry point for mssql-mcp."""

import argparse
import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from mcp.server.fastmcp import FastMCP

from .app import mcp
from .config import MSSQLConfig
from .connection import ConnectionError, ConnectionManager
from .utils.audit import audit_tool_call, get_audit_logger, init_audit_logger
from .utils.watchdog import get_watchdog, init_watchdog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Type variable for generic function wrapping
F = TypeVar("F", bound=Callable[..., Any])

# Global connection manager (initialized on first connect)
_connection_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get or create the global connection manager.

    Returns:
        ConnectionManager instance configured from environment variables
    """
    global _connection_manager
    if _connection_manager is None:
        config = MSSQLConfig()
        _connection_manager = ConnectionManager(config)
    return _connection_manager


def reset_connection_manager() -> None:
    """Reset the global connection manager (useful for testing)."""
    global _connection_manager
    if _connection_manager is not None:
        _connection_manager.disconnect_all()
    _connection_manager = None


def _init_audit_logging(config: MSSQLConfig) -> None:
    """Initialize audit logging if enabled.

    Args:
        config: MSSQLConfig instance with audit settings
    """
    if config.audit_enabled:
        init_audit_logger(
            log_file=config.audit_log_file,
            include_results=True,
            max_result_size=10000,
        )
        logger.info(f"Audit logging enabled, writing to {config.audit_log_file}")


def _init_watchdog(config: MSSQLConfig) -> None:
    """Initialize the connection watchdog if enabled.

    Args:
        config: MSSQLConfig instance with watchdog settings
    """
    if not config.watchdog_enabled:
        logger.info("Connection watchdog disabled")
        return

    manager = get_connection_manager()

    def health_check() -> bool:
        return manager.health_check()

    def force_disconnect() -> None:
        manager.force_disconnect()

    init_watchdog(config, health_check, force_disconnect)
    logger.info(
        f"Connection watchdog initialized (interval={config.watchdog_interval}s, "
        f"timeout={config.watchdog_timeout}s, max_failures={config.watchdog_max_failures})"
    )


def _wrap_tools_with_audit(mcp_instance: FastMCP) -> None:
    """Wrap all registered tools with audit logging.

    Args:
        mcp_instance: The FastMCP instance with registered tools
    """
    audit_logger = get_audit_logger()
    if not audit_logger:
        return

    # Start a new audit session
    audit_logger.start_session()

    # Wrap each tool's function with audit logging
    for tool_name, tool in mcp_instance._tool_manager._tools.items():
        original_fn = tool.fn

        @functools.wraps(original_fn)
        def wrapped_fn(
            *args: Any,
            _original_fn: Callable[..., Any] = original_fn,
            _tool_name: str = tool_name,
            **kwargs: Any,
        ) -> Any:
            start_time = time.time()
            error_msg = None
            result = None

            try:
                result = _original_fn(*args, **kwargs)
                return result
            except Exception as e:
                error_msg = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                audit_tool_call(
                    tool_name=_tool_name,
                    parameters=kwargs,
                    result=result,
                    error=error_msg,
                    duration_ms=duration_ms,
                )

        tool.fn = wrapped_fn


# =============================================================================
# Connection Management Tools
# =============================================================================


@mcp.tool()
def connect() -> dict[str, Any]:
    """Establish connection to the SQL Server database.

    Uses configuration from environment variables:
    - MSSQL_HOST: Server hostname or IP
    - MSSQL_USER: Username
    - MSSQL_PASSWORD: Password
    - MSSQL_DATABASE: Database name
    - MSSQL_PORT: Port (default: 1433)

    Returns:
        Connection status and details including host, database, and timestamp.
    """
    try:
        manager = get_connection_manager()
        info = manager.connect()

        return {
            "status": "connected",
            "host": info.host,
            "database": info.database,
            "connected_at": info.connected_at.isoformat(),
        }
    except ConnectionError as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error during connect: {e}")
        return {"status": "error", "error": f"Unexpected error: {e}"}


@mcp.tool()
def disconnect() -> dict[str, Any]:
    """Close all connections to the SQL Server database.

    Returns:
        Disconnection status and count of closed connections.
    """
    try:
        manager = get_connection_manager()
        closed = manager.disconnect_all()
        return {
            "status": "disconnected",
            "connections_closed": closed,
        }
    except Exception as e:
        logger.error(f"Error during disconnect: {e}")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def list_connections() -> dict[str, Any]:
    """List all active database connections.

    Returns:
        List of active connections with their details (name, host, database,
        connection time, and active status).
    """
    try:
        manager = get_connection_manager()
        connections = manager.list_connections()
        return {
            "connections": [
                {
                    "name": info.name,
                    "host": info.host,
                    "database": info.database,
                    "connected_at": info.connected_at.isoformat(),
                    "is_active": info.is_active,
                }
                for info in connections.values()
            ]
        }
    except Exception as e:
        logger.error(f"Error listing connections: {e}")
        return {"status": "error", "error": str(e)}


# =============================================================================
# Import and register tools from submodules
# =============================================================================

# These imports register the tools and resources with the mcp instance
from .resources import (  # noqa: E402
    examples,  # noqa: F401
    syntax_help,  # noqa: F401
)
from .resources import knowledge as knowledge_resource  # noqa: E402, F401
from .tools import (  # noqa: E402, F401
    crud,
    databases,
    export,
    knowledge,
    query,
    stored_procs,
    tables,
    transaction,
)


def run_sse_server() -> None:
    """Run the MCP server in HTTP/SSE mode for centralized deployment."""
    from contextlib import asynccontextmanager

    import uvicorn
    from starlette.middleware.cors import CORSMiddleware

    config = MSSQLConfig()

    # Initialize audit logging if enabled
    _init_audit_logging(config)
    _wrap_tools_with_audit(mcp)

    # Initialize watchdog
    _init_watchdog(config)

    # Get the SSE app from FastMCP
    app = mcp.sse_app()

    # Add lifespan for watchdog
    @asynccontextmanager
    async def lifespan(app):  # type: ignore
        # Start watchdog on startup
        watchdog = get_watchdog()
        if watchdog:
            await watchdog.start()
        yield
        # Stop watchdog on shutdown
        if watchdog:
            await watchdog.stop()

    app.router.lifespan_context = lifespan

    # Add CORS middleware for browser clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.http_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info(f"Starting MS SQL MCP Server (HTTP/SSE) on {config.http_host}:{config.http_port}")
    logger.info(f"SSE endpoint: http://{config.http_host}:{config.http_port}/sse")
    logger.info(f"CORS origins: {config.http_cors_origins}")
    if config.watchdog_enabled:
        logger.info("Connection watchdog enabled")

    uvicorn.run(
        app,
        host=config.http_host,
        port=config.http_port,
        log_level="info",
    )


def run_streamable_http_server() -> None:
    """Run the MCP server in Streamable HTTP mode for Claude.ai Integrations.

    This mode supports:
    - Streamable HTTP transport (MCP 2025-06-18 spec)
    - OAuth authentication with external IdP (Duo, Auth0, OIDC)
    - Dynamic Client Registration (DCR) for Claude.ai
    """
    from contextlib import asynccontextmanager

    import uvicorn
    from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions
    from mcp.server.fastmcp import FastMCP as FastMCPAuth
    from starlette.middleware.cors import CORSMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.routing import Route

    from .auth.callback import handle_oauth_callback
    from .auth.idp import create_idp_adapter
    from .auth.provider import MSSQLOAuthProvider

    config = MSSQLConfig()

    # Initialize audit logging if enabled
    _init_audit_logging(config)

    # Initialize watchdog
    _init_watchdog(config)

    # Create OAuth provider if auth is enabled
    auth_provider = None
    auth_settings = None

    if config.auth_enabled:
        if not config.auth_issuer_url:
            raise ValueError("MSSQL_AUTH_ISSUER_URL is required when auth is enabled")
        if not config.idp_discovery_url and not config.duo_api_host:
            raise ValueError(
                "MSSQL_IDP_DISCOVERY_URL (or MSSQL_DUO_API_HOST for Duo) "
                "is required when auth is enabled"
            )

        # Create IdP adapter
        idp_adapter = create_idp_adapter(config)

        # Create OAuth provider
        auth_provider = MSSQLOAuthProvider(
            idp_adapter=idp_adapter,
            issuer_url=config.auth_issuer_url,
            token_expiry=config.token_expiry_seconds,
            refresh_token_expiry=config.refresh_token_expiry_seconds,
        )

        # Configure auth settings for FastMCP
        auth_settings = AuthSettings(
            issuer_url=config.auth_issuer_url,
            resource_server_url=config.auth_issuer_url,
            client_registration_options=ClientRegistrationOptions(
                enabled=True,
                valid_scopes=["mcp:tools", "mcp:resources"],
                default_scopes=["mcp:tools", "mcp:resources"],
            ),
            revocation_options=RevocationOptions(enabled=True),
        )

        logger.info(f"OAuth enabled with {config.idp_provider} IdP")

    # Create new FastMCP instance with auth configured
    mcp_streamable = FastMCPAuth(
        name="MS SQL MCP Server",
        host=config.http_host,
        port=config.http_port,
        streamable_http_path="/",
        auth_server_provider=auth_provider,
        auth=auth_settings,
    )

    # Copy tools from the original mcp instance
    mcp_streamable._tool_manager._tools.update(mcp._tool_manager._tools)

    # Copy resources
    mcp_streamable._resource_manager._resources.update(mcp._resource_manager._resources)

    # Copy prompts if any
    mcp_streamable._prompt_manager._prompts.update(mcp._prompt_manager._prompts)

    # Wrap tools with audit logging if enabled
    _wrap_tools_with_audit(mcp_streamable)

    # Get the Streamable HTTP app
    app = mcp_streamable.streamable_http_app()

    # Add lifespan for watchdog
    @asynccontextmanager
    async def lifespan(app):  # type: ignore
        # Start watchdog on startup
        watchdog = get_watchdog()
        if watchdog:
            await watchdog.start()
        yield
        # Stop watchdog on shutdown
        if watchdog:
            await watchdog.stop()

    app.router.lifespan_context = lifespan

    # Add custom OAuth callback route for external IdP
    if auth_provider:
        # This route handles the callback from the external IdP (Duo, Auth0, etc.)
        # after the user authenticates
        async def oauth_callback_handler(request: Request) -> Response:
            return await handle_oauth_callback(request, auth_provider)

        # Insert the callback route
        app.routes.append(Route("/oauth/callback", oauth_callback_handler, methods=["GET"]))

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.http_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info(
        f"Starting MS SQL MCP Server (Streamable HTTP) on {config.http_host}:{config.http_port}"
    )
    logger.info(f"MCP endpoint: http://{config.http_host}:{config.http_port}/")
    logger.info(f"CORS origins: {config.http_cors_origins}")
    if config.auth_enabled:
        logger.info("OAuth endpoints: /authorize, /token, /register, /.well-known/*")
        logger.info("OAuth callback: /oauth/callback")
    if config.watchdog_enabled:
        logger.info("Connection watchdog enabled")

    uvicorn.run(
        app,
        host=config.http_host,
        port=config.http_port,
        log_level="info",
    )


def main() -> None:
    """Entry point for the MCP server."""
    parser = argparse.ArgumentParser(
        description="MS SQL MCP Server - Connect AI assistants to SQL Server databases"
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run as HTTP/SSE server (legacy mode)",
    )
    parser.add_argument(
        "--streamable-http",
        action="store_true",
        help="Run as Streamable HTTP server for Claude.ai Integrations",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="HTTP server host (overrides MSSQL_HTTP_HOST env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="HTTP server port (overrides MSSQL_HTTP_PORT env var)",
    )

    args = parser.parse_args()

    # Override config with CLI args if provided
    if args.host:
        import os

        os.environ["MSSQL_HTTP_HOST"] = args.host
    if args.port:
        import os

        os.environ["MSSQL_HTTP_PORT"] = str(args.port)

    if args.streamable_http:
        run_streamable_http_server()
    elif args.http:
        run_sse_server()
    else:
        # Initialize audit logging for stdio mode
        config = MSSQLConfig()
        _init_audit_logging(config)
        _wrap_tools_with_audit(mcp)

        logger.info("Starting MS SQL MCP Server (stdio mode)")
        mcp.run()


if __name__ == "__main__":
    main()
