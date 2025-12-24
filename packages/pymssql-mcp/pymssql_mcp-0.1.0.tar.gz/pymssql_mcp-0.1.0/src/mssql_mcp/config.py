"""Configuration management for mssql-mcp using pydantic-settings."""

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings


class MSSQLConfig(BaseSettings):
    """Configuration for MS SQL MCP Server, loaded from environment variables.

    Required environment variables:
        MSSQL_HOST: SQL Server hostname or IP address
        MSSQL_USER: Username for authentication
        MSSQL_PASSWORD: Password for authentication
        MSSQL_DATABASE: Database name to connect to

    Optional environment variables:
        MSSQL_PORT: Server port (default: 1433)
        MSSQL_TIMEOUT: Connection timeout in seconds
        MSSQL_READ_ONLY: Disable write operations
        MSSQL_MAX_ROWS: Maximum query results
        MSSQL_QUERY_TIMEOUT: Query execution timeout
        MSSQL_BLOCKED_COMMANDS: Comma-separated list of blocked SQL commands
    """

    # Required connection settings
    host: str = Field(
        ...,
        alias="MSSQL_HOST",
        description="SQL Server hostname or IP address",
    )
    user: str = Field(
        ...,
        alias="MSSQL_USER",
        description="Username for authentication",
    )
    password: str = Field(
        ...,
        alias="MSSQL_PASSWORD",
        description="Password for authentication",
    )
    database: str = Field(
        ...,
        alias="MSSQL_DATABASE",
        description="Database name to connect to",
    )

    # Optional connection settings
    port: int = Field(
        default=1433,
        alias="MSSQL_PORT",
        description="SQL Server port",
    )
    timeout: int = Field(
        default=30,
        alias="MSSQL_TIMEOUT",
        description="Connection timeout in seconds",
    )

    # Safety settings
    read_only: bool = Field(
        default=False,
        alias="MSSQL_READ_ONLY",
        description="Disable write operations (INSERT, UPDATE, DELETE)",
    )
    max_rows: int = Field(
        default=1000,
        alias="MSSQL_MAX_ROWS",
        description="Maximum rows returned by queries",
    )
    query_timeout: int = Field(
        default=60,
        alias="MSSQL_QUERY_TIMEOUT",
        description="Maximum seconds for a query to execute before timeout",
    )
    # Store as string to avoid pydantic-settings JSON parsing issues
    blocked_commands_str: str = Field(
        default="DROP,TRUNCATE,ALTER,CREATE,GRANT,REVOKE,DENY,BACKUP,RESTORE,KILL,SHUTDOWN,RECONFIGURE",
        alias="MSSQL_BLOCKED_COMMANDS",
        description="Comma-separated list of blocked SQL commands",
    )
    allowed_schemas_str: str = Field(
        default="",
        alias="MSSQL_ALLOWED_SCHEMAS",
        description="Comma-separated list of allowed schemas (empty = all)",
    )
    blocked_databases_str: str = Field(
        default="",
        alias="MSSQL_BLOCKED_DATABASES",
        description="Comma-separated list of blocked database names",
    )

    # HTTP Server settings (for centralized deployment)
    http_host: str = Field(
        default="127.0.0.1",
        alias="MSSQL_HTTP_HOST",
        description="Host to bind HTTP server to",
    )
    http_port: int = Field(
        default=8080,
        alias="MSSQL_HTTP_PORT",
        description="Port for HTTP server",
    )
    http_cors_origins_str: str = Field(
        default="*",
        alias="MSSQL_HTTP_CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins, or * for all",
    )

    # OAuth/Authentication settings (for Claude.ai Integrations)
    auth_enabled: bool = Field(
        default=False,
        alias="MSSQL_AUTH_ENABLED",
        description="Enable OAuth authentication for Streamable HTTP endpoint",
    )
    auth_issuer_url: str | None = Field(
        default=None,
        alias="MSSQL_AUTH_ISSUER_URL",
        description="OAuth issuer URL (this server's public URL)",
    )

    # Token settings
    token_expiry_seconds: int = Field(
        default=3600,
        alias="MSSQL_TOKEN_EXPIRY_SECONDS",
        description="Access token expiry time in seconds",
    )

    # Audit logging settings
    audit_enabled: bool = Field(
        default=False,
        alias="MSSQL_AUDIT_ENABLED",
        description="Enable audit logging of all MCP tool calls",
    )
    audit_log_file: str = Field(
        default="mssql_mcp_audit.log",
        alias="MSSQL_AUDIT_LOG_FILE",
        description="Path for audit log file",
    )

    @computed_field  # type: ignore[prop-decorator]  # pydantic pattern
    @property
    def blocked_commands(self) -> list[str]:
        """Parse comma-separated string into list of blocked commands."""
        return [cmd.strip().upper() for cmd in self.blocked_commands_str.split(",") if cmd.strip()]

    @computed_field  # type: ignore[prop-decorator]  # pydantic pattern
    @property
    def allowed_schemas(self) -> list[str]:
        """Parse comma-separated string into list of allowed schemas."""
        if not self.allowed_schemas_str.strip():
            return []
        return [schema.strip() for schema in self.allowed_schemas_str.split(",") if schema.strip()]

    @computed_field  # type: ignore[prop-decorator]  # pydantic pattern
    @property
    def blocked_databases(self) -> list[str]:
        """Parse comma-separated string into list of blocked database names."""
        if not self.blocked_databases_str.strip():
            return []
        return [db.strip().lower() for db in self.blocked_databases_str.split(",") if db.strip()]

    @computed_field  # type: ignore[prop-decorator]  # pydantic pattern
    @property
    def http_cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins into list."""
        origins = self.http_cors_origins_str.strip()
        if origins == "*":
            return ["*"]
        return [o.strip() for o in origins.split(",") if o.strip()]

    model_config = {
        "env_prefix": "",
        "case_sensitive": False,
        "populate_by_name": True,
    }
