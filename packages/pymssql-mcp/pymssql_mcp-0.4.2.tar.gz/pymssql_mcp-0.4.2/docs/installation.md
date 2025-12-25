# Installation Guide

This guide covers installing pymssql-mcp and configuring it to work with Claude Desktop.

**New to MCP?** Start with [What is MCP?](what-is-mcp.md) to understand how this all works.

**Want the fastest path?** See the [Quickstart Guide](quickstart.md) for a 10-minute setup.

## What Gets Installed

When you install pymssql-mcp, you get:

- **pymssql-mcp** - The MCP server that connects Claude to SQL Server
- **pymssql** - Python driver for SQL Server connectivity
- **FastMCP** - The framework for building MCP servers
- **Supporting libraries** - pydantic-settings, starlette (for HTTP mode)

The installation is about 30MB total.

## Prerequisites

Before installing, you need:

| Requirement | Why You Need It | How to Get It |
|-------------|-----------------|---------------|
| **Python 3.10+** | Runs the MCP server | [python.org/downloads](https://www.python.org/downloads/) |
| **Claude Desktop** | The AI assistant that uses MCP | [claude.ai/download](https://claude.ai/download) |
| **SQL Server access** | The database you're connecting to | Contact your DBA |

### Checking Python Version

```bash
python --version
# Should show Python 3.10.x or higher
```

If you see Python 2.x or an older 3.x version, install a newer Python first.

### SQL Server Requirements

You'll need:
- SQL Server hostname or IP address
- Username and password with database access
- Database name to connect to
- Network access from your computer (port 1433 by default)

## Installation Methods

### Method 1: pip (Recommended)

```bash
pip install pymssql-mcp
```

### Method 2: uvx (Isolated Execution)

```bash
uvx pymssql-mcp
```

This runs pymssql-mcp in an isolated environment without permanent installation.

### Method 3: From Source

```bash
git clone https://github.com/bpamiri/pymssql-mcp.git
cd pymssql-mcp
pip install -e .
```

## Claude Desktop Setup

Claude Desktop needs to know about pymssql-mcp so it can start it and communicate with it. This is done through a JSON configuration file.

### Understanding the Config File

The config file tells Claude Desktop:
- **Where to find pymssql-mcp** (the `command` field)
- **How to connect to your database** (the `env` field with credentials)
- **What to call this server** (the key name, like "mssql")

When Claude Desktop starts, it reads this config and launches pymssql-mcp in the background.

### 1. Locate the Config File

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

### 2. Add pymssql-mcp Configuration

Create or edit the config file. Here's what each part means:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "uvx",
      "args": ["pymssql-mcp"],
      "env": {
        "MSSQL_HOST": "your-server.example.com",
        "MSSQL_USER": "username",
        "MSSQL_PASSWORD": "password",
        "MSSQL_DATABASE": "YourDatabase"
      }
    }
  }
}
```

**Config breakdown:**

| Field | Purpose | Example |
|-------|---------|---------|
| `"mssql"` | Name for this server (you choose) | `"mssql"` or `"production-db"` |
| `command` | Program to run | `"uvx"` or `"pymssql-mcp"` |
| `args` | Command arguments | `["pymssql-mcp"]` for uvx |
| `MSSQL_HOST` | Database server hostname | `"sqlserver.company.com"` |
| `MSSQL_USER` | Database username | `"appuser"` |
| `MSSQL_PASSWORD` | Database password | `"secretpassword"` |
| `MSSQL_DATABASE` | Database name | `"SalesDB"` |

### 3. Alternative: Using pip Installation

If you installed via pip:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "pymssql-mcp",
      "env": {
        "MSSQL_HOST": "your-server.example.com",
        "MSSQL_USER": "username",
        "MSSQL_PASSWORD": "password",
        "MSSQL_DATABASE": "YourDatabase"
      }
    }
  }
}
```

### 4. Alternative: From Source with Virtual Environment

