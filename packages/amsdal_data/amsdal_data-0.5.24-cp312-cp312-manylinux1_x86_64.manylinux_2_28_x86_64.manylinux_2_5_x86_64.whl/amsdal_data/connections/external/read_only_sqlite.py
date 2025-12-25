"""
Read-only SQLite connection for external databases.

This connection type is used for external SQLite databases that should only be read,
not modified by the application. Useful for:
- Reference data from external systems
- Shared read-only databases
- Data warehouses
- Legacy database integration
"""

import sqlite3
import typing as t
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from amsdal_data.connections.external.base import AsyncExternalServiceConnection
from amsdal_data.connections.external.base import ExternalServiceConnection

if t.TYPE_CHECKING:
    import aiosqlite


class ReadOnlySqliteConnection(ExternalServiceConnection):
    """
    Read-only SQLite connection for external databases.

    This connection opens SQLite databases in read-only mode to prevent
    accidental modifications to external data sources.

    Example usage:
        connection = ReadOnlySqliteConnection()
        connection.connect(db_path='./external_data.db')

        # Execute read-only queries
        cursor = connection.execute('SELECT * FROM users WHERE id = ?', (1,))
        rows = cursor.fetchall()

        connection.disconnect()
    """

    def __init__(self) -> None:
        super().__init__()
        self._db_path: Path | None = None

    def connect(self, db_path: str | Path, **kwargs: Any) -> None:  # type: ignore[override]
        """
        Establish connection to read-only SQLite database.

        Args:
            db_path: Path to the SQLite database file
            **kwargs: Additional connection parameters (passed to sqlite3.connect)

        Raises:
            ConnectionError: If already connected or database doesn't exist
            FileNotFoundError: If database file doesn't exist
        """
        if self._is_connected:
            msg = 'Already connected to a database'
            raise ConnectionError(msg)

        db_path = Path(db_path)
        if not db_path.exists():
            msg = f'Database file does not exist: {db_path}'
            raise FileNotFoundError(msg)

        try:
            # Open in read-only mode using URI
            uri = f'file:{db_path}?mode=ro'
            kwargs.setdefault('check_same_thread', False)
            self._connection = sqlite3.connect(uri, uri=True, **kwargs)
            self._connection.row_factory = sqlite3.Row  # Enable dict-like access
            self._db_path = db_path
            self._is_connected = True
        except Exception as e:
            msg = f'Failed to connect to database: {e}'
            raise ConnectionError(msg) from e

    def disconnect(self) -> None:
        """Close the database connection."""
        if self._connection:
            try:
                self._connection.close()
            except sqlite3.Error:
                # Database may already be closed
                pass
            finally:
                self._connection = None
                self._db_path = None
                self._is_connected = False

    def execute(self, query: str, parameters: tuple[Any, ...] | None = None) -> sqlite3.Cursor:
        """
        Execute a read-only query.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            sqlite3.Cursor: Cursor with query results

        Raises:
            ConnectionError: If not connected
            sqlite3.OperationalError: If attempting write operations
        """
        if not self._is_connected:
            msg = 'Not connected to database'
            raise ConnectionError(msg)

        try:
            if parameters:
                return self._connection.execute(query, parameters)
            return self._connection.execute(query)
        except sqlite3.OperationalError as e:
            if 'readonly database' in str(e).lower() or 'attempt to write' in str(e).lower():
                msg = f'Write operations not allowed on read-only database: {e}'
                raise ConnectionError(msg) from e
            raise

    def fetch_all(self, query: str, parameters: tuple[Any, ...] | None = None) -> list[sqlite3.Row]:
        """
        Execute query and fetch all results.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            list[sqlite3.Row]: List of result rows
        """
        cursor = self.execute(query, parameters)
        return cursor.fetchall()

    def fetch_one(self, query: str, parameters: tuple[Any, ...] | None = None) -> sqlite3.Row | None:
        """
        Execute query and fetch one result.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            sqlite3.Row | None: Single result row or None
        """
        cursor = self.execute(query, parameters)
        return cursor.fetchone()

    @property
    def is_alive(self) -> bool:
        """
        Check if the connection is alive by executing a simple query.

        Returns:
            bool: True if connection is alive, False otherwise
        """
        if not self._is_connected:
            return False

        try:
            self._connection.execute('SELECT 1')
            return True
        except sqlite3.Error:
            return False

    @property
    def db_path(self) -> Path | None:
        """Get the path to the connected database."""
        return self._db_path

    def get_table_names(self) -> list[str]:
        """
        Get list of all user tables in the database.

        Excludes SQLite internal tables (those starting with 'sqlite_').

        Returns:
            list[str]: List of table names

        Raises:
            ConnectionError: If not connected
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        cursor = self.execute(query)
        return [row['name'] for row in cursor.fetchall()]

    def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        """
        Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            list[dict]: List of column information dictionaries

        Raises:
            ConnectionError: If not connected
        """
        query = f'PRAGMA table_info({table_name})'
        cursor = self.execute(query)
        return [dict(row) for row in cursor.fetchall()]


class AsyncReadOnlySqliteConnection(AsyncExternalServiceConnection):
    """
    Read-only SQLite connection for external databases.

    This connection opens SQLite databases in read-only mode to prevent
    accidental modifications to external data sources.

    Example usage:
        connection = AsyncReadOnlySqliteConnection()
        await connection.connect(db_path='./external_data.db')

        # Execute read-only queries
        cursor = await connection.execute('SELECT * FROM users WHERE id = ?', (1,))
        rows = await cursor.fetchall()

        await connection.disconnect()
    """

    _connection: t.Optional['aiosqlite.Connection']

    def __init__(self) -> None:
        super().__init__()
        self._db_path: Path | None = None

    async def connect(self, db_path: str | Path, **kwargs: Any) -> None:  # type: ignore[override]
        """
        Establish connection to read-only SQLite database.

        Args:
            db_path: Path to the SQLite database file
            **kwargs: Additional connection parameters (passed to sqlite3.connect)

        Raises:
            ConnectionError: If already connected or database doesn't exist
            FileNotFoundError: If database file doesn't exist
        """
        import aiosqlite

        if self._is_connected:
            msg = 'Already connected to a database'
            raise ConnectionError(msg)

        db_path = Path(db_path)
        if not db_path.exists():
            msg = f'Database file does not exist: {db_path}'
            raise FileNotFoundError(msg)

        try:
            kwargs.setdefault('check_same_thread', False)
            self._connection = await aiosqlite.connect(db_path, **kwargs)
            self._connection.row_factory = sqlite3.Row  # Enable dict-like access
            self._db_path = db_path
            self._is_connected = True
        except Exception as e:
            msg = f'Failed to connect to database: {e}'
            raise ConnectionError(msg) from e

    async def disconnect(self) -> None:
        """Close the database connection."""
        if self._connection:
            try:
                await self._connection.close()
            except sqlite3.Error:
                # Database may already be closed
                pass
            finally:
                self._connection = None
                self._db_path = None
                self._is_connected = False

    @property
    def connection(self) -> 'aiosqlite.Connection':
        """Get the active database connection."""
        if not self._connection:
            msg = 'Not connected to any database'
            raise ConnectionError(msg)
        return self._connection

    async def execute(self, query: str, parameters: tuple[Any, ...] | None = None) -> 'aiosqlite.cursor.Cursor':
        """
        Execute a read-only query.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            sqlite3.Cursor: Cursor with query results

        Raises:
            ConnectionError: If not connected
            sqlite3.OperationalError: If attempting write operations
        """
        if not self._is_connected:
            msg = 'Not connected to database'
            raise ConnectionError(msg)

        try:
            if parameters:
                return await self.connection.execute(query, parameters)
            return await self.connection.execute(query)
        except sqlite3.OperationalError as e:
            if 'readonly database' in str(e).lower() or 'attempt to write' in str(e).lower():
                msg = f'Write operations not allowed on read-only database: {e}'
                raise ConnectionError(msg) from e
            raise

    async def fetch_all(self, query: str, parameters: tuple[Any, ...] | None = None) -> Iterable[sqlite3.Row]:
        """
        Execute query and fetch all results.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            list[sqlite3.Row]: List of result rows
        """
        cursor = await self.execute(query, parameters)
        return await cursor.fetchall()

    async def fetch_one(self, query: str, parameters: tuple[Any, ...] | None = None) -> sqlite3.Row | None:
        """
        Execute query and fetch one result.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            sqlite3.Row | None: Single result row or None
        """
        cursor = await self.execute(query, parameters)
        return await cursor.fetchone()

    @property
    async def is_alive(self) -> bool:
        """
        Check if the connection is alive by executing a simple query.

        Returns:
            bool: True if connection is alive, False otherwise
        """
        if not self._is_connected:
            return False

        try:
            await self.connection.execute('SELECT 1')
            return True
        except sqlite3.Error:
            return False

    @property
    def db_path(self) -> Path | None:
        """Get the path to the connected database."""
        return self._db_path

    async def get_table_names(self) -> list[str]:
        """
        Get list of all user tables in the database.

        Excludes SQLite internal tables (those starting with 'sqlite_').

        Returns:
            list[str]: List of table names

        Raises:
            ConnectionError: If not connected
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        cursor = await self.execute(query)
        return [row['name'] for row in await cursor.fetchall()]

    async def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        """
        Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            list[dict]: List of column information dictionaries

        Raises:
            ConnectionError: If not connected
        """
        query = f'PRAGMA table_info({table_name})'
        cursor = await self.execute(query)
        return [dict(row) for row in await cursor.fetchall()]
