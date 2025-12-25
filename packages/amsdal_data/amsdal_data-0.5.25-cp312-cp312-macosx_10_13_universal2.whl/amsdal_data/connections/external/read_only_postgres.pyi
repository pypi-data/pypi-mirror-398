from _typeshed import Incomplete
from amsdal_data.connections.external.base import ExternalServiceConnection as ExternalServiceConnection
from typing import Any

class ReadOnlyPostgresConnection(ExternalServiceConnection):
    """
    Read-only PostgreSQL connection for external databases.

    This connection opens PostgreSQL databases in read-only mode to prevent
    accidental modifications to external data sources.

    Example usage:
        connection = ReadOnlyPostgresConnection()
        connection.connect(
            host='localhost',
            port=5432,
            database='external_db',
            user='readonly_user',
            password='secret'
        )

        # Execute read-only queries
        rows = connection.fetch_all('SELECT * FROM users WHERE id = %s', (1,))

        connection.disconnect()
    """
    _host: str | None
    _port: int | None
    _database: str | None
    _user: str | None
    def __init__(self) -> None: ...
    _connection: Incomplete
    _is_connected: bool
    def connect(self, host: str = 'localhost', port: int = 5432, database: str | None = None, user: str | None = None, password: str | None = None, **kwargs: Any) -> None:
        """
        Establish connection to read-only PostgreSQL database.

        Args:
            host: PostgreSQL server host
            port: PostgreSQL server port (default: 5432)
            database: Database name
            user: Username for authentication
            password: Password for authentication
            **kwargs: Additional connection parameters (passed to psycopg.connect)

        Raises:
            ConnectionError: If already connected or connection fails
            ImportError: If psycopg is not installed
        """
    def disconnect(self) -> None:
        """Close the database connection."""
    def execute(self, query: str, parameters: tuple[Any, ...] | None = None) -> Any:
        """
        Execute a read-only query.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional, uses %s placeholders)

        Returns:
            Cursor with query results

        Raises:
            ConnectionError: If not connected or attempting write operations
        """
    def fetch_all(self, query: str, parameters: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        """
        Execute query and fetch all results.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            list[dict]: List of result rows as dictionaries
        """
    def fetch_one(self, query: str, parameters: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        """
        Execute query and fetch one result.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            dict | None: Single result row as dictionary or None
        """
    @property
    def is_alive(self) -> bool:
        """
        Check if the connection is alive by executing a simple query.

        Returns:
            bool: True if connection is alive, False otherwise
        """
    @property
    def connection_info(self) -> dict[str, Any]:
        """Get connection information."""
    @property
    def sql_placeholder(self) -> str:
        """PostgreSQL uses %s for placeholders."""
    @property
    def supports_limit_minus_one(self) -> bool:
        """PostgreSQL does not support LIMIT -1."""
    def get_table_names(self, schema: str = 'public') -> list[str]:
        """
        Get list of all user tables in the specified schema.

        Args:
            schema: Schema name (default: 'public')

        Returns:
            list[str]: List of table names

        Raises:
            ConnectionError: If not connected
        """
    def get_table_schema(self, table_name: str, schema: str = 'public') -> list[dict[str, Any]]:
        """
        Get schema information for a table.

        Args:
            table_name: Name of the table
            schema: Schema name (default: 'public')

        Returns:
            list[dict]: List of column information dictionaries with keys:
                - name: Column name
                - type: Data type
                - nullable: Whether column can be NULL
                - default: Default value (if any)
                - primary_key: Whether column is part of primary key

        Raises:
            ConnectionError: If not connected
        """
