"""Schema discovery tools for mssql-mcp."""

import logging
from typing import Any

from ..app import mcp
from ..server import get_connection_manager
from ..utils.safety import parse_table_name

logger = logging.getLogger(__name__)


@mcp.tool()
def list_tables(
    schema: str | None = None,
    include_views: bool = True,
    pattern: str | None = None,
) -> dict[str, Any]:
    """List all tables and views in the database.

    Args:
        schema: Filter by schema name (e.g., 'dbo'). If not specified, returns all schemas.
        include_views: Include views in results (default: True)
        pattern: Filter by name pattern using SQL LIKE syntax (e.g., 'Cust%', '%Order%')

    Returns:
        Dictionary with:
        - tables: List of table/view info (schema, name, type)
        - count: Number of results
    """
    try:
        manager = get_connection_manager()

        # Build query with optional filters
        query = """
            SELECT
                TABLE_SCHEMA as [schema],
                TABLE_NAME as [name],
                TABLE_TYPE as [type]
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_CATALOG = DB_NAME()
        """

        params: list[Any] = []

        if schema:
            query += " AND TABLE_SCHEMA = %s"
            params.append(schema)

        if not include_views:
            query += " AND TABLE_TYPE = 'BASE TABLE'"

        if pattern:
            query += " AND TABLE_NAME LIKE %s"
            params.append(pattern)

        query += " ORDER BY TABLE_SCHEMA, TABLE_NAME"

        rows = manager.execute_query(query, tuple(params) if params else None)

        # Convert rows to list of dicts
        tables = [
            {
                "schema": row["schema"],
                "name": row["name"],
                "type": "TABLE" if row["type"] == "BASE TABLE" else "VIEW",
            }
            for row in rows
        ]

        return {
            "tables": tables,
            "count": len(tables),
        }

    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        return {"error": str(e)}


@mcp.tool()
def describe_table(table: str) -> dict[str, Any]:
    """Get detailed column information for a table.

    Retrieves column definitions, primary keys, foreign keys, and indexes.

    Args:
        table: Table name, optionally with schema (e.g., 'dbo.Users' or 'Users').
               Defaults to 'dbo' schema if not specified.

    Returns:
        Dictionary with:
        - table: Full table name (schema.table)
        - columns: List of column info (name, type, nullable, etc.)
        - primary_key: List of primary key column names
        - foreign_keys: List of foreign key relationships
        - indexes: List of index info
    """
    try:
        manager = get_connection_manager()
        schema, table_name = parse_table_name(table)

        # Get columns
        columns_query = """
            SELECT
                COLUMN_NAME as [name],
                DATA_TYPE as [type],
                CHARACTER_MAXIMUM_LENGTH as [max_length],
                NUMERIC_PRECISION as [precision],
                NUMERIC_SCALE as [scale],
                IS_NULLABLE as [nullable],
                COLUMN_DEFAULT as [default_value]
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """
        columns_rows = manager.execute_query(columns_query, (schema, table_name))

        columns = []
        for row in columns_rows:
            col_info: dict[str, Any] = {
                "name": row["name"],
                "type": row["type"],
                "nullable": row["nullable"] == "YES",
            }
            if row["max_length"]:
                col_info["max_length"] = row["max_length"]
            if row["precision"]:
                col_info["precision"] = row["precision"]
            if row["scale"]:
                col_info["scale"] = row["scale"]
            if row["default_value"]:
                col_info["default"] = row["default_value"]
            columns.append(col_info)

        # Get primary key columns
        pk_query = """
            SELECT c.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE c
                ON tc.CONSTRAINT_NAME = c.CONSTRAINT_NAME
                AND tc.TABLE_SCHEMA = c.TABLE_SCHEMA
                AND tc.TABLE_NAME = c.TABLE_NAME
            WHERE tc.TABLE_SCHEMA = %s
                AND tc.TABLE_NAME = %s
                AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
            ORDER BY c.ORDINAL_POSITION
        """
        pk_rows = manager.execute_query(pk_query, (schema, table_name))
        primary_key = [row["COLUMN_NAME"] for row in pk_rows]

        # Get foreign keys
        fk_query = """
            SELECT
                fk.name as constraint_name,
                COL_NAME(fkc.parent_object_id, fkc.parent_column_id) as [column],
                OBJECT_SCHEMA_NAME(fkc.referenced_object_id) as ref_schema,
                OBJECT_NAME(fkc.referenced_object_id) as ref_table,
                COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) as ref_column
            FROM sys.foreign_keys fk
            JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            WHERE fk.parent_object_id = OBJECT_ID(%s)
            ORDER BY fk.name, fkc.constraint_column_id
        """
        fk_rows = manager.execute_query(fk_query, (f"{schema}.{table_name}",))

        foreign_keys = [
            {
                "constraint": row["constraint_name"],
                "column": row["column"],
                "references_table": f"{row['ref_schema']}.{row['ref_table']}",
                "references_column": row["ref_column"],
            }
            for row in fk_rows
        ]

        # Get indexes
        idx_query = """
            SELECT
                i.name as index_name,
                i.type_desc as [type],
                i.is_unique,
                i.is_primary_key,
                STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) as [columns]
            FROM sys.indexes i
            JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE i.object_id = OBJECT_ID(%s)
                AND i.name IS NOT NULL
            GROUP BY i.name, i.type_desc, i.is_unique, i.is_primary_key
            ORDER BY i.name
        """
        idx_rows = manager.execute_query(idx_query, (f"{schema}.{table_name}",))

        indexes = [
            {
                "name": row["index_name"],
                "type": row["type"],
                "is_unique": bool(row["is_unique"]),
                "is_primary_key": bool(row["is_primary_key"]),
                "columns": row["columns"],
            }
            for row in idx_rows
        ]

        return {
            "table": f"{schema}.{table_name}",
            "columns": columns,
            "primary_key": primary_key,
            "foreign_keys": foreign_keys,
            "indexes": indexes,
        }

    except Exception as e:
        logger.error(f"Error describing table {table}: {e}")
        return {"error": str(e)}
