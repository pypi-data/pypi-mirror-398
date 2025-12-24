"""Query execution tools for mssql-mcp."""

import logging
from typing import Any

from ..app import mcp
from ..server import get_connection_manager
from ..utils.safety import SQLValidator

logger = logging.getLogger(__name__)


@mcp.tool()
def execute_query(query: str, max_rows: int | None = None) -> dict[str, Any]:
    """Execute a read-only SQL query and return results.

    Only SELECT statements are allowed. The query will have a row limit applied
    automatically if not specified.

    Args:
        query: SQL SELECT statement to execute
        max_rows: Maximum rows to return (overrides default, capped by MSSQL_MAX_ROWS)

    Returns:
        Dictionary with:
        - query: The original query
        - executed_query: The query that was actually executed (may include TOP)
        - columns: List of column names
        - rows: List of row dictionaries
        - row_count: Number of rows returned
        - max_rows: The effective row limit applied
    """
    try:
        manager = get_connection_manager()
        config = manager.config

        # Create validator
        validator = SQLValidator(
            blocked_commands=config.blocked_commands,
            read_only=True,  # execute_query is always read-only
            allowed_schemas=config.allowed_schemas if config.allowed_schemas else None,
        )

        # Validate query is SELECT-only
        if not validator.is_select_only(query):
            return {
                "error": "Only SELECT queries are allowed. Use other tools for data modification.",
                "query": query,
            }

        # Check blocked commands
        is_valid, error = validator.validate(query)
        if not is_valid:
            return {"error": error, "query": query}

        # Determine effective row limit
        effective_max_rows = min(max_rows or config.max_rows, config.max_rows)

        # Inject row limit
        executed_query = validator.inject_row_limit(query, effective_max_rows)

        # Execute query
        rows = manager.execute_query(executed_query)

        # Extract column names from first row or return empty
        columns: list[str] = []
        if rows:
            columns = list(rows[0].keys())

        return {
            "query": query,
            "executed_query": executed_query,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "max_rows": effective_max_rows,
        }

    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return {"error": str(e), "query": query}


@mcp.tool()
def validate_query(query: str) -> dict[str, Any]:
    """Check if a query is safe to execute without running it.

    Validates the query against:
    - Statement type (SELECT, INSERT, UPDATE, DELETE, DDL, EXEC)
    - Blocked commands list
    - Read-only mode compliance
    - Potential issues (missing WHERE clause, unbounded SELECT)

    Args:
        query: SQL statement to validate

    Returns:
        Dictionary with:
        - query: The original query
        - valid: Whether the query is valid
        - statement_type: Type of SQL statement
        - warnings: List of warning messages
        - suggestions: List of suggested improvements
        - error: Error message if invalid
    """
    try:
        manager = get_connection_manager()
        config = manager.config

        # Create validator
        validator = SQLValidator(
            blocked_commands=config.blocked_commands,
            read_only=config.read_only,
            allowed_schemas=config.allowed_schemas if config.allowed_schemas else None,
        )

        # Detect statement type
        stmt_type = validator.detect_statement_type(query)

        # Validate
        is_valid, error = validator.validate(query)

        # Get warnings
        warnings = validator.get_warnings(query)

        # Build suggestions
        suggestions: list[str] = []
        if stmt_type.value == "SELECT" and "TOP" not in query.upper():
            suggestions.append("Consider using TOP clause to limit results")
        if stmt_type.value in ("UPDATE", "DELETE") and "WHERE" not in query.upper():
            suggestions.append("Add WHERE clause to target specific rows")

        result: dict[str, Any] = {
            "query": query,
            "valid": is_valid,
            "statement_type": stmt_type.value,
            "warnings": warnings,
            "suggestions": suggestions,
        }

        if not is_valid:
            result["error"] = error

        return result

    except Exception as e:
        logger.error(f"Error validating query: {e}")
        return {"error": str(e), "query": query}
