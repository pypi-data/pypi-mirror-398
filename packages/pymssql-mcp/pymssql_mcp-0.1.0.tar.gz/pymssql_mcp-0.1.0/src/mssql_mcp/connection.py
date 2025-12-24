"""Connection management for Microsoft SQL Server databases."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pymssql

from .config import MSSQLConfig

logger = logging.getLogger(__name__)


class ConnectionError(Exception):
    """Raised when a database connection fails."""

    pass


class QueryError(Exception):
    """Raised when a query execution fails."""

    pass


@dataclass
class ConnectionInfo:
    """Information about an active database connection."""

    name: str
    host: str
    database: str
    connected_at: datetime
    is_active: bool = True


class ConnectionManager:
    """Manages connections to SQL Server databases.

    Provides connection lifecycle management, auto-reconnect capability,
    and query execution with timeout support.

    Args:
        config: MSSQLConfig instance with connection parameters
    """

    def __init__(self, config: MSSQLConfig) -> None:
        self._config = config
        self._connection: pymssql.Connection | None = None
        self._connections: dict[str, ConnectionInfo] = {}
        self._default_connection: str = "default"

    @property
    def config(self) -> MSSQLConfig:
        """Return the configuration object."""
        return self._config

    def connect(self, name: str = "default") -> ConnectionInfo:
        """Establish a connection to the SQL Server.

        Args:
            name: Connection name for reference

        Returns:
            ConnectionInfo with connection details

        Raises:
            ConnectionError: If connection fails
        """
        if name in self._connections and self._connections[name].is_active:
            logger.info(f"Reusing existing connection '{name}'")
            return self._connections[name]

        try:
            logger.info(f"Connecting to {self._config.host}/{self._config.database}")

            self._connection = pymssql.connect(
                server=self._config.host,
                user=self._config.user,
                password=self._config.password,
                database=self._config.database,
                port=self._config.port,
                login_timeout=self._config.timeout,
                timeout=self._config.query_timeout,
            )

            info = ConnectionInfo(
                name=name,
                host=self._config.host,
                database=self._config.database,
                connected_at=datetime.now(),
                is_active=True,
            )
            self._connections[name] = info

            logger.info(f"Connected successfully to {self._config.database}")
            return info

        except pymssql.Error as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to {self._config.host}: {e}") from e

    def disconnect(self, name: str = "default") -> bool:
        """Close a named connection.

        Args:
            name: Name of the connection to close

        Returns:
            True if connection was closed, False if not found
        """
        if name not in self._connections:
            return False

        try:
            if self._connection:
                self._connection.close()
                self._connection = None

            self._connections[name].is_active = False
            del self._connections[name]

            logger.info(f"Disconnected connection '{name}'")
            return True

        except pymssql.Error as e:
            logger.warning(f"Error during disconnect: {e}")
            return False

    def disconnect_all(self) -> int:
        """Close all connections.

        Returns:
            Count of closed connections
        """
        names = list(self._connections.keys())
        count = 0
        for name in names:
            if self.disconnect(name):
                count += 1
        return count

    def list_connections(self) -> dict[str, ConnectionInfo]:
        """Return all active connections."""
        return {k: v for k, v in self._connections.items() if v.is_active}

    def get_connection(self) -> pymssql.Connection:
        """Get the active connection, auto-reconnecting if necessary.

        Returns:
            Active pymssql.Connection object

        Raises:
            ConnectionError: If reconnection fails
        """
        if self._connection is None:
            self.connect(self._default_connection)

        assert self._connection is not None

        # Verify connection is still alive
        try:
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        except pymssql.Error:
            logger.warning("Connection lost, attempting reconnect")
            self._connection = None
            self.connect(self._default_connection)

        return self._connection

    def execute_query(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
        as_dict: bool = True,
    ) -> list[dict[str, Any]] | list[tuple[Any, ...]]:
        """Execute a query and return results.

        Args:
            query: SQL query to execute
            params: Optional query parameters (tuple or dict)
            as_dict: If True, return rows as dicts; if False, as tuples

        Returns:
            List of rows (as dicts or tuples)

        Raises:
            QueryError: If query execution fails
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor(as_dict=as_dict)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # For SELECT queries, fetch results
            if cursor.description:
                rows = cursor.fetchall()
                return list(rows)
            else:
                # For INSERT/UPDATE/DELETE, commit and return empty
                conn.commit()
                return []

        except pymssql.Error as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryError(f"Query failed: {e}") from e
        finally:
            cursor.close()

    def execute_non_query(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> int:
        """Execute a non-SELECT query (INSERT, UPDATE, DELETE).

        Args:
            query: SQL statement to execute
            params: Optional query parameters

        Returns:
            Number of affected rows

        Raises:
            QueryError: If execution fails
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            affected = cursor.rowcount
            conn.commit()
            return affected

        except pymssql.Error as e:
            conn.rollback()
            logger.error(f"Query execution failed: {e}")
            raise QueryError(f"Query failed: {e}") from e
        finally:
            cursor.close()

    def call_stored_proc(
        self,
        proc_name: str,
        params: tuple[Any, ...] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a stored procedure and return results.

        Args:
            proc_name: Name of the stored procedure
            params: Optional procedure parameters

        Returns:
            List of result rows as dicts

        Raises:
            QueryError: If execution fails
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.callproc(proc_name, params or ())

            # Fetch results if any
            results = []
            if cursor.description:
                results = list(cursor.fetchall())

            conn.commit()
            return results

        except pymssql.Error as e:
            logger.error(f"Stored procedure execution failed: {e}")
            raise QueryError(f"Stored procedure '{proc_name}' failed: {e}") from e
        finally:
            cursor.close()

    def health_check(self) -> bool:
        """Perform a quick health check on the connection.

        Returns:
            True if connection is healthy, False otherwise
        """
        if self._connection is None:
            return True  # No connection to check

        try:
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    def force_disconnect(self) -> None:
        """Force disconnect the current connection without cleanup.

        Used by the watchdog to reset a hung connection.
        """
        import contextlib

        logger.warning("Force disconnecting database connection")
        try:
            if self._connection:
                with contextlib.suppress(Exception):
                    self._connection.close()
                self._connection = None

            self._connections.clear()

        except Exception as e:
            logger.error(f"Error during force disconnect: {e}")
        finally:
            self._connection = None
