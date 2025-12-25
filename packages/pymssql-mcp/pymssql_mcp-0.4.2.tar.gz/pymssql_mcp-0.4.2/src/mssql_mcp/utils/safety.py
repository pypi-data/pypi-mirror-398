"""SQL validation and safety controls for mssql-mcp."""

import re
from enum import Enum

# Default blocked SQL commands (DDL and dangerous operations)
DEFAULT_BLOCKED_COMMANDS: set[str] = {
    "DROP",
    "TRUNCATE",
    "ALTER",
    "CREATE",
    "GRANT",
    "REVOKE",
    "DENY",
    "BACKUP",
    "RESTORE",
    "KILL",
    "SHUTDOWN",
    "RECONFIGURE",
}

# Commands that modify data (blocked in read-only mode)
WRITE_COMMANDS: set[str] = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "EXEC",
    "EXECUTE",
}

# Commands that are always allowed for reading
READ_COMMANDS: set[str] = {
    "SELECT",
    "WITH",  # CTE prefix
}


class StatementType(Enum):
    """SQL statement type enumeration."""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    DDL = "DDL"
    EXEC = "EXEC"
    OTHER = "OTHER"


class SQLValidator:
    """Validates SQL statements against blocklists and safety rules.

    Provides methods to validate SQL queries, detect statement types,
    enforce read-only mode, and inject row limits.

    Args:
        blocked_commands: List of blocked SQL commands
        read_only: If True, block all write operations
        allowed_schemas: Optional list of allowed schema names
    """

    def __init__(
        self,
        blocked_commands: list[str],
        read_only: bool = False,
        allowed_schemas: list[str] | None = None,
    ) -> None:
        # Combine default blocked commands with user-configured ones
        self._blocked: set[str] = {cmd.upper() for cmd in blocked_commands}
        self._blocked.update(DEFAULT_BLOCKED_COMMANDS)
        self._read_only = read_only
        self._allowed_schemas = [s.lower() for s in allowed_schemas] if allowed_schemas else None

    def _get_first_keyword(self, sql: str) -> str:
        """Extract the first SQL keyword from a statement.

        Handles leading whitespace, comments, and WITH clauses.

        Args:
            sql: SQL statement

        Returns:
            First keyword in uppercase
        """
        # Remove leading whitespace
        sql = sql.strip()

        # Remove single-line comments
        sql = re.sub(r"--[^\n]*\n?", "", sql)

        # Remove multi-line comments
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)

        # Get first word
        sql = sql.strip()
        match = re.match(r"(\w+)", sql, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return ""

    def detect_statement_type(self, sql: str) -> StatementType:
        """Detect the type of SQL statement.

        Args:
            sql: SQL statement

        Returns:
            StatementType enum value
        """
        keyword = self._get_first_keyword(sql)

        if keyword in ("SELECT", "WITH"):
            # WITH could be a CTE followed by SELECT, INSERT, UPDATE, DELETE
            # Check what follows WITH...AS...
            if keyword == "WITH":
                # Find what comes after the CTE
                cte_pattern = r"WITH\s+[\w\s,()]+\s+AS\s*\([^)]+\)\s*(\w+)"
                match = re.search(cte_pattern, sql, re.IGNORECASE | re.DOTALL)
                if match:
                    following = match.group(1).upper()
                    stmt_map = {
                        "SELECT": StatementType.SELECT,
                        "INSERT": StatementType.INSERT,
                        "UPDATE": StatementType.UPDATE,
                        "DELETE": StatementType.DELETE,
                    }
                    if following in stmt_map:
                        return stmt_map[following]
            return StatementType.SELECT

        if keyword == "INSERT":
            return StatementType.INSERT
        if keyword == "UPDATE":
            return StatementType.UPDATE
        if keyword == "DELETE":
            return StatementType.DELETE
        if keyword in ("EXEC", "EXECUTE"):
            return StatementType.EXEC
        if keyword in ("CREATE", "ALTER", "DROP", "TRUNCATE", "GRANT", "REVOKE", "DENY"):
            return StatementType.DDL

        return StatementType.OTHER

    def validate(self, sql: str) -> tuple[bool, str]:
        """Validate a SQL statement against safety rules.

        Checks:
        - Empty query
        - Blocked commands
        - Read-only mode compliance

        Args:
            sql: SQL statement to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "Empty query"

        keyword = self._get_first_keyword(sql)

        # Check blocked commands
        if keyword in self._blocked:
            return False, f"Command '{keyword}' is blocked"

        # Check read-only mode
        if self._read_only and keyword in WRITE_COMMANDS:
            return False, f"Write operation '{keyword}' disabled in read-only mode"

        return True, ""

    def is_select_only(self, sql: str) -> bool:
        """Check if a statement is SELECT-only (read operation).

        Args:
            sql: SQL statement

        Returns:
            True if statement is a SELECT query
        """
        stmt_type = self.detect_statement_type(sql)
        return stmt_type == StatementType.SELECT

    def inject_row_limit(self, sql: str, max_rows: int) -> str:
        """Inject a TOP clause into a SELECT statement if not present.

        Args:
            sql: SQL SELECT statement
            max_rows: Maximum rows to return

        Returns:
            Modified SQL with TOP clause
        """
        sql_stripped = sql.strip()

        # Check if already has TOP clause
        top_pattern = r"\bSELECT\s+TOP\s*[\(\d]"
        if re.search(top_pattern, sql_stripped, re.IGNORECASE):
            return sql_stripped

        # Check if it's a SELECT statement (or WITH...SELECT)
        keyword = self._get_first_keyword(sql_stripped)

        if keyword == "WITH":
            # For CTEs, inject TOP after the SELECT that follows
            # Pattern: WITH ... AS (...) SELECT -> WITH ... AS (...) SELECT TOP N
            cte_select_pattern = r"(\)\s*)(SELECT\s+)"
            replacement = rf"\1SELECT TOP {max_rows} "
            modified = re.sub(
                cte_select_pattern, replacement, sql_stripped, count=1, flags=re.IGNORECASE
            )
            return modified

        if keyword == "SELECT":
            # Simple SELECT - insert TOP after SELECT keyword
            select_pattern = r"^(SELECT\s+)"
            replacement = rf"SELECT TOP {max_rows} "
            modified = re.sub(
                select_pattern, replacement, sql_stripped, count=1, flags=re.IGNORECASE
            )
            return modified

        # Not a SELECT, return as-is
        return sql_stripped

    def validate_table_name(self, table: str) -> tuple[bool, str]:
        """Validate a table name against allowed schemas.

        Args:
            table: Table name (optionally with schema prefix)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not table or not table.strip():
            return False, "Empty table name"

        # Parse schema.table format
        if "." in table:
            parts = table.split(".", 1)
            schema = parts[0].lower()
        else:
            schema = "dbo"

        # Check against allowed schemas
        if self._allowed_schemas and schema not in self._allowed_schemas:
            return False, f"Schema '{schema}' is not in allowed schemas"

        return True, ""

    def get_warnings(self, sql: str) -> list[str]:
        """Generate warnings for potentially problematic queries.

        Args:
            sql: SQL statement

        Returns:
            List of warning messages
        """
        warnings = []
        stmt_type = self.detect_statement_type(sql)

        # Warn on UPDATE/DELETE without WHERE
        if stmt_type in (StatementType.UPDATE, StatementType.DELETE) and not re.search(
            r"\bWHERE\b", sql, re.IGNORECASE
        ):
            warnings.append(f"{stmt_type.value} without WHERE clause will affect all rows")

        # Warn on unbounded SELECT
        if stmt_type == StatementType.SELECT:
            has_top = re.search(r"\bTOP\s*[\(\d]", sql, re.IGNORECASE)
            has_where = re.search(r"\bWHERE\b", sql, re.IGNORECASE)
            if not has_top and not has_where:
                warnings.append("SELECT without TOP or WHERE may return many rows")

        return warnings


def parse_table_name(table: str) -> tuple[str, str]:
    """Parse a table name into schema and table parts.

    Args:
        table: Table name, optionally with schema (e.g., 'dbo.Users' or 'Users')

    Returns:
        Tuple of (schema, table_name)
    """
    if "." in table:
        parts = table.split(".", 1)
        return parts[0], parts[1]
    return "dbo", table
