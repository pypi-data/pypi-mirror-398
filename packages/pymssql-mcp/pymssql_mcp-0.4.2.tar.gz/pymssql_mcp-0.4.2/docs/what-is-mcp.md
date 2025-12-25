# Understanding MCP and pymssql-mcp

This guide explains what MCP is, how it works, and how pymssql-mcp connects your Microsoft SQL Server database to AI assistants like Claude.

## What is MCP?

**MCP (Model Context Protocol)** is an open standard created by Anthropic that allows AI assistants to connect to external tools and data sources. Think of it as a "plugin system" for AI.

### The Problem MCP Solves

Without MCP, AI assistants like Claude can only:
- Answer questions from their training data
- Help with text in the conversation
- Have no access to your specific systems or data

With MCP, AI assistants can:
- Connect to your databases and query real data
- Read and write files on your system
- Call APIs and web services
- Execute commands and run programs
- Remember information across conversations

### How MCP Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Claude Desktop │◄───►│   MCP Server    │◄───►│   Your System   │
│  (AI Assistant) │     │   (pymssql-mcp) │     │   (SQL Server)  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     You talk to             Translates            Your actual
     Claude here             requests              data lives here
```

1. **You** ask Claude a question like "Show me all customers in California"
2. **Claude** recognizes it needs database access and calls the MCP server
3. **The MCP server (pymssql-mcp)** translates this into a SQL query
4. **SQL Server** returns the data
5. **pymssql-mcp** formats the results and sends them back to Claude
6. **Claude** presents the information to you in a readable format

### MCP Components

| Component | What It Is | Example |
|-----------|------------|---------|
| **MCP Host** | The AI application that uses MCP | Claude Desktop, Claude Code |
| **MCP Server** | A program that provides tools/data | pymssql-mcp (this project) |
| **Tools** | Actions the AI can perform | `execute_query`, `insert_row` |
| **Resources** | Data the AI can access | Database knowledge, syntax help |

## What is pymssql-mcp?

**pymssql-mcp** is an MCP server specifically for Microsoft SQL Server databases.

It allows Claude to:
- Query your SQL Server database using natural language
- Read and write rows in tables
- Explore table structures and schemas
- Execute stored procedures
- Learn and remember information about your database

### Why Use pymssql-mcp?

**Without pymssql-mcp:**
> You: "How many customers do we have in California?"
> Claude: "I don't have access to your database. You would need to run a query like `SELECT COUNT(*) FROM Customers WHERE State = 'CA'`..."

**With pymssql-mcp:**
> You: "How many customers do we have in California?"
> Claude: "You have 1,247 customers in California. The largest by revenue is Acme Corp (CustomerID: 12345)."

Claude can actually connect to your database, run the query, and give you real answers.

## Where Does pymssql-mcp Run?

pymssql-mcp runs as a **local process** on your computer, alongside Claude Desktop.

### Local Mode (Default)

```
Your Computer
┌────────────────────────────────────────────────┐
│                                                │
│  ┌──────────────┐      ┌──────────────┐       │
│  │    Claude    │      │  pymssql-mcp │       │
│  │   Desktop    │◄────►│   (local)    │       │
│  └──────────────┘      └──────┬───────┘       │
│                               │               │
└───────────────────────────────┼───────────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │     SQL Server       │
                    │       Server         │
                    └──────────────────────┘
                    (Can be local or remote)
