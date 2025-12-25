import aiosqlite
import sqlite3
from _typeshed import Incomplete
from amsdal_data.connections.external.base import AsyncExternalServiceConnection as AsyncExternalServiceConnection, ExternalServiceConnection as ExternalServiceConnection
from collections.abc import Iterable
from pathlib import Path
from typing import Any

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
    _db_path: Path | None
    def __init__(self) -> None: ...
    _connection: Incomplete
    _is_connected: bool
    def connect(self, db_path: str | Path, **kwargs: Any) -> None:
        """
        Establish connection to read-only SQLite database.

        Args:
            db_path: Path to the SQLite database file
            **kwargs: Additional connection parameters (passed to sqlite3.connect)

        Raises:
            ConnectionError: If already connected or database doesn't exist
            FileNotFoundError: If database file doesn't exist
        """
    def disconnect(self) -> None:
        """Close the database connection."""
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
    def fetch_all(self, query: str, parameters: tuple[Any, ...] | None = None) -> list[sqlite3.Row]:
        """
        Execute query and fetch all results.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            list[sqlite3.Row]: List of result rows
        """
    def fetch_one(self, query: str, parameters: tuple[Any, ...] | None = None) -> sqlite3.Row | None:
        """
        Execute query and fetch one result.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            sqlite3.Row | None: Single result row or None
        """
    @property
    def is_alive(self) -> bool:
        """
        Check if the connection is alive by executing a simple query.

        Returns:
            bool: True if connection is alive, False otherwise
        """
    @property
    def db_path(self) -> Path | None:
        """Get the path to the connected database."""
    def get_table_names(self) -> list[str]:
        """
        Get list of all user tables in the database.

        Excludes SQLite internal tables (those starting with 'sqlite_').

        Returns:
            list[str]: List of table names

        Raises:
            ConnectionError: If not connected
        """
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
    _connection: aiosqlite.Connection | None
    _db_path: Path | None
    def __init__(self) -> None: ...
    _is_connected: bool
    async def connect(self, db_path: str | Path, **kwargs: Any) -> None:
        """
        Establish connection to read-only SQLite database.

        Args:
            db_path: Path to the SQLite database file
            **kwargs: Additional connection parameters (passed to sqlite3.connect)

        Raises:
            ConnectionError: If already connected or database doesn't exist
            FileNotFoundError: If database file doesn't exist
        """
    async def disconnect(self) -> None:
        """Close the database connection."""
    @property
    def connection(self) -> aiosqlite.Connection:
        """Get the active database connection."""
    async def execute(self, query: str, parameters: tuple[Any, ...] | None = None) -> aiosqlite.cursor.Cursor:
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
    async def fetch_all(self, query: str, parameters: tuple[Any, ...] | None = None) -> Iterable[sqlite3.Row]:
        """
        Execute query and fetch all results.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            list[sqlite3.Row]: List of result rows
        """
    async def fetch_one(self, query: str, parameters: tuple[Any, ...] | None = None) -> sqlite3.Row | None:
        """
        Execute query and fetch one result.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            sqlite3.Row | None: Single result row or None
        """
    @property
    async def is_alive(self) -> bool:
        """
        Check if the connection is alive by executing a simple query.

        Returns:
            bool: True if connection is alive, False otherwise
        """
    @property
    def db_path(self) -> Path | None:
        """Get the path to the connected database."""
    async def get_table_names(self) -> list[str]:
        """
        Get list of all user tables in the database.

        Excludes SQLite internal tables (those starting with 'sqlite_').

        Returns:
            list[str]: List of table names

        Raises:
            ConnectionError: If not connected
        """
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
