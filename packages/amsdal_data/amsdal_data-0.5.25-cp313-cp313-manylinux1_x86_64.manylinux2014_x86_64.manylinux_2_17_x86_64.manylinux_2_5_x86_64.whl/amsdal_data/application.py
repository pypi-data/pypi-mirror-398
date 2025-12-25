import inspect
from typing import Any
from typing import ClassVar

import amsdal_glue as glue
from amsdal_glue.applications.lakehouse import AsyncLakehouseApplication
from amsdal_glue.applications.lakehouse import LakehouseApplication
from amsdal_glue_core.common.interfaces.connectable import AsyncConnectable
from amsdal_glue_core.common.interfaces.connection import AsyncConnectionBase
from amsdal_glue_core.common.interfaces.connection import ConnectionBase
from amsdal_utils.config.data_models.amsdal_config import AmsdalConfig
from amsdal_utils.config.data_models.connection_config import ConnectionType
from amsdal_utils.utils.decorators import async_mode_only
from amsdal_utils.utils.decorators import sync_mode_only
from amsdal_utils.utils.singleton import Singleton

from amsdal_data.aliases.using import LAKEHOUSE_DB_ALIAS
from amsdal_data.data_models.connection_status import ConnectionStatus
from amsdal_data.internal_schemas.metadata import metadata_schema
from amsdal_data.internal_schemas.reference import reference_schema
from amsdal_data.internal_schemas.transaction import transaction_schema
from amsdal_data.services.operation_manager import AsyncOperationManager
from amsdal_data.services.operation_manager import OperationManager
from amsdal_data.utils import get_schemas_for_connection_name
from amsdal_data.utils import resolve_backend_class


class DataApplication(metaclass=Singleton):
    DEFAULT_CONTAINER_NAME: ClassVar[str] = 'default'
    LAKEHOUSE_CONTAINER_NAME: ClassVar[str] = 'lakehouse'

    @sync_mode_only
    def __init__(self) -> None:
        self._is_lakehouse_only = False
        self._application = LakehouseApplication()
        self._operation_manager = OperationManager(
            lakehouse_container=self._application.lakehouse_container,
        )
        self._extra_connections: dict[str, ConnectionBase] = {}
        self._external_service_connections: dict[str, Any] = {}

    @property
    def is_lakehouse_only(self) -> bool:
        return self._is_lakehouse_only

    @property
    def operation_manager(self) -> OperationManager:
        return self._operation_manager

    @property
    def connections_statuses(self) -> list[ConnectionStatus]:
        _connections = [
            ConnectionStatus(
                name=_name,
                is_connected=_conn.is_connected,
                is_alive=_conn.is_alive,
            )
            for _name, _conn in self._extra_connections.items()
        ]

        # Add external service connections
        for _name, _conn in self._external_service_connections.items():
            _connections.append(
                ConnectionStatus(
                    name=f'external_service_{_name}',
                    is_connected=_conn.is_connected,
                    is_alive=_conn.is_alive,
                )
            )

        try:
            connection_pool = self._application.lakehouse_connection_manager.get_connection_pool('default')
            _connections.append(
                ConnectionStatus(
                    name='lakehouse_connection',
                    is_connected=connection_pool.is_connected,
                    is_alive=connection_pool.is_alive,
                )
            )
        except Exception:
            _connections.append(
                ConnectionStatus(
                    name='lakehouse_connection',
                    is_connected=False,
                    is_alive=False,
                )
            )

        try:
            connection_pool = self._application.default_connection_manager.get_connection_pool('default')
            _connections.append(
                ConnectionStatus(
                    name='default_connection',
                    is_connected=connection_pool.is_connected,
                    is_alive=connection_pool.is_alive,
                )
            )
        except Exception:
            _connections.append(
                ConnectionStatus(
                    name='default_connection',
                    is_connected=False,
                    is_alive=False,
                )
            )

        return _connections

    def setup(self, config: AmsdalConfig) -> None:
        is_lakehouse_only = config.is_lakehouse_only
        self._is_lakehouse_only = is_lakehouse_only

        if is_lakehouse_only:
            all_services = [
                glue.interfaces.SchemaQueryService,
                glue.interfaces.DataQueryService,
                glue.interfaces.SchemaCommandService,
                glue.interfaces.DataCommandService,
                glue.interfaces.TransactionCommandService,
                glue.interfaces.LockCommandService,
            ]

            for service in all_services:
                self._application.pipeline.define(service, [self._application.lakehouse_container.name])

        for name, connection_config in config.connections.items():
            is_lakehouse = config.resources_config.lakehouse == name
            connection_class = resolve_backend_class(connection_config.backend)

            # Handle external service connections
            if connection_config.connection_type == ConnectionType.EXTERNAL_SERVICE:
                connection = connection_class()  # type: ignore[assignment]
                # Only connect if managed
                if connection_config.is_managed:
                    connection.connect(**connection_config.credentials)  # type: ignore[attr-defined]
                self._external_service_connections[name] = connection  # type: ignore[assignment]
                continue

            # Handle database connections (state-only and historical)
            if issubclass(connection_class, ConnectionBase):
                connection = glue.DefaultConnectionPool(
                    connection_class,
                    **connection_config.credentials,
                )

                if is_lakehouse:
                    self._application.lakehouse_connection_manager.register_connection_pool(connection)

                if is_lakehouse_only:
                    continue

                if config.resources_config.repository:
                    for schema_name in get_schemas_for_connection_name(name, config.resources_config.repository):
                        self._application.default_connection_manager.register_connection_pool(
                            connection,
                            schema_name=schema_name,
                        )
            else:
                # Init extra connections (e.g. Lock, cache, etc.)
                connection = connection_class()  # type: ignore[assignment]
                connection.connect(**connection_config.credentials)  # type: ignore[attr-defined]
                self._extra_connections[name] = connection  # type: ignore[assignment]

    def get_extra_connection(self, name: str) -> Any:
        """Get an extra connection (lock, cache, etc.) by name."""
        return self._extra_connections[name]

    def get_external_service_connection(self, name: str) -> Any:
        """Get an external service connection (email, storage, etc.) by name."""
        return self._external_service_connections[name]

    @staticmethod
    def register_internal_tables() -> None:
        from amsdal_data.services.table_schema_manager import TableSchemasManager

        table_schema_manager = TableSchemasManager()
        table_schema_manager.register_table(metadata_schema, using=LAKEHOUSE_DB_ALIAS)
        table_schema_manager.register_table(reference_schema, using=LAKEHOUSE_DB_ALIAS)
        table_schema_manager.register_table(transaction_schema, using=LAKEHOUSE_DB_ALIAS)

    def teardown(self) -> None:
        from amsdal_data.services.table_schema_manager import TableSchemasManager
        from amsdal_data.transactions.background.manager import BackgroundTransactionManager
        from amsdal_data.transactions.manager import AmsdalTransactionManager

        # Disconnect external service connections
        for connection in self._external_service_connections.values():
            if hasattr(connection, 'disconnect'):
                connection.disconnect()

        self._application.shutdown()

        # Invalidate the singletons
        TableSchemasManager.invalidate()
        AmsdalTransactionManager.invalidate()
        BackgroundTransactionManager.invalidate()
        self.__class__.invalidate()

    def wait_for_background_tasks(self) -> None:
        self._application.shutdown(skip_close_connections=True)


