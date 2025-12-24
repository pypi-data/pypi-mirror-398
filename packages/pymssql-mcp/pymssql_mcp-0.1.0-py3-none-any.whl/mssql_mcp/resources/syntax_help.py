"""T-SQL syntax reference resource for mssql-mcp."""

from ..app import mcp

TSQL_SYNTAX = """
T-SQL Quick Reference for AI Assistants
=======================================

BASIC QUERIES
-------------

SELECT [TOP n] columns
FROM table
[WHERE conditions]
[ORDER BY columns]

Examples:
  SELECT * FROM Customers WHERE State = 'CA'
  SELECT TOP 10 Name, Email FROM Users ORDER BY CreatedAt DESC
  SELECT COUNT(*) FROM Orders WHERE Status = 'Pending'

FILTERING (WHERE clause)
------------------------

Comparison:
  = , <> (not equal), < , > , <= , >=

Pattern Matching:
  LIKE 'pattern'
    'A%'     - starts with A
    '%A'     - ends with A
    '%A%'    - contains A
    'A_B'    - A, any single char, B

Range:
  BETWEEN value1 AND value2
  IN (value1, value2, ...)

NULL:
  IS NULL
  IS NOT NULL

Logical:
  AND, OR, NOT

JOINS
-----

INNER JOIN: Only matching rows
  SELECT * FROM Orders o
  INNER JOIN Customers c ON o.CustomerID = c.ID

LEFT JOIN: All from left, matching from right
  SELECT * FROM Customers c
  LEFT JOIN Orders o ON c.ID = o.CustomerID

RIGHT JOIN: All from right, matching from left
  SELECT * FROM Orders o
  RIGHT JOIN Customers c ON o.CustomerID = c.ID

FULL OUTER JOIN: All rows from both tables
  SELECT * FROM TableA a
  FULL OUTER JOIN TableB b ON a.ID = b.AID

AGGREGATION
-----------

Functions:
  COUNT(*), COUNT(column), SUM(column), AVG(column), MIN(column), MAX(column)

GROUP BY:
  SELECT Status, COUNT(*) as Count
  FROM Orders
  GROUP BY Status

HAVING (filter groups):
  SELECT Status, COUNT(*) as Count
  FROM Orders
  GROUP BY Status
  HAVING COUNT(*) > 10

COMMON FUNCTIONS
----------------

String:
  LEN(str)                  - Length of string
  UPPER(str), LOWER(str)    - Case conversion
  TRIM(str)                 - Remove leading/trailing spaces
  LTRIM(str), RTRIM(str)    - Remove left/right spaces
  SUBSTRING(str, start, len) - Extract substring (1-based)
  CONCAT(s1, s2, ...)       - Concatenate strings
  REPLACE(str, find, repl)  - Replace occurrences
  CHARINDEX(find, str)      - Find position (0 if not found)
  LEFT(str, n), RIGHT(str, n) - First/last n characters

Date/Time:
  GETDATE()                 - Current date/time
  GETUTCDATE()              - Current UTC date/time
  DATEADD(part, n, date)    - Add interval to date
  DATEDIFF(part, d1, d2)    - Difference between dates
  YEAR(date), MONTH(date), DAY(date) - Extract parts
  FORMAT(date, 'format')    - Format date as string

  Date parts: year, quarter, month, day, week, hour, minute, second

Conversion:
  CAST(value AS type)       - Convert to type
  CONVERT(type, value)      - Convert with optional style
  ISNULL(value, default)    - Return default if null
  COALESCE(v1, v2, ...)     - Return first non-null
  NULLIF(v1, v2)            - Return null if values equal

Conditional:
  CASE WHEN cond THEN val ELSE val END
  IIF(condition, true_val, false_val)

DATA TYPES
----------

Numeric:
  INT, BIGINT, SMALLINT, TINYINT  - Integers
  DECIMAL(p,s), NUMERIC(p,s)      - Exact decimal
  FLOAT, REAL                      - Floating point
  MONEY, SMALLMONEY               - Currency

String:
  CHAR(n), VARCHAR(n)        - ASCII strings (n = max length)
  NCHAR(n), NVARCHAR(n)      - Unicode strings
  VARCHAR(MAX), NVARCHAR(MAX) - Large strings (up to 2GB)
  TEXT, NTEXT                 - Legacy large text (deprecated)

Date/Time:
  DATE                - Date only (YYYY-MM-DD)
  TIME                - Time only (HH:MM:SS.nnnnnnn)
  DATETIME            - Date and time (3.33ms precision)
  DATETIME2           - Date and time (100ns precision)
  DATETIMEOFFSET      - Date/time with timezone
  SMALLDATETIME       - Date/time (1 minute precision)

Binary:
  BINARY(n), VARBINARY(n)    - Fixed/variable binary
  VARBINARY(MAX)             - Large binary (up to 2GB)
  IMAGE                      - Legacy binary (deprecated)

Other:
  BIT                        - Boolean (0, 1, NULL)
  UNIQUEIDENTIFIER           - GUID/UUID
  XML                        - XML data
  JSON                       - JSON data (stored as NVARCHAR)

COMMON PATTERNS
---------------

Pagination:
  SELECT * FROM Table
  ORDER BY ID
  OFFSET 10 ROWS
  FETCH NEXT 10 ROWS ONLY

Check if exists:
  IF EXISTS (SELECT 1 FROM Table WHERE condition)
    ...

Upsert (Merge):
  MERGE INTO Target t
  USING Source s ON t.ID = s.ID
  WHEN MATCHED THEN UPDATE SET ...
  WHEN NOT MATCHED THEN INSERT ...

Common Table Expression (CTE):
  WITH CTE AS (
    SELECT ... FROM ...
  )
  SELECT * FROM CTE

TIPS FOR AI-GENERATED QUERIES
-----------------------------

1. Always use parameterized queries for user input (%s placeholders)
2. Use TOP clause to limit results for large tables
3. Prefer specific column names over SELECT *
4. Include WHERE clause in UPDATE/DELETE to avoid affecting all rows
5. Use schema prefix for clarity (dbo.TableName)
6. Check column nullability before comparisons
7. Use NOLOCK hint with caution (dirty reads possible)
8. Consider using transactions for multi-statement operations
"""


@mcp.resource("mssql://tsql_syntax")
def get_tsql_syntax() -> str:
    """T-SQL syntax reference for SQL Server queries.

    Provides a quick reference for T-SQL query syntax,
    including SELECT, WHERE, JOIN, aggregation functions,
    and common data types.
    """
    return TSQL_SYNTAX
