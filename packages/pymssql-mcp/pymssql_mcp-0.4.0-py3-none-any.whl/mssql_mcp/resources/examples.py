"""Query examples resource for mssql-mcp."""

from ..app import mcp

QUERY_EXAMPLES = """
T-SQL Query Examples
====================

These examples demonstrate common query patterns for SQL Server databases.
Adapt table and column names to match your actual schema.


BASIC LISTING
-------------

List all records from a table:
    SELECT * FROM Customers

List specific columns:
    SELECT FirstName, LastName, Email, Phone FROM Customers

List with row limit:
    SELECT TOP 100 * FROM Orders


FILTERING (WHERE clause)
------------------------

Filter by exact value:
    SELECT * FROM Customers WHERE State = 'CA'

Filter by multiple values (IN):
    SELECT * FROM Customers WHERE State IN ('CA', 'NV', 'AZ')

Filter by range:
    SELECT * FROM Invoices WHERE Amount BETWEEN 100 AND 1000

Filter by date:
    SELECT * FROM Orders WHERE OrderDate >= '2024-01-01'

Filter by pattern (starts with):
    SELECT * FROM Customers WHERE CompanyName LIKE 'ACME%'

Filter by pattern (contains):
    SELECT * FROM Customers WHERE CompanyName LIKE '%Corp%'

Filter for non-null values:
    SELECT * FROM Customers WHERE Phone IS NOT NULL

Filter for null values:
    SELECT * FROM Customers WHERE Email IS NULL

Combining conditions:
    SELECT * FROM Products
    WHERE Category = 'Electronics'
      AND Price > 100
      AND Active = 1


SORTING
-------

Sort ascending:
    SELECT * FROM Customers ORDER BY LastName

Sort descending:
    SELECT * FROM Products ORDER BY Price DESC

Sort by multiple columns:
    SELECT * FROM Customers ORDER BY State, City, LastName


COUNTING AND TOTALS
-------------------

Count records:
    SELECT COUNT(*) AS TotalCustomers FROM Customers WHERE State = 'CA'

Sum a column:
    SELECT SUM(Amount) AS TotalDue FROM Invoices WHERE Status = 'Open'

Multiple aggregations:
    SELECT
        COUNT(*) AS OrderCount,
        SUM(Total) AS TotalSales,
        AVG(Total) AS AverageOrder,
        MIN(Total) AS SmallestOrder,
        MAX(Total) AS LargestOrder
    FROM Orders


GROUPING
--------

Group by with counts:
    SELECT State, COUNT(*) AS CustomerCount
    FROM Customers
    GROUP BY State
    ORDER BY CustomerCount DESC

Group by with aggregations:
    SELECT
        Category,
        COUNT(*) AS ProductCount,
        AVG(Price) AS AvgPrice,
        SUM(StockQty) AS TotalStock
    FROM Products
    GROUP BY Category

Filter groups with HAVING:
    SELECT State, COUNT(*) AS CustomerCount
    FROM Customers
    GROUP BY State
    HAVING COUNT(*) > 10


JOINS
-----

Inner join (matching records only):
    SELECT
        o.OrderID,
        o.OrderDate,
        c.CompanyName,
        c.ContactName
    FROM Orders o
    INNER JOIN Customers c ON o.CustomerID = c.CustomerID

Left join (all from left, matching from right):
    SELECT
        c.CustomerID,
        c.CompanyName,
        COUNT(o.OrderID) AS OrderCount
    FROM Customers c
    LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
    GROUP BY c.CustomerID, c.CompanyName

Multi-table join:
    SELECT
        o.OrderID,
        c.CompanyName,
        p.ProductName,
        od.Quantity,
        od.UnitPrice
    FROM Orders o
    INNER JOIN Customers c ON o.CustomerID = c.CustomerID
    INNER JOIN OrderDetails od ON o.OrderID = od.OrderID
    INNER JOIN Products p ON od.ProductID = p.ProductID


DATE QUERIES
------------

Records from today:
    SELECT * FROM Orders WHERE CAST(OrderDate AS DATE) = CAST(GETDATE() AS DATE)

Records from this year:
    SELECT * FROM Orders WHERE YEAR(OrderDate) = YEAR(GETDATE())

Records from last 30 days:
    SELECT * FROM Orders WHERE OrderDate >= DATEADD(DAY, -30, GETDATE())

Records for specific month:
    SELECT * FROM Orders
    WHERE OrderDate >= '2024-07-01' AND OrderDate < '2024-08-01'

Group by month:
    SELECT
        YEAR(OrderDate) AS Year,
        MONTH(OrderDate) AS Month,
        COUNT(*) AS OrderCount,
        SUM(Total) AS TotalSales
    FROM Orders
    GROUP BY YEAR(OrderDate), MONTH(OrderDate)
    ORDER BY Year, Month


PAGINATION
----------

Basic pagination (SQL Server 2012+):
    SELECT * FROM Products
    ORDER BY ProductID
    OFFSET 20 ROWS
    FETCH NEXT 10 ROWS ONLY

With total count:
    SELECT
        *,
        COUNT(*) OVER() AS TotalCount
    FROM Products
    ORDER BY ProductID
    OFFSET 0 ROWS
    FETCH NEXT 10 ROWS ONLY


COMMON BUSINESS PATTERNS
------------------------

Customer lookup by name:
    SELECT CustomerID, CompanyName, ContactName, Phone, Email
    FROM Customers
    WHERE CompanyName LIKE '%acme%' OR ContactName LIKE '%smith%'
    ORDER BY CompanyName

Open invoices over threshold:
    SELECT
        i.InvoiceID,
        c.CompanyName,
        i.InvoiceDate,
        i.Amount,
        DATEDIFF(DAY, i.DueDate, GETDATE()) AS DaysOverdue
    FROM Invoices i
    INNER JOIN Customers c ON i.CustomerID = c.CustomerID
    WHERE i.Status = 'Open' AND i.Amount > 1000
    ORDER BY i.Amount DESC

Order history for customer:
    SELECT
        OrderID,
        OrderDate,
        Total,
        Status,
        ShipDate
    FROM Orders
    WHERE CustomerID = 'CUST001'
    ORDER BY OrderDate DESC

Low stock inventory:
    SELECT
        ProductID,
        ProductName,
        QuantityInStock,
        ReorderLevel,
        (ReorderLevel - QuantityInStock) AS UnitsNeeded
    FROM Products
    WHERE QuantityInStock < ReorderLevel
    ORDER BY UnitsNeeded DESC

Sales by region:
    SELECT
        Region,
        COUNT(*) AS OrderCount,
        SUM(Total) AS TotalSales,
        AVG(Total) AS AvgOrderValue
    FROM Orders
    GROUP BY Region
    ORDER BY TotalSales DESC


ADVANCED PATTERNS
-----------------

Top N per group (ranking):
    WITH RankedProducts AS (
        SELECT
            Category,
            ProductName,
            Price,
            ROW_NUMBER() OVER (PARTITION BY Category ORDER BY Price DESC) AS Rank
        FROM Products
    )
    SELECT * FROM RankedProducts WHERE Rank <= 3

Running totals:
    SELECT
        OrderDate,
        Total,
        SUM(Total) OVER (ORDER BY OrderDate) AS RunningTotal
    FROM Orders

Year-over-year comparison:
    SELECT
        MONTH(OrderDate) AS Month,
        SUM(CASE WHEN YEAR(OrderDate) = 2024 THEN Total ELSE 0 END) AS Sales2024,
        SUM(CASE WHEN YEAR(OrderDate) = 2023 THEN Total ELSE 0 END) AS Sales2023
    FROM Orders
    WHERE YEAR(OrderDate) IN (2023, 2024)
    GROUP BY MONTH(OrderDate)
    ORDER BY Month

Find duplicates:
    SELECT Email, COUNT(*) AS Count
    FROM Customers
    WHERE Email IS NOT NULL
    GROUP BY Email
    HAVING COUNT(*) > 1


TIPS FOR SUCCESS
----------------

1. Start simple, add complexity incrementally
2. Use COUNT(*) first to estimate result size
3. Use TOP clause to limit large result sets during exploration
4. Check table schemas with describe_table before querying
5. Use parameterized queries for user-supplied values
6. Test date formats with small queries first
7. Use aliases for readability in complex joins
8. Consider using transactions for multi-statement operations
"""


@mcp.resource("mssql://query_examples")
def get_query_examples() -> str:
    """Example T-SQL queries for common patterns.

    Provides a collection of example queries demonstrating common patterns
    for data retrieval, filtering, sorting, grouping, joins, and date handling
    in SQL Server databases.
    """
    return QUERY_EXAMPLES
