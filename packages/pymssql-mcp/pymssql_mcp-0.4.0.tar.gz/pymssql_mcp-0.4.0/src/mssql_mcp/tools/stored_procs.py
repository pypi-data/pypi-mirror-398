"""Stored procedure tools for mssql-mcp."""

import logging
from typing import Any

from ..app import mcp
from ..connection import QueryError
from ..server import get_connection_manager

logger = logging.getLogger(__name__)


@mcp.tool()
def list_stored_procs(
    schema: str | None = None,
    pattern: str | None = None,
) -> dict[str, Any]:
    """List available stored procedures in the database.

    Args:
        schema: Filter by schema name (e.g., 'dbo')
        pattern: Filter by name pattern using SQL LIKE syntax (e.g., 'sp_%', '%User%')

    Returns:
        Dictionary with:
        - procedures: List of procedure info (schema, name, created, modified)
        - count: Number of procedures found
    """
    try:
        manager = get_connection_manager()

        query = """
            SELECT
                ROUTINE_SCHEMA as [schema],
                ROUTINE_NAME as [name],
                CREATED as [created],
                LAST_ALTERED as [modified]
            FROM INFORMATION_SCHEMA.ROUTINES
            WHERE ROUTINE_TYPE = 'PROCEDURE'
                AND ROUTINE_CATALOG = DB_NAME()
        """

        params: list[Any] = []

        if schema:
            query += " AND ROUTINE_SCHEMA = %s"
            params.append(schema)

        if pattern:
            query += " AND ROUTINE_NAME LIKE %s"
            params.append(pattern)

        query += " ORDER BY ROUTINE_SCHEMA, ROUTINE_NAME"

        rows = manager.execute_query(query, tuple(params) if params else None)

        procedures = [
            {
                "schema": row["schema"],
                "name": row["name"],
                "created": row["created"].isoformat() if row["created"] else None,
                "modified": row["modified"].isoformat() if row["modified"] else None,
            }
            for row in rows
        ]

        return {
            "procedures": procedures,
            "count": len(procedures),
        }

    except Exception as e:
        logger.error(f"Error listing stored procedures: {e}")
        return {"error": str(e)}


@mcp.tool()
def describe_stored_proc(procedure: str) -> dict[str, Any]:
    """Get parameter information for a stored procedure.

    Args:
        procedure: Procedure name, optionally with schema (e.g., 'dbo.sp_GetUser' or 'sp_GetUser')

    Returns:
        Dictionary with:
        - procedure: Full procedure name (schema.name)
        - parameters: List of parameter info (name, type, direction, etc.)
    """
    try:
        manager = get_connection_manager()

        # Parse schema.procedure format
        if "." in procedure:
            parts = procedure.split(".", 1)
            schema = parts[0]
            proc_name = parts[1]
        else:
            schema = "dbo"
            proc_name = procedure

        query = """
            SELECT
                PARAMETER_NAME as [name],
                DATA_TYPE as [type],
                PARAMETER_MODE as [direction],
                CHARACTER_MAXIMUM_LENGTH as [max_length],
                NUMERIC_PRECISION as [precision],
                NUMERIC_SCALE as [scale],
                ORDINAL_POSITION as [position]
            FROM INFORMATION_SCHEMA.PARAMETERS
            WHERE SPECIFIC_SCHEMA = %s
                AND SPECIFIC_NAME = %s
            ORDER BY ORDINAL_POSITION
        """

        rows = manager.execute_query(query, (schema, proc_name))

        parameters = []
        for row in rows:
            param_info: dict[str, Any] = {
                "name": row["name"] or "(return value)",
                "type": row["type"],
                "direction": row["direction"] or "IN",
            }
            if row["max_length"]:
                param_info["max_length"] = row["max_length"]
            if row["precision"]:
                param_info["precision"] = row["precision"]
            if row["scale"]:
                param_info["scale"] = row["scale"]
            parameters.append(param_info)

        return {
            "procedure": f"{schema}.{proc_name}",
            "parameters": parameters,
        }

    except Exception as e:
        logger.error(f"Error describing stored procedure {procedure}: {e}")
        return {"error": str(e)}


@mcp.tool()
def call_stored_proc(
    procedure: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a stored procedure.

    Args:
        procedure: Procedure name, optionally with schema (e.g., 'dbo.sp_GetUser' or 'sp_GetUser')
        params: Input parameter values as dictionary (parameter names without @)

    Returns:
        Dictionary with:
        - procedure: Full procedure name
        - result_sets: List of result sets (each is a list of row dictionaries)
        - status: 'success' or error
    """
    try:
        manager = get_connection_manager()
        config = manager.config

        # Check read-only mode
        if config.read_only:
            return {"error": "Stored procedure execution disabled in read-only mode"}

        # Parse schema.procedure format
        if "." in procedure:
            parts = procedure.split(".", 1)
            schema = parts[0]
            proc_name = parts[1]
        else:
            schema = "dbo"
            proc_name = procedure

        full_name = f"{schema}.{proc_name}"

        # Build parameter tuple
        param_values = tuple(params.values()) if params else None

        # Execute stored procedure
        results = manager.call_stored_proc(full_name, param_values)

        return {
            "status": "success",
            "procedure": full_name,
            "result_sets": [results] if results else [],
            "row_count": len(results) if results else 0,
        }

    except QueryError as e:
        logger.error(f"Error calling stored procedure {procedure}: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error calling stored procedure {procedure}: {e}")
        return {"error": str(e)}
