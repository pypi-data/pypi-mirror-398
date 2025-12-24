"""Audit logging for mssql-mcp tool invocations."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Sensitive field names to mask in logs
SENSITIVE_FIELDS: set[str] = {
    "password",
    "token",
    "secret",
    "key",
    "credential",
    "api_key",
    "apikey",
    "auth",
}


class AuditLogger:
    """Logs MCP tool invocations to a JSONL file.

    Provides session tracking, parameter sanitization, and result truncation.

    Args:
        log_file: Path to the audit log file
        include_results: Whether to log tool results
        max_result_size: Maximum size of result to log (truncate if larger)
    """

    def __init__(
        self,
        log_file: str,
        include_results: bool = True,
        max_result_size: int = 10000,
    ) -> None:
        self.log_file = Path(log_file)
        self.include_results = include_results
        self.max_result_size = max_result_size
        self._session_id: str | None = None
        self._session_start: datetime | None = None

        # Ensure parent directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def start_session(self, session_id: str | None = None) -> str:
        """Start a new audit session.

        Args:
            session_id: Optional custom session ID

        Returns:
            The session ID
        """
        self._session_start = datetime.now()
        self._session_id = session_id or self._session_start.strftime("%Y%m%d_%H%M%S_%f")

        self._write_entry(
            {
                "event": "session_start",
                "session_id": self._session_id,
                "timestamp": self._session_start.isoformat(),
            }
        )

        logger.debug(f"Audit session started: {self._session_id}")
        return self._session_id

    def end_session(self) -> None:
        """End the current audit session."""
        if self._session_id is None:
            return

        self._write_entry(
            {
                "event": "session_end",
                "session_id": self._session_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

        logger.debug(f"Audit session ended: {self._session_id}")
        self._session_id = None
        self._session_start = None

    def log_tool_call(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        result: Any | None = None,
        error: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        """Log a tool invocation.

        Args:
            tool_name: Name of the MCP tool
            parameters: Tool parameters (will be sanitized)
            result: Tool result (optional, may be truncated)
            error: Error message if tool failed
            duration_ms: Execution time in milliseconds
        """
        entry: dict[str, Any] = {
            "event": "tool_call",
            "session_id": self._session_id,
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "parameters": self._sanitize_parameters(parameters),
        }

        if duration_ms is not None:
            entry["duration_ms"] = round(duration_ms, 2)

        if error:
            entry["error"] = error
            entry["status"] = "error"
        else:
            entry["status"] = "success"

        if self.include_results and result is not None:
            entry["result"] = self._truncate_result(result)

        self._write_entry(entry)

    def log_query(
        self,
        query: str,
        result_count: int | None = None,
        error: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        """Log a SQL query execution.

        Args:
            query: The SQL query executed
            result_count: Number of rows returned/affected
            error: Error message if query failed
            duration_ms: Execution time in milliseconds
        """
        entry: dict[str, Any] = {
            "event": "query",
            "session_id": self._session_id,
            "timestamp": datetime.now().isoformat(),
            "query": query[:5000] if len(query) > 5000 else query,  # Limit query length
        }

        if duration_ms is not None:
            entry["duration_ms"] = round(duration_ms, 2)

        if result_count is not None:
            entry["result_count"] = result_count

        if error:
            entry["error"] = error
            entry["status"] = "error"
        else:
            entry["status"] = "success"

        self._write_entry(entry)

    def _sanitize_parameters(self, params: dict[str, Any]) -> dict[str, Any]:
        """Sanitize parameters by masking sensitive values.

        Args:
            params: Original parameters

        Returns:
            Sanitized parameters with sensitive values masked
        """
        sanitized: dict[str, Any] = {}

        for key, value in params.items():
            key_lower = key.lower()

            # Check if key contains any sensitive field name
            if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_parameters(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_parameters(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    def _truncate_result(self, result: Any) -> Any:
        """Truncate result if it exceeds max size.

        Args:
            result: Original result

        Returns:
            Truncated result
        """
        try:
            result_str = json.dumps(result, default=str)
            if len(result_str) > self.max_result_size:
                return {
                    "_truncated": True,
                    "_original_size": len(result_str),
                    "_preview": result_str[: self.max_result_size // 2] + "...",
                }
            return result
        except (TypeError, ValueError):
            return str(result)[: self.max_result_size]

    def _write_entry(self, entry: dict[str, Any]) -> None:
        """Write an entry to the log file.

        Args:
            entry: Log entry dictionary
        """
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except OSError as e:
            logger.error(f"Failed to write audit log: {e}")


# Module-level singleton
_audit_logger: AuditLogger | None = None


def init_audit_logger(
    log_file: str,
    include_results: bool = True,
    max_result_size: int = 10000,
) -> AuditLogger:
    """Initialize the global audit logger.

    Args:
        log_file: Path to the audit log file
        include_results: Whether to log tool results
        max_result_size: Maximum size of result to log

    Returns:
        The initialized AuditLogger
    """
    global _audit_logger
    _audit_logger = AuditLogger(
        log_file=log_file,
        include_results=include_results,
        max_result_size=max_result_size,
    )
    return _audit_logger


def get_audit_logger() -> AuditLogger | None:
    """Get the global audit logger.

    Returns:
        The audit logger or None if not initialized
    """
    return _audit_logger


def audit_tool_call(
    tool_name: str,
    parameters: dict[str, Any],
    result: Any | None = None,
    error: str | None = None,
    duration_ms: float | None = None,
) -> None:
    """Convenience function to log a tool call.

    Does nothing if audit logging is not initialized.

    Args:
        tool_name: Name of the MCP tool
        parameters: Tool parameters
        result: Tool result
        error: Error message if tool failed
        duration_ms: Execution time in milliseconds
    """
    if _audit_logger is not None:
        _audit_logger.log_tool_call(
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            error=error,
            duration_ms=duration_ms,
        )
