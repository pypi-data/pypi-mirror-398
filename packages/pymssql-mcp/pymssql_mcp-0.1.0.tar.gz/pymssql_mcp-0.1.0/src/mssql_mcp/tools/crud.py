"""CRUD operation tools for mssql-mcp."""

import logging
from typing import Any

from ..app import mcp
from ..connection import QueryError
from ..server import get_connection_manager
from ..utils.safety import parse_table_name

logger = logging.getLogger(__name__)


def _get_primary_key_columns(schema: str, table: str) -> list[str]:
    """Get primary key column(s) for a table.

    Args:
        schema: Schema name
        table: Table name

    Returns:
        List of primary key column names
    """
    manager = get_connection_manager()

    query = """
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
    rows = manager.execute_query(query, (schema, table))
    return [row["COLUMN_NAME"] for row in rows]


@mcp.tool()
def read_rows(
    table: str,
    id: Any | None = None,
    ids: list[Any] | None = None,
    filter: str | None = None,
    columns: list[str] | None = None,
    max_rows: int | None = None,
) -> dict[str, Any]:
    """Read rows from a table by primary key or filter.

    Provide one of: id (single row), ids (multiple rows), or filter (WHERE clause).

    Args:
        table: Table name (can include schema: 'dbo.Users' or 'Users')
        id: Single primary key value (for composite keys, use filter)
        ids: List of primary key values
        filter: WHERE clause without 'WHERE' keyword (e.g., "status = 'active'")
        columns: List of columns to return (default: all columns)
        max_rows: Maximum rows to return

    Returns:
        Dictionary with:
        - table: Full table name
        - rows: List of row dictionaries
        - count: Number of rows returned
    """
    try:
        manager = get_connection_manager()
        config = manager.config
        schema, table_name = parse_table_name(table)

        # Determine columns
        col_list = ", ".join(columns) if columns else "*"

        # Determine effective row limit
        effective_max_rows = min(max_rows or config.max_rows, config.max_rows)

        # Build query
        params: list[Any] = []

        if id is not None:
            # Single row by primary key
            pk_cols = _get_primary_key_columns(schema, table_name)
            if not pk_cols:
                return {"error": f"No primary key found for table {schema}.{table_name}"}
            query = (
                f"SELECT TOP {effective_max_rows} {col_list} "
                f"FROM [{schema}].[{table_name}] WHERE [{pk_cols[0]}] = %s"
            )
            params = [id]

        elif ids is not None:
            # Multiple rows by primary keys
            pk_cols = _get_primary_key_columns(schema, table_name)
            if not pk_cols:
                return {"error": f"No primary key found for table {schema}.{table_name}"}
            placeholders = ", ".join(["%s"] * len(ids))
            query = (
                f"SELECT TOP {effective_max_rows} {col_list} "
                f"FROM [{schema}].[{table_name}] WHERE [{pk_cols[0]}] IN ({placeholders})"
            )
            params = list(ids)

        elif filter is not None:
            # Custom filter
            # Note: filter params not supported - use execute_query for complex cases
            query = (
                f"SELECT TOP {effective_max_rows} {col_list} "
                f"FROM [{schema}].[{table_name}] WHERE {filter}"
            )

        else:
            # All rows (with limit)
            query = f"SELECT TOP {effective_max_rows} {col_list} FROM [{schema}].[{table_name}]"

        rows = manager.execute_query(query, tuple(params) if params else None)

        return {
            "table": f"{schema}.{table_name}",
            "rows": rows,
            "count": len(rows),
        }

    except Exception as e:
        logger.error(f"Error reading rows from {table}: {e}")
        return {"error": str(e)}


@mcp.tool()
def insert_row(table: str, data: dict[str, Any]) -> dict[str, Any]:
    """Insert a new row into a table.

    Args:
        table: Table name (can include schema: 'dbo.Users' or 'Users')
        data: Dictionary of column names and values to insert

    Returns:
        Dictionary with:
        - status: 'success' or error
        - table: Full table name
        - inserted: The inserted row (including generated identity columns)
    """
    try:
        manager = get_connection_manager()
        config = manager.config

        # Check read-only mode
        if config.read_only:
            return {"error": "Write operations disabled in read-only mode"}

        schema, table_name = parse_table_name(table)

        if not data:
            return {"error": "No data provided for insert"}

        # Build INSERT statement with OUTPUT clause
        cols = ", ".join([f"[{k}]" for k in data])
        placeholders = ", ".join(["%s"] * len(data))
        values = tuple(data.values())

        query = f"""
            INSERT INTO [{schema}].[{table_name}] ({cols})
            OUTPUT INSERTED.*
            VALUES ({placeholders})
        """

        rows = manager.execute_query(query, values)

        # The OUTPUT clause returns the inserted row
        inserted = rows[0] if rows else data

        return {
            "status": "success",
            "table": f"{schema}.{table_name}",
            "inserted": inserted,
        }

    except QueryError as e:
        logger.error(f"Error inserting row into {table}: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error inserting row into {table}: {e}")
        return {"error": str(e)}


@mcp.tool()
def update_row(table: str, id: Any, data: dict[str, Any]) -> dict[str, Any]:
    """Update an existing row by primary key.

    Args:
        table: Table name (can include schema: 'dbo.Users' or 'Users')
        id: Primary key value of the row to update
        data: Dictionary of column names and new values

    Returns:
        Dictionary with:
        - status: 'success' or error
        - table: Full table name
        - updated: The updated row
    """
    try:
        manager = get_connection_manager()
        config = manager.config

        # Check read-only mode
        if config.read_only:
            return {"error": "Write operations disabled in read-only mode"}

        schema, table_name = parse_table_name(table)

        if not data:
            return {"error": "No data provided for update"}

        # Get primary key column
        pk_cols = _get_primary_key_columns(schema, table_name)
        if not pk_cols:
            return {"error": f"No primary key found for table {schema}.{table_name}"}

        # Build UPDATE statement with OUTPUT clause
        set_clauses = ", ".join([f"[{k}] = %s" for k in data])
        params = tuple(data.values()) + (id,)

        query = f"""
            UPDATE [{schema}].[{table_name}]
            SET {set_clauses}
            OUTPUT INSERTED.*
            WHERE [{pk_cols[0]}] = %s
        """

        rows = manager.execute_query(query, params)

        if not rows:
            return {
                "error": f"No row found with {pk_cols[0]} = {id}",
                "table": f"{schema}.{table_name}",
            }

        return {
            "status": "success",
            "table": f"{schema}.{table_name}",
            "updated": rows[0],
        }

    except QueryError as e:
        logger.error(f"Error updating row in {table}: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error updating row in {table}: {e}")
        return {"error": str(e)}


@mcp.tool()
def delete_row(table: str, id: Any) -> dict[str, Any]:
    """Delete a row by primary key.

    Args:
        table: Table name (can include schema: 'dbo.Users' or 'Users')
        id: Primary key value of the row to delete

    Returns:
        Dictionary with:
        - status: 'deleted' or error
        - table: Full table name
        - id: The deleted row's ID
        - rows_affected: Number of rows deleted (should be 1)
    """
    try:
        manager = get_connection_manager()
        config = manager.config

        # Check read-only mode
        if config.read_only:
            return {"error": "Delete operations disabled in read-only mode"}

        schema, table_name = parse_table_name(table)

        # Get primary key column
        pk_cols = _get_primary_key_columns(schema, table_name)
        if not pk_cols:
            return {"error": f"No primary key found for table {schema}.{table_name}"}

        # Build DELETE statement
        query = f"DELETE FROM [{schema}].[{table_name}] WHERE [{pk_cols[0]}] = %s"

        affected = manager.execute_non_query(query, (id,))

        if affected == 0:
            return {
                "error": f"No row found with {pk_cols[0]} = {id}",
                "table": f"{schema}.{table_name}",
            }

        return {
            "status": "deleted",
            "table": f"{schema}.{table_name}",
            "id": id,
            "rows_affected": affected,
        }

    except QueryError as e:
        logger.error(f"Error deleting row from {table}: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error deleting row from {table}: {e}")
        return {"error": str(e)}
