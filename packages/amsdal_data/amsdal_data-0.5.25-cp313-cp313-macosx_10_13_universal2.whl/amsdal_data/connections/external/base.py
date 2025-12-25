from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Protocol
from typing import runtime_checkable

__all__ = [
    'AsyncExternalServiceConnection',
    'ExternalServiceConnection',
    'SchemaIntrospectionProtocol',
]


@runtime_checkable
class SchemaIntrospectionProtocol(Protocol):
    """
    Protocol for external connections that support schema introspection.

    Connections that implement this protocol can provide metadata about
    their tables, columns, and structure for model generation purposes.
    """

    def get_table_names(self) -> list[str]:
        """
        Get list of all tables/collections in the external data source.

        Returns:
            list[str]: List of table/collection names
        """
        ...

    def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        """
        Get schema information for a specific table.

        Returns a list of dictionaries containing column/field information.
        The exact structure may vary by connection type, but typically includes:
        - name: Column/field name
        - type: Data type
        - nullable: Whether the field can be null
        - primary_key: Whether this is a primary key field

        Args:
            table_name: Name of the table/collection

        Returns:
            list[dict[str, Any]]: List of column/field information dictionaries
        """
        ...


class ExternalServiceConnection(ABC):
    """
    Base class for external service connections.

    External services are non-database connections such as:
    - Email services (SMTP, SendGrid, etc.)
    - Message queues (RabbitMQ, SQS, etc.)
    - External APIs (Stripe, Twilio, etc.)
    - Cache systems (Redis, Memcached)
    - Storage services (S3, Azure Blob, etc.)
    - External databases (SQLite, PostgreSQL, MySQL, etc.)

    Subclasses must implement the abstract methods for connection lifecycle management.
    Subclasses that represent database connections should also implement
    SchemaIntrospectionProtocol for model generation support.
    """

    def __init__(self) -> None:
        self._connection: Any = None
        self._is_connected: bool = False

    @abstractmethod
    def connect(self, **kwargs: Any) -> None:
        """
        Establish a connection to the external service.

        Args:
            **kwargs: Service-specific connection parameters
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Close the connection to the external service.
        """
        pass

    @property
    def is_connected(self) -> bool:
        """
        Check if the connection is currently established.

        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected

    @property
    def is_alive(self) -> bool:
        """
        Check if the connection is alive and responsive.

        Returns:
            bool: True if the connection is alive, False otherwise
        """
        return self._is_connected

    def get_connection(self) -> Any:
        """
        Get the underlying connection object.

        Returns:
            Any: The underlying connection object

        Raises:
            ConnectionError: If not connected
        """
        if not self._is_connected:
            msg = 'Not connected to external service'
            raise ConnectionError(msg)
        return self._connection

    def supports_schema_introspection(self) -> bool:
        """
        Check if this connection supports schema introspection.

        Returns:
            bool: True if connection implements SchemaIntrospectionProtocol
        """
        return isinstance(self, SchemaIntrospectionProtocol)

    @property
    def sql_placeholder(self) -> str:
        """
        Get the SQL placeholder style for this connection.

        Different databases use different placeholder styles:
        - SQLite, MySQL: '?'
        - PostgreSQL: '%s'
        - Oracle: ':1', ':2', etc.

        Returns:
            str: Placeholder character(s) for SQL queries

        Note:
            Subclasses should override this if they don't use '?' placeholders.
        """
        return '?'  # Default to SQLite-style

    @property
    def supports_limit_minus_one(self) -> bool:
        """
        Check if this database supports LIMIT -1 syntax.

        SQLite accepts LIMIT -1 to mean "no limit", but PostgreSQL does not.

        Returns:
            bool: True if the database supports LIMIT -1, False otherwise

        Note:
            Subclasses should override this for databases that don't support it.
        """
        return True  # Default to True (SQLite-style)


class AsyncExternalServiceConnection(ABC):
    """
    Base class for async external service connections.

    Async version of ExternalServiceConnection for services that support async operations.
    """

    def __init__(self) -> None:
        self._connection: Any = None
        self._is_connected: bool = False

    @abstractmethod
    async def connect(self, **kwargs: Any) -> None:
        """
        Establish a connection to the external service.

        Args:
            **kwargs: Service-specific connection parameters
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close the connection to the external service.
        """
        pass

    @property
    async def is_connected(self) -> bool:
        """
        Check if the connection is currently established.

        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected

    @property
    async def is_alive(self) -> bool:
        """
        Check if the connection is alive and responsive.

        Returns:
            bool: True if the connection is alive, False otherwise
        """
        return self._is_connected

    async def get_connection(self) -> Any:
        """
        Get the underlying connection object.

        Returns:
            Any: The underlying connection object

        Raises:
            ConnectionError: If not connected
        """
        if not self._is_connected:
            msg = 'Not connected to external service'
            raise ConnectionError(msg)
        return self._connection
