# Configuration Reference

All configuration is done via environment variables. These can be set in your shell, in the Claude Desktop config, or in a `.env` file.

## Required Settings

These must be set for the server to connect:

| Variable | Description | Example |
|----------|-------------|---------|
| `MSSQL_HOST` | SQL Server hostname or IP | `server.example.com` |
| `MSSQL_USER` | Username for authentication | `myuser` |
| `MSSQL_PASSWORD` | Password for authentication | `mypassword` |
| `MSSQL_DATABASE` | Database name to connect to | `SalesDB` |

## Connection Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MSSQL_PORT` | SQL Server port | `1433` |
| `MSSQL_TIMEOUT` | Connection timeout in seconds | `30` |

## Safety Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MSSQL_READ_ONLY` | Disable all write operations (INSERT, UPDATE, DELETE) | `false` |
| `MSSQL_MAX_ROWS` | Maximum rows returned by queries | `1000` |
| `MSSQL_QUERY_TIMEOUT` | Maximum seconds for a query to execute | `60` |
| `MSSQL_BLOCKED_COMMANDS` | Comma-separated SQL commands to block | `DROP,TRUNCATE,ALTER,CREATE,GRANT,REVOKE,DENY,BACKUP,RESTORE,KILL,SHUTDOWN,RECONFIGURE` |
| `MSSQL_ALLOWED_SCHEMAS` | Comma-separated list of allowed schemas (empty = all) | (empty) |
| `MSSQL_BLOCKED_DATABASES` | Comma-separated list of blocked database names | (empty) |

## HTTP Server Settings

Used when running in HTTP/SSE mode (`--http` flag) or Streamable HTTP mode (`--streamable-http` flag):

| Variable | Description | Default |
|----------|-------------|---------|
| `MSSQL_HTTP_HOST` | Host to bind HTTP server to | `127.0.0.1` |
| `MSSQL_HTTP_PORT` | Port for HTTP server | `8080` |
| `MSSQL_HTTP_CORS_ORIGINS` | Allowed CORS origins (comma-separated or `*`) | `*` |

## OAuth / Claude.ai Integration Settings

Used when deploying as a Claude.ai Custom Connector with OAuth authentication. See [OAuth Guide](oauth.md) for detailed setup instructions.

| Variable | Description | Default |
|----------|-------------|---------|
| `MSSQL_AUTH_ENABLED` | Enable OAuth authentication | `false` |
| `MSSQL_AUTH_ISSUER_URL` | Public URL of this server (e.g., `https://pymssql-mcp.example.com`) | None |
| `MSSQL_IDP_PROVIDER` | Identity provider type: `duo`, `auth0`, or `oidc` | `duo` |
| `MSSQL_IDP_DISCOVERY_URL` | OIDC discovery URL (`.well-known/openid-configuration`) | None |
| `MSSQL_IDP_CLIENT_ID` | Client ID from your identity provider | None |
| `MSSQL_IDP_CLIENT_SECRET` | Client secret from your identity provider | None |
| `MSSQL_IDP_SCOPES` | Scopes to request from IdP (space-separated) | `openid profile email groups` |
| `MSSQL_DUO_API_HOST` | Duo API hostname (alternative to discovery URL) | None |
| `MSSQL_TOKEN_EXPIRY_SECONDS` | Access token lifetime in seconds | `3600` |
| `MSSQL_REFRESH_TOKEN_EXPIRY_SECONDS` | Refresh token lifetime in seconds | `2592000` (30 days) |

## Audit Logging Settings

Enable audit logging to capture all MCP tool calls for analysis and debugging.

| Variable | Description | Default |
|----------|-------------|---------|
| `MSSQL_AUDIT_ENABLED` | Enable audit logging | `false` |
| `MSSQL_AUDIT_LOG_FILE` | Path for audit log file | `mssql_mcp_audit.log` |

### Audit Log Format

Audit logs are written as JSONL (JSON Lines) format. Each line is a JSON object with:

| Field | Description |
|-------|-------------|
| `event` | Event type: `session_start`, `tool_call`, `session_end`, `error` |
| `timestamp` | ISO 8601 format timestamp |
| `session_id` | Unique session identifier |
| `tool` | Tool name (for `tool_call` events) |
| `parameters` | Tool parameters (sensitive values redacted) |
| `result` | Tool result |
| `duration_ms` | Execution time in milliseconds |
| `status` | `success` or `error` |
| `error` | Error message (if status is `error`) |

## Connection Watchdog Settings

The watchdog monitors database connection health and automatically recovers from hung connections.

| Variable | Description | Default |
|----------|-------------|---------|
| `MSSQL_WATCHDOG_ENABLED` | Enable connection health monitoring | `true` |
| `MSSQL_WATCHDOG_INTERVAL` | Watchdog check interval in seconds | `30` |
| `MSSQL_WATCHDOG_TIMEOUT` | Timeout for each health check in seconds | `10` |
| `MSSQL_WATCHDOG_MAX_FAILURES` | Consecutive failures before forcing reconnect | `3` |

## Configuration Examples

### Basic Setup

```bash
export MSSQL_HOST=sqlserver.example.com
export MSSQL_USER=appuser
export MSSQL_PASSWORD=secretpassword
export MSSQL_DATABASE=SalesDB
```

### Read-Only with Extended Blocking

```bash
export MSSQL_HOST=sqlserver.example.com
export MSSQL_USER=readonly_user
export MSSQL_PASSWORD=password
export MSSQL_DATABASE=ProductionDB
export MSSQL_READ_ONLY=true
export MSSQL_BLOCKED_COMMANDS=DROP,TRUNCATE,ALTER,CREATE,GRANT,REVOKE,DENY,BACKUP,RESTORE,KILL,SHUTDOWN,RECONFIGURE,EXEC,EXECUTE
export MSSQL_MAX_ROWS=500
```

