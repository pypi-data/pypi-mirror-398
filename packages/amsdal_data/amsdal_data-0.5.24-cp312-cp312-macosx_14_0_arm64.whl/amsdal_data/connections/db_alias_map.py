from amsdal_data.aliases.db import POSTGRES_HISTORICAL_ALIAS
from amsdal_data.aliases.db import POSTGRES_HISTORICAL_ASYNC_ALIAS
from amsdal_data.aliases.db import POSTGRES_STATE_ALIAS
from amsdal_data.aliases.db import POSTGRES_STATE_ASYNC_ALIAS
from amsdal_data.aliases.db import SQLITE_ALIAS
from amsdal_data.aliases.db import SQLITE_ASYNC_ALIAS
from amsdal_data.aliases.db import SQLITE_HISTORICAL_ALIAS
from amsdal_data.aliases.db import SQLITE_HISTORICAL_ASYNC_ALIAS
from amsdal_data.aliases.db import SQLITE_STATE_ALIAS
from amsdal_data.aliases.db import SQLITE_STATE_ASYNC_ALIAS
from amsdal_data.aliases.external import CACHE_ALIAS
from amsdal_data.aliases.external import CACHE_ASYNC_ALIAS
from amsdal_data.aliases.external import EMAIL_ALIAS
from amsdal_data.aliases.external import EMAIL_ASYNC_ALIAS
from amsdal_data.aliases.external import IMAP_ALIAS
from amsdal_data.aliases.external import IMAP_ASYNC_ALIAS
from amsdal_data.aliases.external import STORAGE_ALIAS
from amsdal_data.aliases.external import STORAGE_ASYNC_ALIAS

CONNECTION_BACKEND_ALIASES: dict[str, str] = {
    # Database connections
    SQLITE_ALIAS: 'amsdal_glue.SqliteConnection',
    SQLITE_STATE_ALIAS: 'amsdal_glue.SqliteConnection',
    SQLITE_HISTORICAL_ALIAS: 'amsdal_data.connections.sqlite_historical.SqliteHistoricalConnection',
    POSTGRES_HISTORICAL_ALIAS: 'amsdal_data.connections.postgresql_historical.PostgresHistoricalConnection',
    POSTGRES_STATE_ALIAS: 'amsdal_data.connections.postgresql_state.PostgresStateConnection',
    SQLITE_HISTORICAL_ASYNC_ALIAS: 'amsdal_data.connections.async_sqlite_historical.AsyncSqliteHistoricalConnection',
    SQLITE_STATE_ASYNC_ALIAS: 'amsdal_glue.AsyncSqliteConnection',
    SQLITE_ASYNC_ALIAS: 'amsdal_glue.AsyncSqliteConnection',
    POSTGRES_STATE_ASYNC_ALIAS: 'amsdal_data.connections.postgresql_state.AsyncPostgresStateConnection',
    POSTGRES_HISTORICAL_ASYNC_ALIAS: 'amsdal_data.connections.postgresql_historical.AsyncPostgresHistoricalConnection',
    # External service connections
    EMAIL_ALIAS: 'amsdal_data.connections.external.email.EmailConnection',
    EMAIL_ASYNC_ALIAS: 'amsdal_data.connections.external.email.AsyncEmailConnection',
    IMAP_ALIAS: 'amsdal_data.connections.external.imap.ImapConnection',
    IMAP_ASYNC_ALIAS: 'amsdal_data.connections.external.imap.AsyncImapConnection',
    # External database connections (read-only)
    'external-sqlite-readonly': 'amsdal_data.connections.external.read_only_sqlite.ReadOnlySqliteConnection',
    # Placeholders for future external services
    STORAGE_ALIAS: 'amsdal_data.connections.external.base.ExternalServiceConnection',
    STORAGE_ASYNC_ALIAS: 'amsdal_data.connections.external.base.AsyncExternalServiceConnection',
    CACHE_ALIAS: 'amsdal_data.connections.external.base.ExternalServiceConnection',
    CACHE_ASYNC_ALIAS: 'amsdal_data.connections.external.base.AsyncExternalServiceConnection',
}