```

- pymssql-mcp runs on your machine
- Credentials stay on your machine
- Connection goes directly to your database server
- Only you can access this instance

### Centralized Mode (Team Deployment)

For teams, pymssql-mcp can run as an HTTP server:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ User 1's Claude │     │                 │     │                 │
│     Desktop     │────►│                 │     │                 │
├─────────────────┤     │   pymssql-mcp   │     │   SQL Server    │
│ User 2's Claude │────►│   HTTP Server   │────►│     Server      │
│     Desktop     │     │                 │     │                 │
├─────────────────┤     │                 │     │                 │
│ User 3's Claude │────►│                 │     │                 │
│     Desktop     │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

- Single pymssql-mcp instance serves multiple users
- Shared knowledge base
- Centralized credential management

## How Claude Uses pymssql-mcp

When you install pymssql-mcp and configure Claude Desktop, Claude gains new abilities called **tools**. Here's what happens:

### 1. Tool Discovery

When Claude Desktop starts, it discovers what tools pymssql-mcp provides:
- `connect` - Connect to the database
- `execute_query` - Run SQL queries
- `read_rows` - Read table data
- `describe_table` - Explore table structure
- ...and 20+ more tools

### 2. Natural Language Understanding

When you ask a question, Claude decides which tools to use:

> You: "What columns are in the Customers table?"

Claude thinks: "The user wants to know about table structure. I should use the `describe_table` tool."

### 3. Tool Execution

Claude calls the tool with appropriate parameters:
```
describe_table(table="Customers")
```

### 4. Response Formatting

Claude receives the raw data and presents it clearly:

> Claude: "The Customers table has 8 columns:
> - CustomerID (int) - Primary key
> - Name (nvarchar) - Customer name
> - Email (varchar) - Email address, nullable
> ..."

## SQL Server Concepts

pymssql-mcp works with Microsoft SQL Server databases. Here are some key concepts:

| Concept | Description | Example |
|---------|-------------|---------|
| **Database** | Container for tables and objects | `SalesDB`, `HRDatabase` |
| **Schema** | Namespace within a database | `dbo`, `Sales`, `HR` |
| **Table** | Collection of rows with defined columns | `dbo.Customers` |
| **View** | Virtual table based on a query | `dbo.vw_ActiveCustomers` |
| **Stored Procedure** | Pre-compiled SQL statements | `dbo.sp_GetCustomerOrders` |

### Table Naming

Tables in SQL Server are referenced as `schema.table`:
- `dbo.Customers` - Customers table in dbo schema
- `Sales.Orders` - Orders table in Sales schema
- `Customers` - Defaults to `dbo.Customers`

## Security Considerations

### What pymssql-mcp Can Access

pymssql-mcp connects to your database with the credentials you provide. It can:
- Read any table/view the user account can read
- Write to tables (unless read-only mode is enabled)
- Execute stored procedures
- Switch between databases on the server

### Built-in Safety Features

- **Read-only mode** - Prevents all write operations (INSERT, UPDATE, DELETE)
- **Command blocking** - Dangerous commands like DROP, TRUNCATE are blocked
- **Query validation** - Only safe query patterns are allowed
- **Result limiting** - Large queries are automatically limited
- **Database blocklist** - Certain databases can be hidden entirely
- **Schema restrictions** - Limit access to specific schemas only

### Best Practices

1. **Use read-only mode** when exploring or for most users
2. **Create a dedicated database user** with minimal permissions
3. **Review the blocked commands** and add more if needed
4. **Keep credentials secure** - never commit them to source control
5. **Use the database blocklist** to hide sensitive databases

## Common Questions

### Do I need to learn SQL?

No! That's the point of pymssql-mcp. You can ask questions in plain English:
- "Show me all open orders" instead of `SELECT * FROM Orders WHERE Status = 'Open'`
- "Count customers by state" instead of `SELECT State, COUNT(*) FROM Customers GROUP BY State`

Claude will generate the appropriate queries.

### Does Claude understand my specific database?

Initially, no. But pymssql-mcp has a **knowledge persistence** feature. As Claude explores your database, it can save what it learns:
- "dbo.Customers is the customer master table"
- "StatusCode 1=Active, 2=Inactive, 3=Suspended"
- "OrderTotal is calculated from LineItems"

This knowledge persists across sessions, so Claude gets smarter over time.

### Can multiple people use the same pymssql-mcp?

Yes, with HTTP mode. One pymssql-mcp server can serve multiple Claude Desktop users, and they can share a common knowledge base.

### Is my data sent to Anthropic?

Your database queries and results pass through Claude (Anthropic's AI), similar to if you typed the data into a chat. Review Anthropic's privacy policy if this is a concern for your data.

The pymssql-mcp server itself runs locally and doesn't send data anywhere except to Claude and your database.

### What SQL Server versions are supported?

pymssql-mcp uses the `pymssql` package which supports:
- SQL Server 2012 and later
- Azure SQL Database
- Azure SQL Managed Instance

## Next Steps

Ready to get started?

1. **[Installation Guide](installation.md)** - Install pymssql-mcp and configure Claude Desktop
2. **[Quickstart Guide](quickstart.md)** - Get running in 10 minutes
3. **[Configuration Reference](configuration.md)** - All configuration options
4. **[Usage Examples](examples.md)** - See what you can do
5. **[Tools Reference](tools.md)** - Detailed tool documentation
