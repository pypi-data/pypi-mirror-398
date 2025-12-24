# mssql-mcp

An MCP (Model Context Protocol) server for Microsoft SQL Server databases. Enables AI assistants like Claude to interact with SQL Server through a standardized protocol.

## Features

- **Query Execution**: Run SELECT queries with safety limits
- **Schema Discovery**: List tables, views, and column information
- **CRUD Operations**: Read, insert, update, and delete rows
- **Stored Procedures**: Execute stored procedures with parameters
- **Export**: Export query results to JSON or CSV
- **Safety Controls**: Command blocklist, read-only mode, row limits, query timeouts

## Installation

```bash
pip install mssql-mcp
```

Or install from source:

```bash
git clone https://github.com/yourusername/mssql-mcp.git
cd mssql-mcp
pip install -e ".[dev]"
```

## Configuration

Copy `.env.sample` to `.env` and configure your settings:

```bash
cp .env.sample .env
```

Required environment variables:

| Variable | Description |
|----------|-------------|
| `MSSQL_HOST` | SQL Server hostname |
| `MSSQL_USER` | Database username |
| `MSSQL_PASSWORD` | Database password |
| `MSSQL_DATABASE` | Database name |

Optional settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `MSSQL_PORT` | `1433` | Server port |
| `MSSQL_READ_ONLY` | `false` | Block write operations |
| `MSSQL_MAX_ROWS` | `1000` | Query row limit |
| `MSSQL_QUERY_TIMEOUT` | `60` | Query timeout (seconds) |

## Usage

### With Claude Code

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "mssql-mcp",
      "env": {
        "MSSQL_HOST": "localhost",
        "MSSQL_USER": "sa",
        "MSSQL_PASSWORD": "your_password",
        "MSSQL_DATABASE": "your_database"
      }
    }
  }
}
```

### Standalone

```bash
# Run with stdio transport (default)
mssql-mcp

# Run with HTTP transport
mssql-mcp --http
```

## Available Tools

| Tool | Description |
|------|-------------|
| `execute_query` | Run a SELECT query |
| `validate_query` | Check if a query is safe to execute |
| `list_tables` | List tables and views |
| `describe_table` | Get column information for a table |
| `read_rows` | Read rows by ID or filter |
| `insert_row` | Insert a new row |
| `update_row` | Update an existing row |
| `delete_row` | Delete a row |
| `call_stored_proc` | Execute a stored procedure |
| `export_to_json` | Export query results to JSON |
| `export_to_csv` | Export query results to CSV |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint and format
ruff check .
ruff format .

# Type check
mypy src/
```

## License

Apache-2.0
