# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in mssql-mcp, please report it responsibly:

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. Email the maintainers directly with details of the vulnerability
3. Include steps to reproduce the issue
4. Allow reasonable time for a fix before public disclosure

## Security Features

### Credential Protection

- Database credentials are loaded from environment variables, never hardcoded
- Credentials are never logged or exposed in error messages
- The `MSSQL_PASSWORD` field is treated as sensitive data

### Command Blocking

Dangerous SQL commands are blocked by default:

- `DROP` - Prevents dropping tables, databases, etc.
- `TRUNCATE` - Prevents data truncation
- `ALTER` - Prevents schema modifications
- `CREATE` - Prevents object creation
- `SHUTDOWN` - Prevents server shutdown
- `KILL` - Prevents process termination

Configure additional blocked commands via `MSSQL_BLOCKED_COMMANDS`:

```bash
export MSSQL_BLOCKED_COMMANDS="DROP,TRUNCATE,ALTER,CREATE,SHUTDOWN,KILL,EXEC,xp_"
```

### Read-Only Mode

Enable read-only mode to prevent all write operations:

```bash
export MSSQL_READ_ONLY=true
```

This restricts:
- `execute_query` to SELECT statements only
- `insert_row`, `update_row`, `delete_row` operations
- Any SQL command that modifies data

### Query Validation

The `execute_query` tool validates all queries:
- Only SELECT statements are allowed
- Blocked commands are rejected
- Row limits are enforced automatically

### Result Limiting

Query results are limited by `MSSQL_MAX_ROWS` (default: 1000) to prevent accidental large data exports.

### Database Access Control

Restrict access to specific databases using `MSSQL_BLOCKED_DATABASES`:

```bash
export MSSQL_BLOCKED_DATABASES="master,msdb,tempdb,model"
```

### CORS Configuration (HTTP Mode)

When running in HTTP mode, configure CORS origins to restrict access:

```bash
export MSSQL_HTTP_CORS_ORIGINS="https://trusted-app.example.com"
```

## Best Practices

1. **Use read-only mode** for exploration and development
2. **Restrict blocked commands** based on your security requirements
3. **Use dedicated service accounts** with minimal SQL Server permissions
4. **Grant only db_datareader** role for read-only access
5. **Store credentials securely** using secrets management (not plain text)
6. **Limit network access** to the HTTP server if deployed centrally
7. **Enable audit logging** to track all database operations

### SQL Server Account Setup

For maximum security, create a dedicated service account:

```sql
-- Create login
CREATE LOGIN [mcp_service] WITH PASSWORD = 'SecurePassword123!';

-- For each database you want to access:
USE YourDatabase;
CREATE USER [mcp_service] FOR LOGIN [mcp_service];
ALTER ROLE db_datareader ADD MEMBER [mcp_service];

-- For read-write access (if needed):
-- ALTER ROLE db_datawriter ADD MEMBER [mcp_service];
```

## Known Limitations

- The MCP protocol transmits data in plain text over stdio
- HTTP mode should use HTTPS in production (configure via reverse proxy)
- Audit logs are stored as plain text files
