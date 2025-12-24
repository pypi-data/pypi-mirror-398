# Tools Reference

This document provides a complete reference for all MCP tools available in pymssql-mcp.

## Overview

pymssql-mcp provides 25 tools organized into these categories:

| Category | Tools | Description |
|----------|-------|-------------|
| [Connection](#connection-management) | 3 | Connect/disconnect from database |
| [Query](#query-execution) | 2 | Execute and validate SQL queries |
| [Schema Discovery](#schema-discovery) | 2 | Explore tables and columns |
| [CRUD Operations](#crud-operations) | 4 | Read, insert, update, delete rows |
| [Export](#data-export) | 2 | Export data to JSON/CSV files |
| [Stored Procedures](#stored-procedures) | 3 | List, describe, and execute procedures |
| [Database Management](#database-management) | 2 | List and switch databases |
| [Transactions](#transaction-management) | 4 | Begin, commit, rollback transactions |
| [Knowledge](#knowledge-persistence) | 6 | Save and retrieve learned information |

---

## Connection Management

### connect

Establish connection to the SQL Server database.

**Parameters:** None (uses environment configuration)

**Returns:**
```json
{
  "status": "connected",
  "host": "server.example.com",
  "database": "SalesDB",
  "connected_at": "2024-01-15T10:30:00"
}
```

**Example usage:**
> "Connect to the database"

---

### disconnect

Close all connections to the SQL Server database.

**Parameters:** None

**Returns:**
```json
{
  "status": "disconnected",
  "connections_closed": 1
}
```

---

### list_connections

List all active database connections.

**Parameters:** None

**Returns:**
```json
{
  "connections": [
    {
      "name": "default",
      "host": "server.example.com",
      "database": "SalesDB",
      "connected_at": "2024-01-15T10:30:00",
      "is_active": true
    }
  ]
}
```

---

## Query Execution

### execute_query

Execute a read-only SQL SELECT query and return results.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | Required | SQL SELECT statement |
| `max_rows` | integer | `MSSQL_MAX_ROWS` | Maximum rows to return |

**Returns:**
```json
{
  "query": "SELECT * FROM Customers",
  "executed_query": "SELECT TOP 1000 * FROM Customers",
  "columns": ["CustomerID", "Name", "Email"],
  "rows": [
    {"CustomerID": 1, "Name": "Acme Corp", "Email": "contact@acme.com"}
  ],
  "row_count": 1,
  "max_rows": 1000
}
```

**Note:** Only SELECT queries are allowed. The query automatically has a TOP clause injected for safety.

**Example usage:**
> "Show me all customers in California"
> "Count orders by status"

---

### validate_query

Check if a query is safe to execute without running it.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | SQL statement to validate |

**Returns:**
```json
{
  "query": "SELECT * FROM Customers",
  "valid": true,
  "statement_type": "SELECT",
  "warnings": [],
  "suggestions": ["Consider using TOP clause to limit results"]
}
```

Validates against:
- Statement type (SELECT, INSERT, UPDATE, DELETE, DDL)
- Blocked commands list
- Read-only mode compliance
- Potential issues (missing WHERE clause, unbounded SELECT)

---

## Schema Discovery

### list_tables

List all tables and views in the database.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `schema` | string | All schemas | Filter by schema name (e.g., 'dbo') |
| `include_views` | boolean | `true` | Include views in results |
| `pattern` | string | None | Filter by name using SQL LIKE pattern |

**Returns:**
```json
{
  "tables": [
    {"schema": "dbo", "name": "Customers", "type": "TABLE"},
    {"schema": "dbo", "name": "Orders", "type": "TABLE"},
    {"schema": "dbo", "name": "vw_ActiveCustomers", "type": "VIEW"}
  ],
  "count": 3
}
```

**Example usage:**
> "What tables are available?"
> "List all tables starting with 'Order'"

---

### describe_table

Get detailed column information for a table.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table` | string | Yes | Table name (e.g., 'dbo.Customers' or 'Customers') |

**Returns:**
```json
{
  "table": "dbo.Customers",
  "columns": [
    {"name": "CustomerID", "type": "int", "nullable": false},
    {"name": "Name", "type": "nvarchar", "max_length": 100, "nullable": false},
    {"name": "Email", "type": "varchar", "max_length": 255, "nullable": true}
  ],
  "primary_key": ["CustomerID"],
  "foreign_keys": [
    {"constraint": "FK_Customers_Region", "column": "RegionID", "references_table": "dbo.Regions", "references_column": "RegionID"}
  ],
  "indexes": [
    {"name": "PK_Customers", "type": "CLUSTERED", "is_unique": true, "is_primary_key": true, "columns": "CustomerID"}
  ]
}
```

**Example usage:**
> "Describe the Orders table"
> "What columns are in dbo.Products?"

---

## CRUD Operations

### read_rows

Read rows from a table by primary key or filter.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `table` | string | Required | Table name |
| `id` | any | None | Single primary key value |
| `ids` | list | None | List of primary key values |
| `filter` | string | None | WHERE clause (without 'WHERE') |
| `columns` | list | All | Columns to return |
| `max_rows` | integer | Config | Maximum rows to return |

Provide one of: `id` (single row), `ids` (multiple rows), or `filter` (WHERE clause).

**Returns:**
```json
{
  "table": "dbo.Customers",
  "rows": [
    {"CustomerID": 1, "Name": "Acme Corp", "Email": "contact@acme.com"}
  ],
  "count": 1
}
```

**Example usage:**
> "Read customer with ID 12345"
> "Get all orders where status = 'Pending'"

---

### insert_row

Insert a new row into a table.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table` | string | Yes | Table name |
| `data` | object | Yes | Column names and values |

**Returns:**
```json
{
  "status": "success",
  "table": "dbo.Customers",
  "inserted": {"CustomerID": 123, "Name": "New Customer", "Email": "new@example.com"}
}
```

**Note:** Disabled in read-only mode.

---

### update_row

Update an existing row by primary key.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table` | string | Yes | Table name |
| `id` | any | Yes | Primary key value |
| `data` | object | Yes | Column names and new values |

**Returns:**
```json
{
  "status": "success",
  "table": "dbo.Customers",
  "updated": {"CustomerID": 123, "Name": "Updated Name", "Email": "updated@example.com"}
}
```

**Note:** Disabled in read-only mode.

---

### delete_row

Delete a row by primary key.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table` | string | Yes | Table name |
| `id` | any | Yes | Primary key value |

**Returns:**
```json
{
  "status": "deleted",
  "table": "dbo.Customers",
  "id": 123,
  "rows_affected": 1
}
```

**Note:** Disabled in read-only mode.

---

## Data Export

### export_to_json

Export query results to a JSON file.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | SQL SELECT query |
| `filename` | string | Yes | Output file path |

**Returns:**
```json
{
  "status": "success",
  "path": "/path/to/output.json",
  "row_count": 150,
  "file_size": 24576
}
```

**Note:** Only SELECT queries are allowed.

---

### export_to_csv

Export query results to a CSV file.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | Required | SQL SELECT query |
| `filename` | string | Required | Output file path |
| `delimiter` | string | `,` | Field delimiter |

**Returns:**
```json
{
  "status": "success",
  "path": "/path/to/output.csv",
  "row_count": 150,
  "file_size": 12288
}
```

---

## Stored Procedures

### list_stored_procs

List available stored procedures in the database.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `schema` | string | All | Filter by schema name |
| `pattern` | string | All | Filter by name pattern (SQL LIKE) |

**Returns:**
```json
{
  "procedures": [
    {"schema": "dbo", "name": "sp_GetCustomerOrders", "created": "2024-01-01T10:00:00", "modified": "2024-01-15T14:30:00"}
  ],
  "count": 1
}
```

---

### describe_stored_proc

Get parameter information for a stored procedure.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `procedure` | string | Yes | Procedure name (e.g., 'dbo.sp_GetUser') |

**Returns:**
```json
{
  "procedure": "dbo.sp_GetCustomerOrders",
  "parameters": [
    {"name": "@CustomerID", "type": "int", "direction": "IN"},
    {"name": "@StartDate", "type": "datetime", "direction": "IN"},
    {"name": "(return value)", "type": "int", "direction": "OUT"}
  ]
}
```

---

### call_stored_proc

Execute a stored procedure.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `procedure` | string | Required | Procedure name |
| `params` | object | None | Input parameter values (without @) |

**Returns:**
```json
{
  "status": "success",
  "procedure": "dbo.sp_GetCustomerOrders",
  "result_sets": [[{"OrderID": 1, "Total": 99.99}]],
  "row_count": 1
}
```

**Note:** Disabled in read-only mode.

---

## Database Management

### list_databases

List all available databases on the SQL Server.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_system` | boolean | `false` | Include system databases |

**Returns:**
```json
{
  "databases": ["SalesDB", "HRDatabase", "Inventory"],
  "current_database": "SalesDB",
  "count": 3,
  "blocked_count": 0
}
```

System databases (master, tempdb, model, msdb) are excluded by default. Databases in the blocklist are always excluded.

---

### switch_database

Switch the active database context.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `database_name` | string | Yes | Database to switch to |

**Returns:**
```json
{
  "status": "switched",
  "database": "HRDatabase",
  "previous_database": "SalesDB"
}
```

**Note:** Blocked databases cannot be switched to.

---

## Transaction Management

### begin_transaction

Begin a database transaction.

**Parameters:** None

**Returns:**
```json
{
  "status": "success",
  "message": "Transaction started",
  "in_transaction": true,
  "started_at": "2024-01-15T10:30:00"
}
```

**Note:** Only one transaction can be active at a time. Disabled in read-only mode.

---

### commit_transaction

Commit the current transaction.

**Parameters:** None

**Returns:**
```json
{
  "status": "success",
  "message": "Transaction committed successfully",
  "in_transaction": false
}
```

---

### rollback_transaction

Rollback the current transaction.

**Parameters:** None

**Returns:**
```json
{
  "status": "success",
  "message": "Transaction rolled back successfully",
  "in_transaction": false
}
```

---

### get_transaction_status

Get the current transaction status.

**Parameters:** None

**Returns:**
```json
{
  "in_transaction": true,
  "started_at": "2024-01-15T10:30:00",
  "read_only_mode": false
}
```

---

## Knowledge Persistence

These tools allow Claude to save and retrieve learned information about your database across sessions.

### save_knowledge

Save learned information about the SQL Server database.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `topic` | string | Required | Short descriptive name |
| `content` | string | Required | The knowledge (markdown supported) |
| `append` | boolean | `false` | Add to existing topic |

**Good things to save:**
- Table purposes (e.g., "Customers contains customer master records")
- Column meanings (e.g., "StatusCode 1=Active, 2=Inactive")
- Working query patterns
- Relationships between tables
- Data format notes

**Example:**
```
save_knowledge(
  "dbo.Customers",
  "Customer master table. PK is CustomerID.\n- Name: Customer name\n- StatusCode: 1=Active, 2=Inactive"
)
```

---

### list_knowledge

List all saved knowledge topics.

**Parameters:** None

**Returns:**
```json
{
  "topics": [
    {"topic": "dbo.Customers", "summary": "Customer master table..."},
    {"topic": "Status codes", "summary": "StatusCode meanings..."}
  ],
  "count": 2,
  "knowledge_file": "/path/to/knowledge.md"
}
```

---

### get_all_knowledge

Get ALL saved knowledge about this database.

**Parameters:** None

**Returns:**
```json
{
  "status": "success",
  "knowledge": "# dbo.Customers\nCustomer master table...\n\n# Status codes\n...",
  "topic_count": 2,
  "topics": ["dbo.Customers", "Status codes"]
}
```

**Important:** Call this at the start of conversations to retrieve previously learned information.

---

### get_knowledge_topic

Get saved knowledge for a specific topic.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `topic` | string | Yes | The topic name to retrieve |

**Returns:**
```json
{
  "status": "found",
  "topic": "dbo.Customers",
  "content": "Customer master table. PK is CustomerID..."
}
```

---

### search_knowledge

Search saved knowledge for specific information.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Text to search for (case-insensitive) |

**Returns:**
```json
{
  "query": "customer",
  "results": [
    {"topic": "dbo.Customers", "matches": ["Customer master table", "CustomerID"]}
  ],
  "match_count": 1
}
```

---

### delete_knowledge

Delete a saved knowledge topic.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `topic` | string | Required | Topic to delete |
| `confirm` | boolean | `false` | Must be `true` to execute |

---

## MCP Resources

In addition to tools, pymssql-mcp exposes these MCP resources:

### mssql://knowledge

Returns all saved knowledge about the database. Automatically available in every conversation.

### mssql://syntax_help

Returns T-SQL syntax reference including data types, functions, and common patterns.

### mssql://query_examples

Returns example T-SQL queries for common operations, helping Claude generate correct queries.

---

## Safety Features

### Read-Only Mode

When `MSSQL_READ_ONLY=true`:
- `insert_row` returns an error
- `update_row` returns an error
- `delete_row` returns an error
- `call_stored_proc` returns an error
- Transaction tools return errors
- Query and read operations work normally

### Command Blocking

SQL commands can be blocked via `MSSQL_BLOCKED_COMMANDS`. Default blocked commands:
- `DROP`, `TRUNCATE`, `ALTER`, `CREATE`
- `GRANT`, `REVOKE`, `DENY`
- `BACKUP`, `RESTORE`
- `KILL`, `SHUTDOWN`, `RECONFIGURE`

### Result Limiting

All queries are limited by `MSSQL_MAX_ROWS` (default: 1000).

### Confirmation Requirements

`delete_knowledge` requires `confirm=true` to execute.
