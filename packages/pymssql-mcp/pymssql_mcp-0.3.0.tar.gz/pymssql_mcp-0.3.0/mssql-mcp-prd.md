# MS SQL Server MCP Server - Product Requirements Document

## Overview

This document defines the requirements for `mssql-mcp`, an MCP (Model Context Protocol) server that enables AI assistants to interact with Microsoft SQL Server databases. The server is modeled after the proven architecture of `u2-mcp` but tailored for relational database semantics.

## Goals

1. **Enable AI-database interaction** - Allow Claude and other AI assistants to query, read, write, and manage SQL Server data
2. **Safety first** - Prevent destructive operations through configurable blocklists, read-only mode, and query limits
3. **Production ready** - Support multiple transport modes (stdio, HTTP, streamable HTTP with OAuth)
4. **Developer friendly** - Simple configuration via environment variables, clear error messages

## Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.10+ | Consistency with u2-mcp, broad ecosystem |
| MCP Framework | FastMCP | Proven in u2-mcp, clean decorator-based API |
| Database Driver | pymssql | Pure Python, no ODBC required, good for Docker/Linux |
| Settings | pydantic-settings | Type-safe config, env var binding |
| Testing | pytest | Standard, good async support |
| Linting | ruff | Fast, comprehensive |

## MCP Tools

### Query Tools

#### `execute_query`
Execute a read-only SQL query and return results.

**Parameters:**
- `query` (str, required): SQL SELECT statement
- `max_rows` (int, optional): Override default row limit

**Safety:**
- Only SELECT statements allowed
- Query timeout enforced
- Row limit applied
- Blocked patterns checked

**Returns:** JSON with columns and rows

---

#### `validate_query`
Check if a query is safe to execute without running it.

**Parameters:**
- `query` (str, required): SQL statement to validate

**Returns:** Validation result with any warnings

---

### Schema Discovery Tools

#### `list_tables`
List all tables and views in the database.

**Parameters:**
- `schema` (str, optional): Filter by schema (default: all schemas)
- `include_views` (bool, optional): Include views (default: true)
- `pattern` (str, optional): Filter by name pattern (SQL LIKE syntax)

**Returns:** List of table/view names with schema and type

---

#### `describe_table`
Get detailed column information for a table.

**Parameters:**
- `table` (str, required): Table name (can include schema: `dbo.Users`)

**Returns:**
- Column names, types, nullability
- Primary key columns
- Foreign key relationships
- Indexes

---

### CRUD Tools

#### `read_rows`
Read rows from a table by primary key or filter.

**Parameters:**
- `table` (str, required): Table name
- `id` (any, optional): Primary key value (for single row)
- `ids` (list, optional): Multiple primary key values
- `filter` (str, optional): WHERE clause (parameterized)
- `columns` (list, optional): Columns to return (default: all)
- `max_rows` (int, optional): Row limit

**Returns:** Rows as JSON objects

---

#### `insert_row`
Insert a new row into a table.

**Parameters:**
- `table` (str, required): Table name
- `data` (dict, required): Column-value pairs

**Safety:** Blocked in read-only mode

**Returns:** Inserted row with generated keys (e.g., identity columns)

---

#### `update_row`
Update an existing row.

**Parameters:**
- `table` (str, required): Table name
- `id` (any, required): Primary key value
- `data` (dict, required): Column-value pairs to update

**Safety:** Blocked in read-only mode

**Returns:** Updated row

---

#### `delete_row`
Delete a row by primary key.

**Parameters:**
- `table` (str, required): Table name
- `id` (any, required): Primary key value

**Safety:** Blocked in read-only mode

**Returns:** Confirmation with deleted row count

---

### Stored Procedure Tools

#### `list_stored_procs`
List available stored procedures.

**Parameters:**
- `schema` (str, optional): Filter by schema
- `pattern` (str, optional): Name pattern filter

**Returns:** List of procedure names with schemas

---

#### `describe_stored_proc`
Get parameter information for a stored procedure.

**Parameters:**
- `procedure` (str, required): Procedure name

**Returns:** Parameter names, types, directions (in/out/inout)

---

#### `call_stored_proc`
Execute a stored procedure.

**Parameters:**
- `procedure` (str, required): Procedure name
- `params` (dict, optional): Input parameter values

**Safety:** Blocked in read-only mode (unless procedure is whitelisted)

**Returns:** Output parameters and result sets

---

### Export Tools

#### `export_to_json`
Export query results to a JSON file.

**Parameters:**
- `query` (str, required): SELECT query
- `filename` (str, required): Output filename

