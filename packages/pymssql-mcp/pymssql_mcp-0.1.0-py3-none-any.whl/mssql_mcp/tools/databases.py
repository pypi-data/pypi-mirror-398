"""Database discovery and switching tools for mssql-mcp."""

import logging
from typing import Any

from ..app import mcp
from ..server import get_connection_manager

logger = logging.getLogger(__name__)

# System databases that are always excluded from listing
SYSTEM_DATABASES = {"master", "tempdb", "model", "msdb"}


@mcp.tool()
def list_databases(include_system: bool = False) -> dict[str, Any]:
    """List all available databases on the SQL Server.

    Queries sys.databases to discover accessible databases. System databases
    (master, tempdb, model, msdb) are excluded by default. Databases in the
    blocklist (MSSQL_BLOCKED_DATABASES) are always excluded.

    Args:
        include_system: If True, include system databases in the list

    Returns:
        Dictionary with:
        - databases: List of available database names
        - current_database: The currently active database
        - count: Number of databases returned
        - blocked_count: Number of databases hidden due to blocklist
    """
    try:
        manager = get_connection_manager()
        config = manager.config
        blocked_databases = config.blocked_databases

        # Query all databases
        query = """
            SELECT name, database_id, state_desc
            FROM sys.databases
            WHERE state_desc = 'ONLINE'
            ORDER BY name
        """
        rows = manager.execute_query(query)

        # Filter databases
        databases = []
        blocked_count = 0

        for row in rows:
            db_name = row["name"]
            db_name_lower = db_name.lower()

            # Check if blocked
            if db_name_lower in blocked_databases:
                blocked_count += 1
                continue

            # Check if system database
            if not include_system and db_name_lower in SYSTEM_DATABASES:
                continue

            databases.append(db_name)

        # Get current database
        current_db_query = "SELECT DB_NAME() AS current_database"
        current_db_result = manager.execute_query(current_db_query)
        current_database = current_db_result[0]["current_database"] if current_db_result else None

        return {
            "databases": databases,
            "current_database": current_database,
            "count": len(databases),
            "blocked_count": blocked_count,
        }

    except Exception as e:
        logger.error(f"Error listing databases: {e}")
        return {"error": str(e)}


@mcp.tool()
def switch_database(database_name: str) -> dict[str, Any]:
    """Switch the active database context.

    Changes the current database using the USE statement. The database must
    exist, be online, and not be in the blocklist (MSSQL_BLOCKED_DATABASES).

    Args:
        database_name: Name of the database to switch to

    Returns:
        Dictionary with:
        - status: "switched" on success, "error" on failure
        - database: The new active database name
        - previous_database: The previously active database
        - error: Error message if switch failed
    """
    try:
        manager = get_connection_manager()
        config = manager.config
        blocked_databases = config.blocked_databases

        # Check if database is blocked
        if database_name.lower() in blocked_databases:
            return {
                "status": "error",
                "error": f"Access to database '{database_name}' is not allowed",
                "database": database_name,
            }

        # Get current database before switching
        current_db_query = "SELECT DB_NAME() AS current_database"
        current_db_result = manager.execute_query(current_db_query)
        previous_database = current_db_result[0]["current_database"] if current_db_result else None

        # Switch database using USE statement
        # Note: USE cannot be parameterized, but we validate the name exists first
        # by checking sys.databases
        check_query = "SELECT name FROM sys.databases WHERE name = %s AND state_desc = 'ONLINE'"
        check_result = manager.execute_query(check_query, (database_name,))

        if not check_result:
            return {
                "status": "error",
                "error": f"Database '{database_name}' does not exist or is not online",
                "database": database_name,
            }

        # Execute USE statement (database name is validated, use bracket quoting for safety)
        use_query = f"USE [{database_name}]"
        manager.execute_query(use_query)

        # Verify the switch
        verify_result = manager.execute_query(current_db_query)
        new_database = verify_result[0]["current_database"] if verify_result else None

        return {
            "status": "switched",
            "database": new_database,
            "previous_database": previous_database,
        }

    except Exception as e:
        logger.error(f"Error switching database: {e}")
        return {"error": str(e), "database": database_name}
