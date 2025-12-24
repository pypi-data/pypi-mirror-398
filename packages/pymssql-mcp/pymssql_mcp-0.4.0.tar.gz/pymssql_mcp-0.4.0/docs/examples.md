# Usage Examples

This guide shows common usage patterns for interacting with SQL Server databases through Claude using pymssql-mcp.

## Getting Started

### Initial Connection

When you start a conversation, Claude can connect to the database using your configured credentials:

> "Connect to the database and show me the current database"

Claude will:
1. Call `connect()` to establish the connection
2. Return connection details

### Exploring the Database

> "What tables are available in this database?"

```json
// Claude calls: list_tables()
{
  "tables": [
    {"schema": "dbo", "name": "Customers", "type": "TABLE"},
    {"schema": "dbo", "name": "Orders", "type": "TABLE"},
    {"schema": "dbo", "name": "Products", "type": "TABLE"}
  ],
  "count": 3
}
```

> "List all tables in the Sales schema"

```json
// Claude calls: list_tables(schema="Sales")
{
  "tables": [
    {"schema": "Sales", "name": "Invoices", "type": "TABLE"},
    {"schema": "Sales", "name": "LineItems", "type": "TABLE"}
  ],
  "count": 2
}
```

---

## Reading Data

### Single Row

> "Read customer with ID 12345"

```json
// Claude calls: read_rows(table="Customers", id=12345)
{
  "table": "dbo.Customers",
  "rows": [
    {
      "CustomerID": 12345,
      "Name": "Acme Corporation",
      "Email": "contact@acme.com",
      "State": "CA"
    }
  ],
  "count": 1
}
```

### Multiple Rows

> "Get customers with IDs 100, 101, and 102"

```json
// Claude calls: read_rows(table="Customers", ids=[100, 101, 102])
{
  "table": "dbo.Customers",
  "rows": [
    {"CustomerID": 100, "Name": "Customer A", ...},
    {"CustomerID": 101, "Name": "Customer B", ...},
    {"CustomerID": 102, "Name": "Customer C", ...}
  ],
  "count": 3
}
```

### Filtered Results

> "Show me all active customers in California"

```json
// Claude calls: read_rows(table="Customers", filter="State = 'CA' AND Status = 'Active'")
{
  "table": "dbo.Customers",
  "rows": [...],
  "count": 47
}
```

### Understanding Table Structure

> "Describe the Orders table"

Claude will call `describe_table("Orders")` and explain:
- All columns with their data types
- Primary key columns
- Foreign key relationships
- Indexes

---

## Querying Data

### Basic Queries

> "List all customers in California"

```sql
-- Claude generates and executes:
SELECT TOP 1000 * FROM dbo.Customers WHERE State = 'CA'
```

> "Count how many orders are pending"

```sql
-- Claude generates and executes:
SELECT COUNT(*) AS count FROM dbo.Orders WHERE Status = 'Pending'
```

> "Show me the top 10 products by price"

```sql
-- Claude generates and executes:
SELECT TOP 10 * FROM dbo.Products ORDER BY Price DESC
```

### Aggregations

> "What's our total sales by region?"

```sql
-- Claude generates:
SELECT Region, SUM(Total) AS TotalSales, COUNT(*) AS OrderCount
FROM dbo.Orders
GROUP BY Region
ORDER BY TotalSales DESC
```

### Filtering with Multiple Conditions

> "Find orders over $1000 from California customers in the last 30 days"

```sql
-- Claude generates:
SELECT o.*
FROM dbo.Orders o
JOIN dbo.Customers c ON o.CustomerID = c.CustomerID
WHERE c.State = 'CA'
  AND o.Total > 1000
  AND o.OrderDate >= DATEADD(DAY, -30, GETDATE())
```

### Working with Dates

> "Show me orders from January 2024"

```sql
-- Claude generates:
SELECT * FROM dbo.Orders
WHERE OrderDate >= '2024-01-01' AND OrderDate < '2024-02-01'
```

---

## Understanding Data Structure

### Dictionary Exploration

