"""
Read-only PostgreSQL connection for external databases.

This connection type is used for external PostgreSQL databases that should only be read,
not modified by the application. Useful for:
- Reference data from external systems
- Shared read-only databases
- Data warehouses
- Legacy database integration
- Cross-service data access
"""

from typing import Any

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None  # type: ignore[assignment]
    dict_row = None  # type: ignore[assignment]

from amsdal_data.connections.external.base import ExternalServiceConnection


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

    def __init__(self) -> None:
        super().__init__()
        self._host: str | None = None
        self._port: int | None = None
        self._database: str | None = None
        self._user: str | None = None

        if psycopg is None:
            msg = 'psycopg is required for PostgreSQL connections. Install it with: pip install psycopg'
            raise ImportError(msg)

    def connect(
        self,
        host: str = 'localhost',
        port: int = 5432,
        database: str | None = None,
        user: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> None:  # type: ignore[override]
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
        if self._is_connected:
            msg = 'Already connected to a database'
            raise ConnectionError(msg)

        if not database:
            msg = 'Database name is required'
            raise ValueError(msg)

        try:
            # Build connection string
            conninfo = f'host={host} port={port} dbname={database}'
            if user:
                conninfo += f' user={user}'
            if password:
                conninfo += f' password={password}'

            # Connect to PostgreSQL with dict row factory
            self._connection = psycopg.connect(
                conninfo,
                row_factory=dict_row,
                autocommit=True,
                **kwargs,
            )

            # Set connection to read-only mode
            with self._connection.cursor() as cur:
                cur.execute('SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY')

            self._host = host
            self._port = port
            self._database = database
            self._user = user
            self._is_connected = True
        except Exception as e:
            msg = f'Failed to connect to PostgreSQL database: {e}'
            raise ConnectionError(msg) from e

    def disconnect(self) -> None:
        """Close the database connection."""
        if self._connection:
            try:
                self._connection.close()
            except Exception:  # noqa: S110
                # Connection may already be closed
                pass
            finally:
                self._connection = None
                self._host = None
                self._port = None
                self._database = None
                self._user = None
                self._is_connected = False

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
        if not self._is_connected:
            msg = 'Not connected to database'
            raise ConnectionError(msg)

        try:
            cursor = self._connection.cursor()
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            return cursor
        except psycopg.errors.Error as e:
            error_msg = str(e).lower()
            if 'read-only' in error_msg or 'cannot execute' in error_msg:
                msg = f'Write operations not allowed on read-only database: {e}'
                raise ConnectionError(msg) from e
            raise

    def fetch_all(self, query: str, parameters: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        """
        Execute query and fetch all results.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            list[dict]: List of result rows as dictionaries
        """
        cursor = self.execute(query, parameters)
        results = cursor.fetchall()
        cursor.close()
        return results

    def fetch_one(self, query: str, parameters: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        """
        Execute query and fetch one result.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            dict | None: Single result row as dictionary or None
        """
        cursor = self.execute(query, parameters)
        result = cursor.fetchone()
        cursor.close()
        return result

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
            with self._connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            return True
        except Exception:
            return False

    @property
    def connection_info(self) -> dict[str, Any]:
        """Get connection information."""
        return {
            'host': self._host,
            'port': self._port,
            'database': self._database,
            'user': self._user,
        }

    @property
    def sql_placeholder(self) -> str:
        """PostgreSQL uses %s for placeholders."""
        return '%s'

    @property
    def supports_limit_minus_one(self) -> bool:
        """PostgreSQL does not support LIMIT -1."""
        return False

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
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        cursor = self.execute(query, (schema,))
        results = cursor.fetchall()
        cursor.close()
        return [row['table_name'] for row in results]

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
        # Get column information
        query = """
            SELECT
                c.column_name as name,
                c.data_type as type,
                c.is_nullable as nullable,
                c.column_default as default,
                CASE WHEN pk.column_name IS NOT NULL THEN 1 ELSE 0 END as primary_key,
                c.ordinal_position as position
            FROM information_schema.columns c
            LEFT JOIN (
                SELECT ku.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage ku
                    ON tc.constraint_name = ku.constraint_name
                    AND tc.table_schema = ku.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
            ) pk ON c.column_name = pk.column_name
            WHERE c.table_schema = %s
            AND c.table_name = %s
            ORDER BY c.ordinal_position
        """
        cursor = self.execute(query, (schema, table_name, schema, table_name))
        results = cursor.fetchall()
        cursor.close()

        # Convert to more usable format
        schema_info = []
        for row in results:
            col_info = {
                'name': row['name'],
                'type': row['type'],
                'nullable': row['nullable'] == 'YES',
                'default': row['default'],
                'pk': row['primary_key'],
                'position': row['position'],
            }
            schema_info.append(col_info)

        return schema_info