**Returns:** Path to created file, row count

---

#### `export_to_csv`
Export query results to a CSV file.

**Parameters:**
- `query` (str, required): SELECT query
- `filename` (str, required): Output filename
- `delimiter` (str, optional): Field delimiter (default: comma)

**Returns:** Path to created file, row count

---

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MSSQL_HOST` | Server hostname or IP | `localhost` |
| `MSSQL_USER` | SQL Server username | `sa` |
| `MSSQL_PASSWORD` | Password | `MyP@ssw0rd` |
| `MSSQL_DATABASE` | Database name | `AdventureWorks` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MSSQL_PORT` | `1433` | Server port |
| `MSSQL_TIMEOUT` | `30` | Connection timeout (seconds) |
| `MSSQL_READ_ONLY` | `false` | Block all write operations |
| `MSSQL_MAX_ROWS` | `1000` | Default row limit for queries |
| `MSSQL_QUERY_TIMEOUT` | `60` | Query execution timeout (seconds) |
| `MSSQL_BLOCKED_COMMANDS` | (see below) | Comma-separated blocked SQL patterns |
| `MSSQL_ALLOWED_SCHEMAS` | (all) | Restrict to specific schemas |

### Default Blocked Commands

```
DROP,TRUNCATE,ALTER,CREATE,GRANT,REVOKE,DENY,BACKUP,RESTORE,KILL,SHUTDOWN,RECONFIGURE
```

## Safety Architecture

### Query Validation
1. Parse SQL to identify statement type (SELECT, INSERT, UPDATE, DELETE, etc.)
2. Check against blocked commands list
3. Verify read-only mode compliance
4. Apply row limits to unbounded queries

### Parameterized Queries
All user-provided values in CRUD operations use parameterized queries to prevent SQL injection.

### Schema Restrictions
Optional `MSSQL_ALLOWED_SCHEMAS` limits operations to specific schemas.

### Audit Logging
All tool invocations logged with:
- Timestamp
- Tool name
- Parameters (with sensitive data masked)
- Result status
- Execution time

## Transport Modes

### Stdio (Default)
Direct process communication for local Claude Code usage.

### HTTP/SSE
HTTP server with Server-Sent Events for centralized deployment.

### Streamable HTTP with OAuth
For Claude.ai remote MCP connections with authentication.

## Project Structure

```
mssql-mcp/
├── src/mssql_mcp/
│   ├── __init__.py
│   ├── server.py           # FastMCP entry point
│   ├── config.py           # Pydantic settings
│   ├── connection.py       # pymssql connection manager
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── query.py        # execute_query, validate_query
│   │   ├── tables.py       # list_tables, describe_table
│   │   ├── crud.py         # read/insert/update/delete rows
│   │   ├── stored_procs.py # Stored procedure tools
│   │   └── export.py       # export_to_json, export_to_csv
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── safety.py       # SQL validation, blocklist
│   │   └── audit.py        # Audit logging
│   └── resources/
│       ├── __init__.py
│       └── syntax_help.py  # T-SQL syntax reference
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Fixtures
│   ├── test_connection.py
│   ├── test_query.py
│   ├── test_crud.py
│   └── integration/        # Requires actual SQL Server
├── pyproject.toml
├── README.md
├── CLAUDE.md
└── .env.sample
```

## Implementation Notes

### Patterns from U2 MCP to Reuse
- FastMCP server initialization (server.py)
- Pydantic BaseSettings pattern (config.py)
- Audit logging approach (utils/audit.py)
- Tool registration with decorators
- Error handling and response formatting

### Key Differences from U2 MCP
- No dynamic arrays (relational data is flat)
- No multivalue/subvalue handling
- Standard SQL instead of RetrieVe/UniQuery
- INFORMATION_SCHEMA for metadata instead of VOC/dictionaries
- pymssql instead of uopy

### pymssql Usage Pattern

```python
import pymssql

# Connection
conn = pymssql.connect(
    server=host,
    user=user,
    password=password,
    database=database,
    port=port,
    timeout=timeout
)

# Query execution
cursor = conn.cursor(as_dict=True)  # Returns rows as dicts
cursor.execute("SELECT * FROM Users WHERE id = %s", (user_id,))
rows = cursor.fetchall()

# Stored procedure
cursor.callproc('sp_GetUser', (user_id,))
```

## Future Considerations

These are not in scope for v1.0 but may be added later:
- Connection pooling for high-concurrency scenarios
- Azure SQL support (may need pyodbc)
- Transaction support across multiple operations
- Bulk insert/update operations
- Query plan analysis tools