> "What columns are in the Orders table?"

```json
// Claude calls: describe_table(table="Orders")
{
  "table": "dbo.Orders",
  "columns": [
    {"name": "OrderID", "type": "int", "nullable": false},
    {"name": "CustomerID", "type": "int", "nullable": false},
    {"name": "OrderDate", "type": "datetime2", "nullable": false},
    {"name": "Total", "type": "decimal", "precision": 18, "scale": 2}
  ],
  "primary_key": ["OrderID"],
  "foreign_keys": [
    {"column": "CustomerID", "references_table": "dbo.Customers", "references_column": "CustomerID"}
  ]
}
```

### Finding Relationships

> "What tables reference the Customers table?"

Claude will query the foreign key metadata to find all tables that have foreign keys pointing to Customers.

---

## Writing Data

### Creating a Record

> "Create a new customer named 'Test Company' with email 'test@example.com'"

```json
// Claude calls: insert_row(table="Customers", data={"Name": "Test Company", "Email": "test@example.com"})
{
  "status": "success",
  "table": "dbo.Customers",
  "inserted": {
    "CustomerID": 12346,
    "Name": "Test Company",
    "Email": "test@example.com"
  }
}
```

### Updating a Record

> "Update customer 12345 to change the email to 'newemail@acme.com'"

```json
// Claude calls: update_row(table="Customers", id=12345, data={"Email": "newemail@acme.com"})
{
  "status": "success",
  "table": "dbo.Customers",
  "updated": {
    "CustomerID": 12345,
    "Name": "Acme Corporation",
    "Email": "newemail@acme.com"
  }
}
```

### Deleting a Record

> "Delete customer 99999"

```json
// Claude calls: delete_row(table="Customers", id=99999)
{
  "status": "deleted",
  "table": "dbo.Customers",
  "id": 99999,
  "rows_affected": 1
}
```

---

## Exporting Data

### JSON Export

> "Export all California customers to a JSON file"

```json
// Claude first queries, then exports
// Claude calls: export_to_json(query="SELECT * FROM Customers WHERE State = 'CA'", filename="ca_customers.json")
{
  "status": "success",
  "path": "/Users/me/ca_customers.json",
  "row_count": 150,
  "file_size": 24576
}
```

### CSV Export

> "Export the orders report to CSV"

```json
// Claude calls: export_to_csv(query="SELECT * FROM Orders WHERE OrderDate >= '2024-01-01'", filename="orders_2024.csv")
{
  "status": "success",
  "path": "/Users/me/orders_2024.csv",
  "row_count": 500,
  "file_size": 45678
}
```

---

## Working with Stored Procedures

### Listing Procedures

> "What stored procedures are available?"

```json
// Claude calls: list_stored_procs()
{
  "procedures": [
    {"schema": "dbo", "name": "sp_GetCustomerOrders", ...},
    {"schema": "dbo", "name": "sp_ProcessOrder", ...}
  ],
  "count": 2
}
```

### Understanding Procedure Parameters

> "What parameters does sp_GetCustomerOrders need?"

```json
// Claude calls: describe_stored_proc(procedure="sp_GetCustomerOrders")
{
  "procedure": "dbo.sp_GetCustomerOrders",
  "parameters": [
    {"name": "@CustomerID", "type": "int", "direction": "IN"},
    {"name": "@StartDate", "type": "datetime", "direction": "IN"},
    {"name": "@EndDate", "type": "datetime", "direction": "IN"}
  ]
}
```

### Calling a Procedure

> "Get orders for customer 12345 for January 2024"

```json
// Claude calls: call_stored_proc(
//   procedure="sp_GetCustomerOrders",
//   params={"CustomerID": 12345, "StartDate": "2024-01-01", "EndDate": "2024-01-31"}
// )
{
  "status": "success",
  "procedure": "dbo.sp_GetCustomerOrders",
  "result_sets": [[{"OrderID": 1, "Total": 99.99}, ...]],
  "row_count": 5
}
```

---

## Using Transactions

### Transaction Workflow

