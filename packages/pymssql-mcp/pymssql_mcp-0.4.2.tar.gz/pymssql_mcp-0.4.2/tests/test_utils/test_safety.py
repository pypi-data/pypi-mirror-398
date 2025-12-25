"""Tests for SQL validation and safety controls."""

import pytest

from mssql_mcp.utils.safety import (
    DEFAULT_BLOCKED_COMMANDS,
    SQLValidator,
    StatementType,
    parse_table_name,
)


class TestSQLValidator:
    """Tests for SQLValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a basic validator."""
        return SQLValidator(
            blocked_commands=["DROP", "TRUNCATE"],
            read_only=False,
        )

    @pytest.fixture
    def readonly_validator(self):
        """Create a read-only validator."""
        return SQLValidator(
            blocked_commands=["DROP", "TRUNCATE"],
            read_only=True,
        )

    # Statement type detection tests
    def test_detect_select_statement(self, validator):
        """Test SELECT statement detection."""
        assert validator.detect_statement_type("SELECT * FROM Users") == StatementType.SELECT
        assert validator.detect_statement_type("  SELECT id FROM Users") == StatementType.SELECT

    def test_detect_insert_statement(self, validator):
        """Test INSERT statement detection."""
        result = validator.detect_statement_type("INSERT INTO Users VALUES (1)")
        assert result == StatementType.INSERT

    def test_detect_update_statement(self, validator):
        """Test UPDATE statement detection."""
        result = validator.detect_statement_type("UPDATE Users SET name = 'test'")
        assert result == StatementType.UPDATE

    def test_detect_delete_statement(self, validator):
        """Test DELETE statement detection."""
        result = validator.detect_statement_type("DELETE FROM Users WHERE id = 1")
        assert result == StatementType.DELETE

    def test_detect_ddl_statement(self, validator):
        """Test DDL statement detection."""
        assert validator.detect_statement_type("CREATE TABLE Users (id INT)") == StatementType.DDL
        assert validator.detect_statement_type("ALTER TABLE Users ADD col INT") == StatementType.DDL
        assert validator.detect_statement_type("DROP TABLE Users") == StatementType.DDL

    def test_detect_exec_statement(self, validator):
        """Test EXEC statement detection."""
        assert validator.detect_statement_type("EXEC sp_GetUser 1") == StatementType.EXEC
        assert validator.detect_statement_type("EXECUTE sp_GetUser 1") == StatementType.EXEC

    def test_detect_with_cte(self, validator):
        """Test CTE (WITH) statement detection."""
        cte_select = "WITH cte AS (SELECT * FROM Users) SELECT * FROM cte"
        assert validator.detect_statement_type(cte_select) == StatementType.SELECT

    # Validation tests
    def test_validate_empty_query(self, validator):
        """Test validation of empty query."""
        is_valid, error = validator.validate("")
        assert is_valid is False
        assert "Empty" in error

    def test_validate_blocked_command(self, validator):
        """Test blocked command is rejected."""
        is_valid, error = validator.validate("DROP TABLE Users")
        assert is_valid is False
        assert "blocked" in error.lower()

    def test_validate_select_allowed(self, validator):
        """Test SELECT is allowed."""
        is_valid, error = validator.validate("SELECT * FROM Users")
        assert is_valid is True
        assert error == ""

    def test_validate_insert_allowed_when_not_readonly(self, validator):
        """Test INSERT is allowed when not in read-only mode."""
        is_valid, error = validator.validate("INSERT INTO Users VALUES (1)")
        assert is_valid is True

    def test_validate_insert_blocked_in_readonly(self, readonly_validator):
        """Test INSERT is blocked in read-only mode."""
        is_valid, error = readonly_validator.validate("INSERT INTO Users VALUES (1)")
        assert is_valid is False
        assert "read-only" in error.lower()

    def test_validate_update_blocked_in_readonly(self, readonly_validator):
        """Test UPDATE is blocked in read-only mode."""
        is_valid, error = readonly_validator.validate("UPDATE Users SET name = 'test'")
        assert is_valid is False
        assert "read-only" in error.lower()

    def test_validate_delete_blocked_in_readonly(self, readonly_validator):
        """Test DELETE is blocked in read-only mode."""
        is_valid, error = readonly_validator.validate("DELETE FROM Users WHERE id = 1")
        assert is_valid is False
        assert "read-only" in error.lower()

    # is_select_only tests
    def test_is_select_only_true(self, validator):
        """Test is_select_only returns True for SELECT."""
        assert validator.is_select_only("SELECT * FROM Users") is True

    def test_is_select_only_false_for_insert(self, validator):
        """Test is_select_only returns False for INSERT."""
        assert validator.is_select_only("INSERT INTO Users VALUES (1)") is False

    # inject_row_limit tests
    def test_inject_row_limit_adds_top(self, validator):
        """Test TOP clause is added."""
        result = validator.inject_row_limit("SELECT * FROM Users", 100)
        assert "TOP 100" in result.upper()

    def test_inject_row_limit_preserves_existing_top(self, validator):
        """Test existing TOP clause is preserved."""
        result = validator.inject_row_limit("SELECT TOP 50 * FROM Users", 100)
        assert "TOP 50" in result.upper()
        assert result.upper().count("TOP") == 1

    def test_inject_row_limit_handles_cte(self, validator):
        """Test row limit injection in CTE."""
        cte = "WITH cte AS (SELECT * FROM Users) SELECT * FROM cte"
        result = validator.inject_row_limit(cte, 100)
        assert "TOP 100" in result.upper()

    # Warnings tests
    def test_warnings_update_without_where(self, validator):
        """Test warning for UPDATE without WHERE."""
        warnings = validator.get_warnings("UPDATE Users SET name = 'test'")
        assert len(warnings) == 1
        assert "WHERE" in warnings[0]

    def test_warnings_delete_without_where(self, validator):
        """Test warning for DELETE without WHERE."""
        warnings = validator.get_warnings("DELETE FROM Users")
        assert len(warnings) == 1
        assert "WHERE" in warnings[0]

    def test_warnings_unbounded_select(self, validator):
        """Test warning for SELECT without TOP or WHERE."""
        warnings = validator.get_warnings("SELECT * FROM Users")
        assert len(warnings) == 1
        assert "TOP" in warnings[0] or "WHERE" in warnings[0]

    def test_no_warnings_for_bounded_select(self, validator):
        """Test no warning for SELECT with TOP."""
        warnings = validator.get_warnings("SELECT TOP 10 * FROM Users")
        assert len(warnings) == 0

    # validate_table_name tests
    def test_validate_table_name_empty(self, validator):
        """Test empty table name is invalid."""
        is_valid, error = validator.validate_table_name("")
        assert is_valid is False
        assert "Empty" in error

    def test_validate_table_name_simple(self, validator):
        """Test simple table name is valid."""
        is_valid, error = validator.validate_table_name("Users")
        assert is_valid is True

    def test_validate_table_name_with_schema(self, validator):
        """Test schema.table format is valid."""
        is_valid, error = validator.validate_table_name("dbo.Users")
        assert is_valid is True

    def test_validate_table_name_with_allowed_schemas(self):
        """Test schema restriction."""
        validator = SQLValidator(
            blocked_commands=[],
            read_only=False,
            allowed_schemas=["dbo"],
        )
        is_valid, error = validator.validate_table_name("dbo.Users")
        assert is_valid is True

        is_valid, error = validator.validate_table_name("hr.Employees")
        assert is_valid is False
        assert "not in allowed schemas" in error


class TestParseTableName:
    """Tests for parse_table_name helper."""

    def test_simple_table_name(self):
        """Test simple table name defaults to dbo schema."""
        schema, table = parse_table_name("Users")
        assert schema == "dbo"
        assert table == "Users"

    def test_schema_qualified_name(self):
        """Test schema.table format."""
        schema, table = parse_table_name("hr.Employees")
        assert schema == "hr"
        assert table == "Employees"

    def test_dbo_qualified_name(self):
        """Test dbo.table format."""
        schema, table = parse_table_name("dbo.Users")
        assert schema == "dbo"
        assert table == "Users"


class TestDefaultBlockedCommands:
    """Tests for default blocked commands."""

    def test_drop_is_blocked(self):
        """Test DROP is in default blocked commands."""
        assert "DROP" in DEFAULT_BLOCKED_COMMANDS

    def test_truncate_is_blocked(self):
        """Test TRUNCATE is in default blocked commands."""
        assert "TRUNCATE" in DEFAULT_BLOCKED_COMMANDS

    def test_shutdown_is_blocked(self):
        """Test SHUTDOWN is in default blocked commands."""
        assert "SHUTDOWN" in DEFAULT_BLOCKED_COMMANDS
