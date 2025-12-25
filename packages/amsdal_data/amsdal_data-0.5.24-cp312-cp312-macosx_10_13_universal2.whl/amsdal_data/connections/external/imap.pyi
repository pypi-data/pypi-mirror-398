from _typeshed import Incomplete
from amsdal_data.connections.external.base import AsyncExternalServiceConnection as AsyncExternalServiceConnection, ExternalServiceConnection as ExternalServiceConnection
from email.message import Message
from typing import Any

logger: Incomplete

class ImapConnection(ExternalServiceConnection):
    """
    IMAP email connection for reading emails.

    Supports both SSL/TLS and non-SSL connections.

    Example usage:
        connection = ImapConnection()
        connection.connect(
            host='imap.gmail.com',
            port=993,
            username='user@gmail.com',
            password='password',
            use_ssl=True
        )
        emails = connection.fetch_emails(folder='INBOX', limit=10)
        folders = connection.get_folders()
        connection.disconnect()
    """
    _host: str | None
    _port: int | None
    _username: str | None
    _password: str | None
    _use_ssl: bool
    _current_folder: str | None
    def __init__(self) -> None: ...
    _connection: Incomplete
    _is_connected: bool
    def connect(self, host: str, port: int = 993, username: str | None = None, password: str | None = None, *, use_ssl: bool = True, **kwargs: Any) -> None:
        """
        Establish IMAP connection.

        Args:
            host: IMAP server hostname
            port: IMAP server port (993 for SSL, 143 for plain)
            username: IMAP username (optional)
            password: IMAP password (optional)
            use_ssl: Use SSL/TLS (default True)
            **kwargs: Additional IMAP connection parameters
        """
    def disconnect(self) -> None:
        """Close the IMAP connection."""
    def select_folder(self, folder: str = 'INBOX', *, readonly: bool = True) -> dict[str, Any]:
        """
        Select a mailbox folder.

        Args:
            folder: Folder name (default 'INBOX')
            readonly: Open folder in readonly mode (default True)

        Returns:
            dict: Folder information including message count

        Raises:
            ConnectionError: If not connected or folder selection fails
        """
    def get_folders(self) -> list[str]:
        """
        Get list of available mailbox folders.

        Returns:
            list[str]: List of folder names

        Raises:
            ConnectionError: If not connected
        """
    def fetch_emails(self, folder: str = 'INBOX', criteria: str = 'ALL', limit: int | None = None) -> list[dict[str, Any]]:
        '''
        Fetch emails from a folder.

        Args:
            folder: Folder name (default \'INBOX\')
            criteria: Search criteria (default \'ALL\'). Examples:
                - \'ALL\': All messages
                - \'UNSEEN\': Unread messages
                - \'SEEN\': Read messages
                - \'SUBJECT "keyword"\': Messages with keyword in subject
                - \'FROM "email@example.com"\': Messages from specific sender
            limit: Maximum number of emails to fetch (optional)

        Returns:
            list[dict]: List of email dictionaries with keys:
                - uid: Email unique ID
                - subject: Email subject
                - from: Sender email address
                - to: Recipient email address(es)
                - date: Email date
                - body: Email body (plain text if available)
                - html_body: Email HTML body (if available)

        Raises:
            ConnectionError: If not connected
        '''
    def _parse_email(self, msg: Message, uid: str) -> dict[str, Any]:
        """
        Parse email message into a dictionary.

        Args:
            msg: Email message object
            uid: Email unique ID

        Returns:
            dict: Email information
        """
    def _decode_header(self, header: str | None) -> str:
        """
        Decode email header.

        Args:
            header: Header string

        Returns:
            str: Decoded header
        """
    @property
    def is_alive(self) -> bool:
        """
        Check if the IMAP connection is alive.

        Returns:
            bool: True if connection is alive, False otherwise
        """

class AsyncImapConnection(AsyncExternalServiceConnection):
    """
    Async IMAP email connection for reading emails.

    Example usage:
        connection = AsyncImapConnection()
        await connection.connect(
            host='imap.gmail.com',
            port=993,
            username='user@gmail.com',
            password='password',
            use_ssl=True
        )
        emails = await connection.fetch_emails(folder='INBOX', limit=10)
        folders = await connection.get_folders()
        await connection.disconnect()
    """
    _host: str | None
    _port: int | None
    _username: str | None
    _password: str | None
    _use_ssl: bool
    _current_folder: str | None
    def __init__(self) -> None: ...
    _connection: Incomplete
    _is_connected: bool
    async def connect(self, host: str, port: int = 993, username: str | None = None, password: str | None = None, *, use_ssl: bool = True, **kwargs: Any) -> None:
        """
        Establish async IMAP connection.

        Args:
            host: IMAP server hostname
            port: IMAP server port (993 for SSL, 143 for plain)
            username: IMAP username (optional)
            password: IMAP password (optional)
            use_ssl: Use SSL/TLS (default True)
            **kwargs: Additional IMAP connection parameters
        """
    async def disconnect(self) -> None:
        """Close the async IMAP connection."""
    async def select_folder(self, folder: str = 'INBOX', *, readonly: bool = True) -> dict[str, Any]:
        """
        Select a mailbox folder.

        Args:
            folder: Folder name (default 'INBOX')
            readonly: Open folder in readonly mode (default True)

        Returns:
            dict: Folder information including message count

        Raises:
            ConnectionError: If not connected or folder selection fails
        """
    async def get_folders(self) -> list[str]:
        """
        Get list of available mailbox folders.

        Returns:
            list[str]: List of folder names

        Raises:
            ConnectionError: If not connected
        """
    async def fetch_emails(self, folder: str = 'INBOX', criteria: str = 'ALL', limit: int | None = None) -> list[dict[str, Any]]:
        '''
        Fetch emails from a folder.

        Args:
            folder: Folder name (default \'INBOX\')
            criteria: Search criteria (default \'ALL\'). Examples:
                - \'ALL\': All messages
                - \'UNSEEN\': Unread messages
                - \'SEEN\': Read messages
                - \'SUBJECT "keyword"\': Messages with keyword in subject
                - \'FROM "email@example.com"\': Messages from specific sender
            limit: Maximum number of emails to fetch (optional)

        Returns:
            list[dict]: List of email dictionaries with keys:
                - uid: Email unique ID
                - subject: Email subject
                - from: Sender email address
                - to: Recipient email address(es)
                - date: Email date
                - body: Email body (plain text if available)
                - html_body: Email HTML body (if available)

        Raises:
            ConnectionError: If not connected
        '''
    def _parse_email(self, msg: Message, uid: str) -> dict[str, Any]:
        """
        Parse email message into a dictionary.

        Args:
            msg: Email message object
            uid: Email unique ID

        Returns:
            dict: Email information
        """
    def _decode_header(self, header: str | None) -> str:
        """
        Decode email header.

        Args:
            header: Header string

        Returns:
            str: Decoded header
        """
    @property
    async def is_alive(self) -> bool:
        """
        Check if the async IMAP connection is alive.

        Returns:
            bool: True if connection is alive, False otherwise
        """