> "I need to update multiple related records atomically"

```json
// Claude calls: begin_transaction()
{
  "status": "success",
  "message": "Transaction started",
  "in_transaction": true
}

// Claude performs multiple updates...

// Claude calls: commit_transaction()
{
  "status": "success",
  "message": "Transaction committed successfully"
}
```

### Rolling Back

> "Cancel the changes, something went wrong"

```json
// Claude calls: rollback_transaction()
{
  "status": "success",
  "message": "Transaction rolled back successfully"
}
```

---

## Knowledge Persistence

### Saving Discoveries

When Claude discovers useful information about your database, it can save it:

> Claude: "I found that StatusCode 1 means Active and 2 means Inactive. Let me save this for future reference."

```json
// Claude calls: save_knowledge(
//   topic="Status codes",
//   content="In the Customers table:\n- StatusCode 1 = Active\n- StatusCode 2 = Inactive\n- StatusCode 3 = Suspended"
// )
```

### Retrieving Knowledge

In future sessions, Claude can recall this information:

```json
// Claude calls: get_all_knowledge()
{
  "knowledge": "# Status codes\nIn the Customers table:\n- StatusCode 1 = Active\n...",
  "topic_count": 1
}
```

### Managing Knowledge

> "What have you learned about this database?"

```json
// Claude calls: list_knowledge()
{
  "topics": [
    {"topic": "Status codes", "summary": "StatusCode meanings..."},
    {"topic": "dbo.Customers", "summary": "Customer master table..."},
    {"topic": "Date formats", "summary": "Dates stored as datetime2..."}
  ],
  "count": 3
}
```

---

## Complex Workflows

### Data Investigation

> "I need to understand the relationship between Orders and Customers"

Claude will:
1. Call `describe_table("Orders")` to see order structure
2. Call `describe_table("Customers")` to see customer structure
3. Find the foreign key relationship (CustomerID)
4. Sample some data to verify
5. Save the discovered relationship for future reference

### Report Generation

> "Generate a summary of orders by customer for January 2024"

Claude will:
1. Build a query with grouping and aggregation
2. Execute the query
3. Present a formatted summary
4. Optionally export to CSV or JSON

### Data Cleanup Task

> "Find all customers without an email address"

Claude will:
1. Execute a query for null/empty emails
2. Present the results
3. With your permission, help update the records

---

## Switching Databases

### List Available Databases

> "What databases can I access?"

```json
// Claude calls: list_databases()
{
  "databases": ["SalesDB", "HRDatabase", "Inventory"],
  "current_database": "SalesDB",
  "count": 3
}
```

### Switch Context

> "Switch to the Inventory database"

```json
// Claude calls: switch_database(database_name="Inventory")
{
  "status": "switched",
  "database": "Inventory",
  "previous_database": "SalesDB"
}
```

---

## Best Practices

### Start with Exploration

Before querying, understand the database structure:
1. Use `list_tables` to see available tables
2. Use `describe_table` to understand columns
3. Ask Claude to save what it learns

### Use Read-Only Mode for Exploration

Set `MSSQL_READ_ONLY=true` when exploring to prevent accidental changes.

### Let Claude Learn

Encourage Claude to save useful discoveries:
> "Please save what you learned about this table for next time"

### Verify Before Writing

Always review Claude's proposed changes before confirming writes.

### Use Transactions for Related Changes

When updating multiple records that must succeed together, use transactions.

---

## Troubleshooting

### Query Returns No Results

> "My query isn't returning anything"

Claude will:
1. Validate the query syntax with `validate_query`
2. Check if the column and table names are correct
3. Verify data exists matching the criteria
4. Suggest corrections

### Column Not Found

> "It says 'CustomerName' is not found"

Claude will:
1. Check `describe_table` for the correct column name
2. Look for similar names (Name, CustName, etc.)
3. Suggest the correct column to use

### Connection Issues

> "I'm getting connection errors"

Check:
1. Server hostname and port are correct
2. Credentials are valid
3. Network connectivity to the server
4. Firewall rules allow the connection
