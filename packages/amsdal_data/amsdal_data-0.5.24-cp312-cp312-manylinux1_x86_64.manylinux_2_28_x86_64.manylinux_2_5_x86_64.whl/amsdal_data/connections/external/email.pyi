from _typeshed import Incomplete
from amsdal_data.connections.external.base import AsyncExternalServiceConnection as AsyncExternalServiceConnection, ExternalServiceConnection as ExternalServiceConnection
from typing import Any

logger: Incomplete

class EmailConnection(ExternalServiceConnection):
    """
    SMTP email connection for sending emails.

    Supports both SSL/TLS and STARTTLS connections.

    Example usage:
        connection = EmailConnection()
        connection.connect(
            host='smtp.gmail.com',
            port=587,
            username='user@gmail.com',
            password='password',
            use_tls=True
        )
        connection.send_email(
            from_addr='user@gmail.com',
            to_addrs=['recipient@example.com'],
            subject='Hello',
            body='Hello World',
            html_body='<p>Hello World</p>'
        )
        connection.disconnect()
    """
    _host: str | None
    _port: int | None
    _username: str | None
    _password: str | None
    _use_tls: bool
    _use_ssl: bool
    def __init__(self) -> None: ...
    _connection: Incomplete
    _is_connected: bool
    def connect(self, host: str, port: int = 587, username: str | None = None, password: str | None = None, *, use_tls: bool = True, use_ssl: bool = False, **kwargs: Any) -> None:
        """
        Establish SMTP connection.

        Args:
            host: SMTP server hostname
            port: SMTP server port (587 for TLS, 465 for SSL, 25 for plain)
            username: SMTP username (optional)
            password: SMTP password (optional)
            use_tls: Use STARTTLS (default True)
            use_ssl: Use SSL from the start (default False)
            **kwargs: Additional SMTP connection parameters
        """
    def disconnect(self) -> None:
        """Close the SMTP connection."""
    def send_email(self, from_addr: str, to_addrs: list[str] | str, subject: str, body: str | None = None, html_body: str | None = None, cc_addrs: list[str] | None = None, bcc_addrs: list[str] | None = None) -> None:
        """
        Send an email.

        Args:
            from_addr: Sender email address
            to_addrs: Recipient email address(es)
            subject: Email subject
            body: Plain text body (optional if html_body provided)
            html_body: HTML body (optional)
            cc_addrs: CC recipients (optional)
            bcc_addrs: BCC recipients (optional)

        Raises:
            ConnectionError: If not connected
            ValueError: If neither body nor html_body is provided
        """
    @property
    def is_alive(self) -> bool:
        """
        Check if the SMTP connection is alive.

        Returns:
            bool: True if connection is alive, False otherwise
        """

class AsyncEmailConnection(AsyncExternalServiceConnection):
    """
    Async SMTP email connection for sending emails.

    Example usage:
        connection = AsyncEmailConnection()
        await connection.connect(
            host='smtp.gmail.com',
            port=587,
            username='user@gmail.com',
            password='password',
            use_tls=True
        )
        await connection.send_email(
            from_addr='user@gmail.com',
            to_addrs=['recipient@example.com'],
            subject='Hello',
            body='Hello World'
        )
        await connection.disconnect()
    """
    _host: str | None
    _port: int | None
    _username: str | None
    _password: str | None
    _use_tls: bool
    _use_ssl: bool
    def __init__(self) -> None: ...
    _connection: Incomplete
    _is_connected: bool
    async def connect(self, host: str, port: int = 587, username: str | None = None, password: str | None = None, *, use_tls: bool = True, use_ssl: bool = False, **kwargs: Any) -> None:
        """
        Establish async SMTP connection.

        Args:
            host: SMTP server hostname
            port: SMTP server port
            username: SMTP username (optional)
            password: SMTP password (optional)
            use_tls: Use STARTTLS (default True)
            use_ssl: Use SSL from the start (default False)
            **kwargs: Additional SMTP connection parameters
        """
    async def disconnect(self) -> None:
        """Close the async SMTP connection."""
    async def send_email(self, from_addr: str, to_addrs: list[str] | str, subject: str, body: str | None = None, html_body: str | None = None, cc_addrs: list[str] | None = None, bcc_addrs: list[str] | None = None) -> None:
        """
        Send an email asynchronously.

        Args:
            from_addr: Sender email address
            to_addrs: Recipient email address(es)
            subject: Email subject
            body: Plain text body (optional if html_body provided)
            html_body: HTML body (optional)
            cc_addrs: CC recipients (optional)
            bcc_addrs: BCC recipients (optional)

        Raises:
            ConnectionError: If not connected
            ValueError: If neither body nor html_body is provided
        """
    @property
    async def is_alive(self) -> bool:
        """
        Check if the async SMTP connection is alive.

        Returns:
            bool: True if connection is alive, False otherwise
        """