If running from source:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "/bin/bash",
      "args": ["-c", "cd /path/to/pymssql-mcp && .venv/bin/python -m mssql_mcp"],
      "env": {
        "MSSQL_HOST": "your-server.example.com",
        "MSSQL_USER": "username",
        "MSSQL_PASSWORD": "password",
        "MSSQL_DATABASE": "YourDatabase"
      }
    }
  }
}
```

### 5. Restart Claude Desktop

Quit Claude Desktop completely (Cmd+Q on macOS, or exit from system tray on Windows) and reopen it.

### 6. Verify Installation

In Claude Desktop, you should see a hammer icon indicating tools are available. Try asking:

> "Connect to the database and list available tables"

## Optional Settings

Add these to your `env` section for additional control:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "pymssql-mcp",
      "env": {
        "MSSQL_HOST": "your-server.example.com",
        "MSSQL_USER": "username",
        "MSSQL_PASSWORD": "password",
        "MSSQL_DATABASE": "YourDatabase",
        "MSSQL_PORT": "1433",
        "MSSQL_READ_ONLY": "true",
        "MSSQL_MAX_ROWS": "1000"
      }
    }
  }
}
```

| Variable | Purpose | Default |
|----------|---------|---------|
| `MSSQL_PORT` | SQL Server port | `1433` |
| `MSSQL_READ_ONLY` | Disable write operations | `false` |
| `MSSQL_MAX_ROWS` | Limit query results | `1000` |
| `MSSQL_TIMEOUT` | Connection timeout (seconds) | `30` |

See [Configuration Reference](configuration.md) for all options.

## Multiple Database Connections

You can configure multiple SQL Server connections:

```json
{
  "mcpServers": {
    "production-db": {
      "command": "pymssql-mcp",
      "env": {
        "MSSQL_HOST": "prod-server.example.com",
        "MSSQL_USER": "readonly_user",
        "MSSQL_PASSWORD": "password",
        "MSSQL_DATABASE": "ProductionDB",
        "MSSQL_READ_ONLY": "true"
      }
    },
    "dev-db": {
      "command": "pymssql-mcp",
      "env": {
        "MSSQL_HOST": "dev-server.example.com",
        "MSSQL_USER": "dev_user",
        "MSSQL_PASSWORD": "password",
        "MSSQL_DATABASE": "DevelopmentDB"
      }
    }
  }
}
```

Claude will see both as separate tool sets and can work with either.

## Azure SQL Database

For Azure SQL Database, use your Azure SQL connection details:

```json
{
  "mcpServers": {
    "azure-sql": {
      "command": "pymssql-mcp",
      "env": {
        "MSSQL_HOST": "your-server.database.windows.net",
        "MSSQL_USER": "your-admin@your-server",
        "MSSQL_PASSWORD": "your-password",
        "MSSQL_DATABASE": "your-database",
        "MSSQL_PORT": "1433"
      }
    }
  }
}
```

Ensure your Azure SQL firewall allows connections from your IP address.

## Troubleshooting

### "Module not found" Error

Ensure pymssql-mcp is installed in the Python environment being used:

```bash
pip show pymssql-mcp
```

### Connection Refused

1. Verify your SQL Server is running and accepting connections
2. Check the hostname and port are correct
3. Verify network connectivity (try `telnet hostname 1433`)
4. Check firewall rules allow the connection
5. Verify credentials are correct

### "Login failed" Error

1. Verify username and password are correct
2. Check the database name exists
3. Ensure the user has permissions on the database
4. For Windows Authentication issues, use SQL Server Authentication instead

### Check MCP Logs

Claude Desktop logs MCP server output to:

**macOS:**
```
~/Library/Logs/Claude/mcp-server-mssql.log
```

**Windows:**
```
%APPDATA%\Claude\Logs\mcp-server-mssql.log
```

Review this file for detailed error messages.

### Python Not Found

If Claude can't find Python or pymssql-mcp, use the full path:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "/usr/local/bin/pymssql-mcp",
      "env": { ... }
    }
  }
}
```

Find your pymssql-mcp path with: `which pymssql-mcp` (Mac/Linux) or `where pymssql-mcp` (Windows)

## Next Steps

Now that you're installed:

1. **Test the connection** - Ask Claude "Connect to the database and show me the current database name"
2. **Explore your data** - Ask "What tables are available?"
3. **Learn more:**
   - [Usage Examples](examples.md) - Common usage patterns
   - [Configuration Reference](configuration.md) - All environment variables
   - [Tools Reference](tools.md) - Available MCP tools
   - [What is MCP?](what-is-mcp.md) - Understanding how it all works
