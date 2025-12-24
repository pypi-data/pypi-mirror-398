# Quickstart Guide

Get pymssql-mcp running with Claude Desktop in 10 minutes.

## What You'll Need

Before starting, make sure you have:

- [ ] **Claude Desktop** installed ([download here](https://claude.ai/download))
- [ ] **Python 3.10 or later** installed
- [ ] **Access to a SQL Server database** with:
  - Hostname or IP address
  - Username and password
  - Database name to connect to
  - Network access from your computer

## Step 1: Install pymssql-mcp

Open your terminal (Command Prompt on Windows, Terminal on Mac/Linux) and run:

```bash
pip install pymssql-mcp
```

To verify it installed correctly:

```bash
pymssql-mcp --help
```

You should see:
```
usage: pymssql-mcp [-h] [--http] [--streamable-http] [--host HOST] [--port PORT]

MS SQL MCP Server - Connect AI assistants to SQL Server databases
```

## Step 2: Find Your Claude Desktop Config File

Claude Desktop stores its configuration in a JSON file. Find it at:

| Operating System | Config File Location |
|------------------|---------------------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

**Quick way to open on macOS:**
```bash
open ~/Library/Application\ Support/Claude/
```

**Quick way to open on Windows:**
```
explorer %APPDATA%\Claude
```

If the file doesn't exist, create it.

## Step 3: Configure Claude Desktop

Edit `claude_desktop_config.json` and add the pymssql-mcp configuration:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "pymssql-mcp",
      "env": {
        "MSSQL_HOST": "your-server-hostname",
        "MSSQL_USER": "your-username",
        "MSSQL_PASSWORD": "your-password",
        "MSSQL_DATABASE": "your-database-name",
        "MSSQL_READ_ONLY": "true"
      }
    }
  }
}
```

**Replace the placeholder values:**

| Setting | Replace With | Example |
|---------|--------------|---------|
| `MSSQL_HOST` | Your SQL Server hostname | `sqlserver.company.com` |
| `MSSQL_USER` | Your database username | `appuser` |
| `MSSQL_PASSWORD` | Your database password | `secretpassword` |
| `MSSQL_DATABASE` | Your database name | `SalesDB` |

**Important:** We set `MSSQL_READ_ONLY=true` for safety while you're learning. This prevents any accidental data changes.

### For Azure SQL Database

If you're connecting to Azure SQL Database:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "pymssql-mcp",
      "env": {
        "MSSQL_HOST": "your-server.database.windows.net",
        "MSSQL_USER": "your-admin@your-server",
        "MSSQL_PASSWORD": "your-password",
        "MSSQL_DATABASE": "your-database",
        "MSSQL_READ_ONLY": "true"
      }
    }
  }
}
```

## Step 4: Restart Claude Desktop

**Completely quit Claude Desktop** (not just close the window):

- **macOS:** Press Cmd+Q or right-click the dock icon and choose Quit
- **Windows:** Right-click the system tray icon and choose Exit

Then reopen Claude Desktop.

## Step 5: Verify It's Working

In Claude Desktop, you should see a **hammer icon** in the input area, indicating tools are available.

Try asking Claude:

> "Connect to the database and tell me the current database name"

Claude should respond with your connection details:

> "I've connected to SQL Server. You're connected to the 'SalesDB' database on server 'sqlserver.company.com'."

## Step 6: Start Exploring

Now you can ask Claude about your database:

### See What Tables Exist
> "What tables are available in this database?"

### Explore a Table's Structure
> "Describe the Customers table"

### Query Data
> "Show me the first 10 rows from the Orders table"

> "Count how many customers we have"

### Read Specific Rows
> "Read the customer with ID 12345"

## Troubleshooting

### "Tool not found" or No Hammer Icon

1. Make sure you completely quit and reopened Claude Desktop
2. Check your config file for JSON syntax errors (missing commas, quotes)
3. Verify pymssql-mcp is installed: `pymssql-mcp --help`

### Connection Errors

1. **Verify your credentials** work with other SQL tools (SSMS, Azure Data Studio)
2. **Check the hostname** is reachable from your computer
3. **Verify the port** - default is 1433
4. **Check firewall rules** allow connections

### Check the Logs

Claude Desktop logs MCP server output. Check:

**macOS:**
```bash
cat ~/Library/Logs/Claude/mcp-server-mssql.log
```

**Windows:**
```
%APPDATA%\Claude\Logs\mcp-server-mssql.log
```

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

## What's Next?

Now that you're connected:

1. **Learn what Claude can do** - See [Usage Examples](examples.md)
2. **Understand the tools** - See [Tools Reference](tools.md)
3. **Configure more options** - See [Configuration Reference](configuration.md)
4. **Learn how it works** - See [What is MCP?](what-is-mcp.md)

## Quick Reference

### Common Questions to Ask Claude

| What You Want | Ask Claude |
|---------------|------------|
| List tables | "What tables are in this database?" |
| Table structure | "Describe the Orders table" |
| Query data | "List customers in California" |
| Read row | "Read the order with OrderID 123" |
| Count records | "How many open invoices are there?" |
| Column info | "What columns are in the Products table?" |

### Configuration Cheat Sheet

```json
{
  "mcpServers": {
    "mssql": {
      "command": "pymssql-mcp",
      "env": {
        "MSSQL_HOST": "server.example.com",
        "MSSQL_USER": "username",
        "MSSQL_PASSWORD": "password",
        "MSSQL_DATABASE": "DatabaseName",
        "MSSQL_PORT": "1433",
        "MSSQL_READ_ONLY": "true",
        "MSSQL_MAX_ROWS": "1000"
      }
    }
  }
}
```

| Variable | Required | Description |
|----------|----------|-------------|
| `MSSQL_HOST` | Yes | Server hostname |
| `MSSQL_USER` | Yes | Username |
| `MSSQL_PASSWORD` | Yes | Password |
| `MSSQL_DATABASE` | Yes | Database name |
| `MSSQL_PORT` | No | Port (default: 1433) |
| `MSSQL_READ_ONLY` | No | Set to `true` to prevent writes |
| `MSSQL_MAX_ROWS` | No | Limit query results (default: 1000) |