class AsyncDataApplication(metaclass=Singleton):
    DEFAULT_CONTAINER_NAME: ClassVar[str] = 'default'
    LAKEHOUSE_CONTAINER_NAME: ClassVar[str] = 'lakehouse'

    @async_mode_only
    def __init__(self) -> None:
        self._is_lakehouse_only = False
        self._application = AsyncLakehouseApplication()
        self._operation_manager = AsyncOperationManager(
            lakehouse_container=self._application.lakehouse_container,
        )
        self._extra_connections: dict[str, AsyncConnectionBase] = {}
        self._external_service_connections: dict[str, Any] = {}

    @property
    def is_lakehouse_only(self) -> bool:
        return self._is_lakehouse_only

    @property
    def operation_manager(self) -> AsyncOperationManager:
        return self._operation_manager

    @property
    async def connections_statuses(self) -> list[ConnectionStatus]:
        _connections = [
            ConnectionStatus(
                name=_name,
                is_connected=await _conn.is_connected,
                is_alive=await _conn.is_alive,
            )
            for _name, _conn in self._extra_connections.items()
        ]

        # Add external service connections
        for _name, _conn in self._external_service_connections.items():
            _connections.append(
                ConnectionStatus(
                    name=f'external_service_{_name}',
                    is_connected=await _conn.is_connected,
                    is_alive=await _conn.is_alive,
                )
            )

        try:
            connection_pool = self._application.lakehouse_connection_manager.get_connection_pool('default')
            _connections.append(
                ConnectionStatus(
                    name='lakehouse_connection',
                    is_connected=await connection_pool.is_connected,
                    is_alive=await connection_pool.is_alive,
                )
            )
        except Exception:
            _connections.append(
                ConnectionStatus(
                    name='lakehouse_connection',
                    is_connected=False,
                    is_alive=False,
                )
            )

        try:
            connection_pool = self._application.default_connection_manager.get_connection_pool('default')
            _connections.append(
                ConnectionStatus(
                    name='default_connection',
                    is_connected=await connection_pool.is_connected,
                    is_alive=await connection_pool.is_alive,
                )
            )
        except Exception:
            _connections.append(
                ConnectionStatus(
                    name='default_connection',
                    is_connected=False,
                    is_alive=False,
                )
            )

        return _connections

    async def setup(self, config: AmsdalConfig) -> None:
        is_lakehouse_only = config.is_lakehouse_only
        self._is_lakehouse_only = is_lakehouse_only

        if is_lakehouse_only:
            all_services = [
                glue.interfaces.AsyncSchemaQueryService,
                glue.interfaces.AsyncDataQueryService,
                glue.interfaces.AsyncSchemaCommandService,
                glue.interfaces.AsyncDataCommandService,
                glue.interfaces.AsyncTransactionCommandService,
                glue.interfaces.AsyncLockCommandService,
            ]

            for service in all_services:
                self._application.pipeline.define(service, [self._application.lakehouse_container.name])

        for name, connection_config in config.connections.items():
            is_lakehouse = config.resources_config.lakehouse == name
            connection_class = resolve_backend_class(connection_config.backend)

            # Handle external service connections
            if connection_config.connection_type == ConnectionType.EXTERNAL_SERVICE:
                if issubclass(connection_class, AsyncConnectable):
                    connection = connection_class()
                    # Only connect if managed
                    if connection_config.is_managed:
                        await connection.connect(**connection_config.credentials)
                else:
                    connection = connection_class()  # type: ignore[assignment]
                    # Only connect if managed
                    if connection_config.is_managed:
                        _external_connection = connection.connect(**connection_config.credentials)  # type: ignore[attr-defined]
                        if inspect.isawaitable(_external_connection):
                            await _external_connection

                self._external_service_connections[name] = connection  # type: ignore[assignment]
                continue

            # Handle database connections (state-only and historical)
            if issubclass(connection_class, AsyncConnectionBase):
                connection = glue.DefaultAsyncConnectionPool(
                    connection_class,
                    **connection_config.credentials,
                )

                if is_lakehouse:
                    self._application.lakehouse_connection_manager.register_connection_pool(connection)

                if is_lakehouse_only:
                    continue

                if config.resources_config.repository:
                    for schema_name in get_schemas_for_connection_name(name, config.resources_config.repository):
                        self._application.default_connection_manager.register_connection_pool(
                            connection,
                            schema_name=schema_name,
                        )
            else:
                # Init extra connections (e.g. Lock, cache, etc.)
                if issubclass(connection_class, AsyncConnectable):
                    connection = connection_class()
                    await connection.connect(**connection_config.credentials)
                else:
                    connection = connection_class()  # type: ignore[assignment]
                    connection.connect(**connection_config.credentials)  # type: ignore[attr-defined]
                self._extra_connections[name] = connection  # type: ignore[assignment]

    def get_extra_connection(self, name: str) -> Any:
        """Get an extra connection (lock, cache, etc.) by name."""
        return self._extra_connections[name]

    def get_external_service_connection(self, name: str) -> Any:
        """Get an external service connection (email, storage, etc.) by name."""
        return self._external_service_connections[name]

    @staticmethod
    async def register_internal_tables() -> None:
        from amsdal_data.services.table_schema_manager import AsyncTableSchemasManager

        table_schema_manager = AsyncTableSchemasManager()
        await table_schema_manager.register_table(metadata_schema, using=LAKEHOUSE_DB_ALIAS)
        await table_schema_manager.register_table(reference_schema, using=LAKEHOUSE_DB_ALIAS)
        await table_schema_manager.register_table(transaction_schema, using=LAKEHOUSE_DB_ALIAS)

    async def teardown(self) -> None:
        from amsdal_data.services.table_schema_manager import AsyncTableSchemasManager
        from amsdal_data.transactions.background.manager import AsyncBackgroundTransactionManager
        from amsdal_data.transactions.manager import AmsdalAsyncTransactionManager

        # Disconnect external service connections
        for connection in self._external_service_connections.values():
            if hasattr(connection, 'disconnect'):
                if callable(connection.disconnect):
                    result = connection.disconnect()
                    # If it's a coroutine, await it
                    if hasattr(result, '__await__'):
                        await result

        await self._application.shutdown()

        # Invalidate the singletons
        AsyncTableSchemasManager.invalidate()
        AmsdalAsyncTransactionManager.invalidate()
        AsyncBackgroundTransactionManager.invalidate()
        self.__class__.invalidate()

    async def wait_for_background_tasks(self) -> None:
        await self._application.shutdown(skip_close_connections=True)