### Restricted Schema Access

```bash
export MSSQL_HOST=sqlserver.example.com
export MSSQL_USER=sales_user
export MSSQL_PASSWORD=password
export MSSQL_DATABASE=CompanyDB
export MSSQL_ALLOWED_SCHEMAS=dbo,Sales,Reporting
export MSSQL_BLOCKED_DATABASES=master,msdb,tempdb,model
```

### Azure SQL Database

```bash
export MSSQL_HOST=your-server.database.windows.net
export MSSQL_USER=admin@your-server
export MSSQL_PASSWORD=password
export MSSQL_DATABASE=your-database
export MSSQL_PORT=1433
```

### HTTP Server Deployment

```bash
export MSSQL_HOST=sqlserver.example.com
export MSSQL_USER=api_user
export MSSQL_PASSWORD=password
export MSSQL_DATABASE=API_DB
export MSSQL_HTTP_HOST=0.0.0.0
export MSSQL_HTTP_PORT=3000
export MSSQL_HTTP_CORS_ORIGINS=https://app.example.com,https://admin.example.com
export MSSQL_READ_ONLY=true
```

### Claude.ai Integration with Duo OAuth

```bash
# Database Connection
export MSSQL_HOST=sqlserver.example.com
export MSSQL_USER=mcp_user
export MSSQL_PASSWORD=password
export MSSQL_DATABASE=ProductionDB

# OAuth Configuration
export MSSQL_AUTH_ENABLED=true
export MSSQL_AUTH_ISSUER_URL=https://pymssql-mcp.example.com

# Duo Identity Provider
export MSSQL_IDP_PROVIDER=duo
export MSSQL_IDP_DISCOVERY_URL=https://sso-abc123.sso.duosecurity.com/oidc/YOUR_CLIENT_ID/.well-known/openid-configuration
export MSSQL_IDP_CLIENT_ID=YOUR_CLIENT_ID
export MSSQL_IDP_CLIENT_SECRET=YOUR_CLIENT_SECRET
export MSSQL_IDP_SCOPES="openid profile email groups"

# CORS for Claude.ai
export MSSQL_HTTP_CORS_ORIGINS=https://claude.ai,https://*.claude.ai
```

### With Audit Logging

```bash
export MSSQL_HOST=sqlserver.example.com
export MSSQL_USER=appuser
export MSSQL_PASSWORD=password
export MSSQL_DATABASE=SalesDB
export MSSQL_AUDIT_ENABLED=true
export MSSQL_AUDIT_LOG_FILE=/var/log/pymssql-mcp/audit.log
```

## Claude Desktop Config

Full example with all common options:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "pymssql-mcp",
      "env": {
        "MSSQL_HOST": "sqlserver.example.com",
        "MSSQL_USER": "myuser",
        "MSSQL_PASSWORD": "mypassword",
        "MSSQL_DATABASE": "SalesDB",
        "MSSQL_PORT": "1433",
        "MSSQL_TIMEOUT": "30",
        "MSSQL_READ_ONLY": "true",
        "MSSQL_MAX_ROWS": "500",
        "MSSQL_QUERY_TIMEOUT": "60",
        "MSSQL_BLOCKED_COMMANDS": "DROP,TRUNCATE,ALTER,CREATE"
      }
    }
  }
}
```

## Environment File (.env)

For local development or server deployment, create a `.env` file:

```bash
# Database Connection
MSSQL_HOST=localhost
MSSQL_USER=devuser
MSSQL_PASSWORD=devpassword
MSSQL_DATABASE=DevDB

# Safety
MSSQL_READ_ONLY=true
MSSQL_MAX_ROWS=1000

# Watchdog
MSSQL_WATCHDOG_ENABLED=true
MSSQL_WATCHDOG_INTERVAL=30
```

Note: The `.env` file is loaded automatically by pydantic-settings when running from the command line, but Claude Desktop requires explicit environment variables in the config.

## Blocked Commands

The default blocked commands prevent destructive operations:

| Command | Why It's Blocked |
|---------|------------------|
| `DROP` | Can delete tables, databases, procedures |
| `TRUNCATE` | Deletes all data from tables |
| `ALTER` | Can modify schema |
| `CREATE` | Can create new objects |
| `GRANT` | Can modify permissions |
| `REVOKE` | Can revoke permissions |
| `DENY` | Can deny permissions |
| `BACKUP` | Can access file system |
| `RESTORE` | Can overwrite databases |
| `KILL` | Can terminate connections |
| `SHUTDOWN` | Can stop SQL Server |
| `RECONFIGURE` | Can change server settings |

To allow a blocked command, remove it from the list:
```bash
# Allow CREATE but block everything else
export MSSQL_BLOCKED_COMMANDS=DROP,TRUNCATE,ALTER,GRANT,REVOKE,DENY,BACKUP,RESTORE,KILL,SHUTDOWN,RECONFIGURE
```

## Schema Restrictions

Limit which schemas Claude can access:

```bash
# Only allow access to dbo and Sales schemas
export MSSQL_ALLOWED_SCHEMAS=dbo,Sales
```

When set, any query referencing other schemas will be rejected.

## Database Restrictions

Hide entire databases from Claude:

```bash
# Block access to system and sensitive databases
export MSSQL_BLOCKED_DATABASES=master,msdb,tempdb,model,SecretDB
```

Blocked databases won't appear in `list_databases` and can't be switched to.
