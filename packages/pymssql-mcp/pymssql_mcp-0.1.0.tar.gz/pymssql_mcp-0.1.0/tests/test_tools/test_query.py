"""Tests for query execution tools."""

from unittest.mock import MagicMock, patch

import pytest


class TestExecuteQuery:
    """Tests for execute_query tool."""

    @pytest.fixture
    def mock_manager(self, mock_config, sample_rows):
        """Create a mock connection manager."""
        manager = MagicMock()
        manager.config = mock_config
        manager.execute_query.return_value = sample_rows
        return manager

    def test_execute_query_success(self, mock_manager, sample_rows):
        """Test successful query execution."""
        with patch("mssql_mcp.tools.query.get_connection_manager", return_value=mock_manager):
            from mssql_mcp.tools.query import execute_query

            result = execute_query("SELECT * FROM Users")

            assert "error" not in result
            assert result["row_count"] == 3
            assert result["rows"] == sample_rows
            assert "columns" in result

    def test_execute_query_non_select_rejected(self, mock_manager):
        """Test non-SELECT queries are rejected."""
        with patch("mssql_mcp.tools.query.get_connection_manager", return_value=mock_manager):
            from mssql_mcp.tools.query import execute_query

            result = execute_query("INSERT INTO Users VALUES (1)")

            assert "error" in result
            assert "SELECT" in result["error"]

    def test_execute_query_blocked_command(self, mock_manager):
        """Test non-SELECT commands are rejected (execute_query is read-only)."""
        # Note: execute_query only allows SELECT queries, so DROP is rejected
        # as a non-SELECT query, not via the blocked commands list
        with patch("mssql_mcp.tools.query.get_connection_manager", return_value=mock_manager):
            from mssql_mcp.tools.query import execute_query

            result = execute_query("DROP TABLE Users")

            assert "error" in result
            assert "select" in result["error"].lower()

    def test_execute_query_applies_row_limit(self, mock_manager):
        """Test row limit is applied."""
        with patch("mssql_mcp.tools.query.get_connection_manager", return_value=mock_manager):
            from mssql_mcp.tools.query import execute_query

            execute_query("SELECT * FROM Users", max_rows=50)

            # Check that the executed query has TOP clause
            call_args = mock_manager.execute_query.call_args
            executed_query = call_args[0][0]
            assert "TOP" in executed_query.upper()


class TestValidateQuery:
    """Tests for validate_query tool."""

    @pytest.fixture
    def mock_manager(self, mock_config):
        """Create a mock connection manager."""
        manager = MagicMock()
        manager.config = mock_config
        return manager

    def test_validate_select_valid(self, mock_manager):
        """Test SELECT query validation."""
        with patch("mssql_mcp.tools.query.get_connection_manager", return_value=mock_manager):
            from mssql_mcp.tools.query import validate_query

            result = validate_query("SELECT * FROM Users")

            assert result["valid"] is True
            assert result["statement_type"] == "SELECT"

    def test_validate_insert_valid_when_not_readonly(self, mock_manager):
        """Test INSERT validation when not in read-only mode."""
        mock_manager.config.read_only = False
        with patch("mssql_mcp.tools.query.get_connection_manager", return_value=mock_manager):
            from mssql_mcp.tools.query import validate_query

            result = validate_query("INSERT INTO Users VALUES (1)")

            assert result["valid"] is True
            assert result["statement_type"] == "INSERT"

    def test_validate_insert_invalid_when_readonly(self, mock_manager):
        """Test INSERT validation when in read-only mode."""
        mock_manager.config.read_only = True
        with patch("mssql_mcp.tools.query.get_connection_manager", return_value=mock_manager):
            from mssql_mcp.tools.query import validate_query

            result = validate_query("INSERT INTO Users VALUES (1)")

            assert result["valid"] is False
            assert "error" in result

    def test_validate_drop_blocked(self, mock_manager):
        """Test DROP command is blocked."""
        # Note: mock_config already has DROP, TRUNCATE, ALTER, CREATE blocked
        with patch("mssql_mcp.tools.query.get_connection_manager", return_value=mock_manager):
            from mssql_mcp.tools.query import validate_query

            result = validate_query("DROP TABLE Users")

            assert result["valid"] is False
            assert "error" in result

    def test_validate_includes_warnings(self, mock_manager):
        """Test validation includes warnings."""
        with patch("mssql_mcp.tools.query.get_connection_manager", return_value=mock_manager):
            from mssql_mcp.tools.query import validate_query

            result = validate_query("UPDATE Users SET name = 'test'")

            assert "warnings" in result
            assert len(result["warnings"]) > 0

    def test_validate_includes_suggestions(self, mock_manager):
        """Test validation includes suggestions."""
        with patch("mssql_mcp.tools.query.get_connection_manager", return_value=mock_manager):
            from mssql_mcp.tools.query import validate_query

            result = validate_query("SELECT * FROM Users")

            assert "suggestions" in result
