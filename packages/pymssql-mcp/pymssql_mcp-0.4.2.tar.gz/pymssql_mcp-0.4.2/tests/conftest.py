"""Pytest configuration and fixtures for mssql-mcp tests."""

import os
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mssql_mcp.config import MSSQLConfig


@pytest.fixture
def mock_env() -> Generator[dict[str, str], None, None]:
    """Provide mock environment variables for testing."""
    env_vars = {
        "MSSQL_HOST": "test-host.example.com",
        "MSSQL_USER": "test-user",
        "MSSQL_PASSWORD": "test-password",
        "MSSQL_DATABASE": "TestDB",
        "MSSQL_PORT": "1433",
        "MSSQL_READ_ONLY": "false",
        "MSSQL_MAX_ROWS": "1000",
        "MSSQL_QUERY_TIMEOUT": "60",
        "MSSQL_BLOCKED_COMMANDS": "DROP,TRUNCATE,ALTER,CREATE",
        "MSSQL_AUDIT_ENABLED": "false",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_env_read_only() -> Generator[dict[str, str], None, None]:
    """Provide mock environment variables with read-only mode enabled."""
    env_vars = {
        "MSSQL_HOST": "test-host.example.com",
        "MSSQL_USER": "test-user",
        "MSSQL_PASSWORD": "test-password",
        "MSSQL_DATABASE": "TestDB",
        "MSSQL_PORT": "1433",
        "MSSQL_READ_ONLY": "true",
        "MSSQL_MAX_ROWS": "1000",
        "MSSQL_QUERY_TIMEOUT": "60",
        "MSSQL_BLOCKED_COMMANDS": "DROP,TRUNCATE,ALTER,CREATE",
        "MSSQL_AUDIT_ENABLED": "false",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_config(mock_env: dict[str, str]) -> MSSQLConfig:
    """Provide a test configuration instance."""
    return MSSQLConfig()


@pytest.fixture
def mock_config_read_only(mock_env_read_only: dict[str, str]) -> MSSQLConfig:
    """Provide a read-only test configuration."""
    return MSSQLConfig()


@pytest.fixture
def mock_cursor() -> MagicMock:
    """Provide a mock pymssql cursor."""
    cursor = MagicMock()
    cursor.description = [("id",), ("name",), ("email",)]
    cursor.fetchall.return_value = [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
    ]
    cursor.rowcount = 2
    return cursor


@pytest.fixture
def mock_connection(mock_cursor: MagicMock) -> MagicMock:
    """Provide a mock pymssql connection."""
    conn = MagicMock()
    conn.cursor.return_value = mock_cursor
    return conn


@pytest.fixture
def mock_pymssql(mock_connection: MagicMock) -> Generator[MagicMock, None, None]:
    """Patch pymssql.connect to return mock connection."""
    with (
        patch("pymssql.connect", return_value=mock_connection),
        patch("pymssql.Error", Exception),
    ):
        yield mock_connection


@pytest.fixture
def sample_table_columns() -> list[dict[str, Any]]:
    """Sample column metadata for testing."""
    return [
        {"name": "id", "type": "int", "nullable": "NO", "max_length": None},
        {"name": "name", "type": "nvarchar", "nullable": "NO", "max_length": 100},
        {"name": "email", "type": "nvarchar", "nullable": "YES", "max_length": 255},
        {"name": "created_at", "type": "datetime2", "nullable": "NO", "max_length": None},
    ]


@pytest.fixture
def sample_rows() -> list[dict[str, Any]]:
    """Sample data rows for testing."""
    return [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
        {"id": 3, "name": "Charlie", "email": None},
    ]


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for file operations."""
    return tmp_path
