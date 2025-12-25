# pymssql-mcp

An MCP (Model Context Protocol) server for Microsoft SQL Server databases. Enables AI assistants like Claude to interact with SQL Server through a standardized protocol.

[![PyPI version](https://badge.fury.io/py/pymssql-mcp.svg)](https://badge.fury.io/py/pymssql-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Features

- **Natural Language Queries**: Ask Claude about your data in plain English
- **Schema Discovery**: Explore tables, views, columns, and relationships
- **CRUD Operations**: Read, insert, update, and delete rows safely
- **Stored Procedures**: Execute stored procedures with parameters
- **Multi-Database Support**: List and switch between databases
- **Data Export**: Export query results to JSON or CSV files
- **Transaction Support**: Begin, commit, and rollback transactions
- **Knowledge Persistence**: Claude remembers what it learns about your database
- **Safety Controls**: Read-only mode, command blocking, row limits, schema restrictions
- **Connection Watchdog**: Automatic recovery from hung connections
- **OAuth Integration**: Deploy as a Claude.ai Custom Connector with SSO

## Documentation

| Guide | Description |
|-------|-------------|
| [What is MCP?](docs/what-is-mcp.md) | Understanding MCP and pymssql-mcp |
| [Installation](docs/installation.md) | Complete installation guide |
| [Quickstart](docs/quickstart.md) | Get running in 10 minutes |
| [Configuration](docs/configuration.md) | All configuration options |
| [Tools Reference](docs/tools.md) | Detailed tool documentation |
| [Usage Examples](docs/examples.md) | Common usage patterns |
| [OAuth Setup](docs/oauth.md) | Claude.ai integration with SSO |

## Quick Start

### 1. Install

```bash
pip install pymssql-mcp
```

### 2. Configure Claude Desktop

Edit your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mssql": {
      "command": "pymssql-mcp",
      "env": {
        "MSSQL_HOST": "your-server.example.com",
        "MSSQL_USER": "your-username",
        "MSSQL_PASSWORD": "your-password",
        "MSSQL_DATABASE": "your-database",
        "MSSQL_READ_ONLY": "true"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

Quit and reopen Claude Desktop. You'll see a hammer icon indicating tools are available.

### 4. Start Chatting

Ask Claude about your database:

> "What tables are available?"

> "Describe the Customers table"

> "Show me the top 10 orders by total amount"

> "How many customers do we have in each state?"

## Available Tools

### Connection & Database
| Tool | Description |
|------|-------------|
| `connect` | Connect to the database |
| `disconnect` | Close all connections |
| `list_databases` | List available databases |
| `switch_database` | Switch database context |

### Queries & Schema
| Tool | Description |
|------|-------------|
| `execute_query` | Run a SELECT query |
| `validate_query` | Check if a query is safe |
| `list_tables` | List tables and views |
| `describe_table` | Get column information |

### CRUD Operations
| Tool | Description |
|------|-------------|
| `read_rows` | Read rows by ID or filter |
| `insert_row` | Insert a new row |
| `update_row` | Update an existing row |
| `delete_row` | Delete a row |

### Stored Procedures
| Tool | Description |
|------|-------------|
| `list_stored_procs` | List available procedures |
| `describe_stored_proc` | Get procedure parameters |
| `call_stored_proc` | Execute a procedure |

### Export & Transactions
| Tool | Description |
|------|-------------|
| `export_to_json` | Export results to JSON |
| `export_to_csv` | Export results to CSV |
| `begin_transaction` | Start a transaction |
| `commit_transaction` | Commit changes |
| `rollback_transaction` | Rollback changes |

### Knowledge Persistence
| Tool | Description |
|------|-------------|
| `save_knowledge` | Save learned information |
| `get_all_knowledge` | Retrieve all knowledge |
| `search_knowledge` | Search saved knowledge |

## Configuration

### Required Variables

| Variable | Description |
|----------|-------------|
| `MSSQL_HOST` | SQL Server hostname |
| `MSSQL_USER` | Database username |
| `MSSQL_PASSWORD` | Database password |
| `MSSQL_DATABASE` | Database name |

### Safety Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MSSQL_READ_ONLY` | `false` | Block all write operations |
| `MSSQL_MAX_ROWS` | `1000` | Maximum rows per query |
| `MSSQL_BLOCKED_COMMANDS` | `DROP,TRUNCATE,...` | Commands to block |
| `MSSQL_ALLOWED_SCHEMAS` | (all) | Restrict to specific schemas |
| `MSSQL_BLOCKED_DATABASES` | (none) | Hide specific databases |

See [Configuration Reference](docs/configuration.md) for all options.

## Deployment Modes

### Local (Default)

Run as a local process with Claude Desktop:

```bash
pymssql-mcp
```

### HTTP/SSE Server

Run as a shared HTTP server for multiple users:

```bash
pymssql-mcp --http --host 0.0.0.0 --port 8080
```

### Streamable HTTP (Claude.ai Integration)

Run with OAuth authentication for Claude.ai:

```bash
pymssql-mcp --streamable-http --host 0.0.0.0 --port 8080
```

See [OAuth Setup](docs/oauth.md) for complete integration instructions.

## Development

```bash
# Clone repository
git clone https://github.com/bpamiri/pymssql-mcp.git
cd pymssql-mcp

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint and format
ruff check .
ruff format .

# Type check
mypy src/
```

## Security

pymssql-mcp includes multiple safety features:

- **Read-only mode**: Prevent all write operations
- **Command blocking**: Block dangerous SQL commands (DROP, TRUNCATE, etc.)
- **Schema restrictions**: Limit access to specific schemas
- **Database blocklist**: Hide sensitive databases
- **Row limits**: Cap query results to prevent memory issues
- **Query validation**: Analyze queries before execution
- **Parameterized queries**: Prevent SQL injection

See [SECURITY.md](SECURITY.md) for security policy and best practices.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache-2.0. See [LICENSE](LICENSE) for details.

## Links

- [PyPI Package](https://pypi.org/project/pymssql-mcp/)
- [GitHub Repository](https://github.com/bpamiri/pymssql-mcp)
- [Issue Tracker](https://github.com/bpamiri/pymssql-mcp/issues)
- [MCP Documentation](https://modelcontextprotocol.io/)
