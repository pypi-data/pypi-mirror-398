"""Data export tools for mssql-mcp."""

import csv
import json
import logging
from pathlib import Path
from typing import Any

from ..app import mcp
from ..server import get_connection_manager
from ..utils.safety import SQLValidator

logger = logging.getLogger(__name__)


@mcp.tool()
def export_to_json(query: str, filename: str) -> dict[str, Any]:
    """Export query results to a JSON file.

    Args:
        query: SQL SELECT query to execute
        filename: Output filename (relative or absolute path)

    Returns:
        Dictionary with:
        - status: 'success' or error
        - path: Absolute path to created file
        - row_count: Number of rows exported
        - file_size: Size of created file in bytes
    """
    try:
        manager = get_connection_manager()
        config = manager.config

        # Create validator
        validator = SQLValidator(
            blocked_commands=config.blocked_commands,
            read_only=True,
            allowed_schemas=config.allowed_schemas if config.allowed_schemas else None,
        )

        # Validate query is SELECT-only
        if not validator.is_select_only(query):
            return {
                "error": "Only SELECT queries are allowed for export",
                "query": query,
            }

        # Check blocked commands
        is_valid, error = validator.validate(query)
        if not is_valid:
            return {"error": error, "query": query}

        # Execute query (no row limit for export)
        rows = manager.execute_query(query)

        # Prepare output path
        path = Path(filename)
        if not path.is_absolute():
            path = Path.cwd() / path

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON file
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, default=str)

        return {
            "status": "success",
            "path": str(path.absolute()),
            "row_count": len(rows),
            "file_size": path.stat().st_size,
        }

    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        return {"error": str(e)}


@mcp.tool()
def export_to_csv(
    query: str,
    filename: str,
    delimiter: str = ",",
) -> dict[str, Any]:
    """Export query results to a CSV file.

    Args:
        query: SQL SELECT query to execute
        filename: Output filename (relative or absolute path)
        delimiter: Field delimiter (default: comma)

    Returns:
        Dictionary with:
        - status: 'success' or error
        - path: Absolute path to created file
        - row_count: Number of rows exported
        - file_size: Size of created file in bytes
    """
    try:
        manager = get_connection_manager()
        config = manager.config

        # Create validator
        validator = SQLValidator(
            blocked_commands=config.blocked_commands,
            read_only=True,
            allowed_schemas=config.allowed_schemas if config.allowed_schemas else None,
        )

        # Validate query is SELECT-only
        if not validator.is_select_only(query):
            return {
                "error": "Only SELECT queries are allowed for export",
                "query": query,
            }

        # Check blocked commands
        is_valid, error = validator.validate(query)
        if not is_valid:
            return {"error": error, "query": query}

        # Execute query (no row limit for export)
        rows = manager.execute_query(query)

        # Prepare output path
        path = Path(filename)
        if not path.is_absolute():
            path = Path.cwd() / path

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Handle empty results
        if not rows:
            # Create empty file with just a newline
            path.write_text("")
            return {
                "status": "success",
                "path": str(path.absolute()),
                "row_count": 0,
                "file_size": 0,
            }

        # Write CSV file
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter=delimiter)
            writer.writeheader()
            writer.writerows(rows)

        return {
            "status": "success",
            "path": str(path.absolute()),
            "row_count": len(rows),
            "file_size": path.stat().st_size,
        }

    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        return {"error": str(e)}
