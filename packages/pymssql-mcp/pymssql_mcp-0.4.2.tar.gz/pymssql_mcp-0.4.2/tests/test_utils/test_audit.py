"""Tests for audit logging."""

import json

import pytest

from mssql_mcp.utils.audit import (
    AuditLogger,
    audit_tool_call,
    get_audit_logger,
    init_audit_logger,
)


class TestAuditLogger:
    """Tests for AuditLogger class."""

    @pytest.fixture
    def audit_log_path(self, temp_dir):
        """Provide a temp path for audit log."""
        return temp_dir / "audit.jsonl"

    @pytest.fixture
    def logger(self, audit_log_path):
        """Create an AuditLogger instance."""
        return AuditLogger(
            log_file=str(audit_log_path),
            include_results=True,
            max_result_size=1000,
        )

    def test_start_session(self, logger, audit_log_path):
        """Test starting an audit session."""
        session_id = logger.start_session()
        assert session_id is not None
        assert len(session_id) > 0

        # Check log file contains session_start entry
        with open(audit_log_path) as f:
            entry = json.loads(f.readline())
            assert entry["event"] == "session_start"
            assert entry["session_id"] == session_id

    def test_start_session_custom_id(self, logger):
        """Test starting a session with custom ID."""
        session_id = logger.start_session(session_id="custom-123")
        assert session_id == "custom-123"

    def test_end_session(self, logger, audit_log_path):
        """Test ending an audit session."""
        logger.start_session()
        logger.end_session()

        # Check log file contains session_end entry
        with open(audit_log_path) as f:
            lines = f.readlines()
            end_entry = json.loads(lines[-1])
            assert end_entry["event"] == "session_end"

    def test_log_tool_call(self, logger, audit_log_path):
        """Test logging a tool call."""
        logger.start_session()
        logger.log_tool_call(
            tool_name="execute_query",
            parameters={"query": "SELECT * FROM Users"},
            result={"rows": [{"id": 1}]},
            error=None,
            duration_ms=50.5,
        )

        # Check log file contains tool_call entry
        with open(audit_log_path) as f:
            lines = f.readlines()
            tool_entry = json.loads(lines[1])  # Second entry after session_start
            assert tool_entry["event"] == "tool_call"
            assert tool_entry["tool_name"] == "execute_query"
            assert tool_entry["status"] == "success"
            assert tool_entry["duration_ms"] == 50.5

    def test_log_tool_call_error(self, logger, audit_log_path):
        """Test logging a failed tool call."""
        logger.start_session()
        logger.log_tool_call(
            tool_name="execute_query",
            parameters={"query": "SELECT * FROM Users"},
            result=None,
            error="Connection failed",
            duration_ms=10.0,
        )

        with open(audit_log_path) as f:
            lines = f.readlines()
            tool_entry = json.loads(lines[1])
            assert tool_entry["status"] == "error"
            assert tool_entry["error"] == "Connection failed"

    def test_sanitize_parameters_password(self, logger, audit_log_path):
        """Test sensitive parameters are masked."""
        logger.start_session()
        logger.log_tool_call(
            tool_name="connect",
            parameters={"host": "localhost", "password": "secret123"},
            result=None,
            error=None,
            duration_ms=100.0,
        )

        with open(audit_log_path) as f:
            lines = f.readlines()
            tool_entry = json.loads(lines[1])
            assert tool_entry["parameters"]["host"] == "localhost"
            assert tool_entry["parameters"]["password"] == "***REDACTED***"

    def test_sanitize_parameters_token(self, logger, audit_log_path):
        """Test token parameters are masked."""
        logger.start_session()
        logger.log_tool_call(
            tool_name="auth",
            parameters={"api_token": "abc123", "user": "test"},
            result=None,
            error=None,
            duration_ms=100.0,
        )

        with open(audit_log_path) as f:
            lines = f.readlines()
            tool_entry = json.loads(lines[1])
            assert tool_entry["parameters"]["user"] == "test"
            assert tool_entry["parameters"]["api_token"] == "***REDACTED***"

    def test_truncate_large_result(self, audit_log_path):
        """Test large results are truncated."""
        logger = AuditLogger(
            log_file=str(audit_log_path),
            include_results=True,
            max_result_size=100,
        )
        logger.start_session()

        large_result = {"data": "x" * 500}
        logger.log_tool_call(
            tool_name="test",
            parameters={},
            result=large_result,
            error=None,
            duration_ms=10.0,
        )

        with open(audit_log_path) as f:
            lines = f.readlines()
            tool_entry = json.loads(lines[1])
            assert tool_entry["result"]["_truncated"] is True

    def test_log_query(self, logger, audit_log_path):
        """Test logging a SQL query."""
        logger.start_session()
        logger.log_query(
            query="SELECT * FROM Users",
            result_count=10,
            error=None,
            duration_ms=25.0,
        )

        with open(audit_log_path) as f:
            lines = f.readlines()
            query_entry = json.loads(lines[1])
            assert query_entry["event"] == "query"
            assert query_entry["query"] == "SELECT * FROM Users"
            assert query_entry["result_count"] == 10


class TestAuditLoggerSingleton:
    """Tests for audit logger singleton functions."""

    def test_init_and_get_logger(self, temp_dir):
        """Test initializing and getting the global logger."""
        log_path = str(temp_dir / "global_audit.jsonl")

        # Initialize
        logger = init_audit_logger(log_file=log_path)
        assert logger is not None

        # Get
        retrieved = get_audit_logger()
        assert retrieved is logger

    def test_audit_tool_call_function(self, temp_dir):
        """Test the convenience audit_tool_call function."""
        log_path = str(temp_dir / "func_audit.jsonl")

        logger = init_audit_logger(log_file=log_path)
        logger.start_session()

        audit_tool_call(
            tool_name="test_tool",
            parameters={"param1": "value1"},
            result={"ok": True},
            error=None,
            duration_ms=5.0,
        )

        with open(log_path) as f:
            lines = f.readlines()
            assert len(lines) == 2  # session_start + tool_call
