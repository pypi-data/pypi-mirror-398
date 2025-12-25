import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from amsdal_data.connections.external.base import AsyncExternalServiceConnection
from amsdal_data.connections.external.base import ExternalServiceConnection

logger = logging.getLogger(__name__)


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

    def __init__(self) -> None:
        super().__init__()
        self._host: str | None = None
        self._port: int | None = None
        self._username: str | None = None
        self._password: str | None = None
        self._use_tls: bool = False
        self._use_ssl: bool = False

    def connect(
        self,
        host: str,
        port: int = 587,
        username: str | None = None,
        password: str | None = None,
        *,
        use_tls: bool = True,
        use_ssl: bool = False,
        **kwargs: Any,
    ) -> None:
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
        if self._is_connected:
            msg = 'Already connected'
            raise ConnectionError(msg)

        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._use_ssl = use_ssl

        try:
            if use_ssl:
                context = ssl.create_default_context()
                self._connection = smtplib.SMTP_SSL(host, port, context=context, **kwargs)
            else:
                self._connection = smtplib.SMTP(host, port, **kwargs)

            if use_tls and not use_ssl:
                context = ssl.create_default_context()
                self._connection.starttls(context=context)

            if username and password:
                self._connection.login(username, password)

            self._is_connected = True
        except Exception as e:
            msg = f'Failed to connect to SMTP server: {e}'
            raise ConnectionError(msg) from e

    def disconnect(self) -> None:
        """Close the SMTP connection."""
        if self._connection:
            try:
                self._connection.quit()
            except (OSError, smtplib.SMTPException):
                # Connection may already be closed or in bad state
                pass
            finally:
                self._connection = None
                self._is_connected = False

    def send_email(
        self,
        from_addr: str,
        to_addrs: list[str] | str,
        subject: str,
        body: str | None = None,
        html_body: str | None = None,
        cc_addrs: list[str] | None = None,
        bcc_addrs: list[str] | None = None,
    ) -> None:
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
        if not self._is_connected:
            msg = 'Not connected to SMTP server'
            raise ConnectionError(msg)

        if not body and not html_body:
            msg = 'Either body or html_body must be provided'
            raise ValueError(msg)

        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addrs) if isinstance(to_addrs, list) else to_addrs
        msg['Subject'] = subject

        if cc_addrs:
            msg['Cc'] = ', '.join(cc_addrs)

        # Add plain text part
        if body:
            msg.attach(MIMEText(body, 'plain'))

        # Add HTML part
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))

        # Prepare recipients
        all_recipients = []
        if isinstance(to_addrs, str):
            all_recipients.append(to_addrs)
        else:
            all_recipients.extend(to_addrs)

        if cc_addrs:
            all_recipients.extend(cc_addrs)
        if bcc_addrs:
            all_recipients.extend(bcc_addrs)

        # Send
        self._connection.sendmail(from_addr, all_recipients, msg.as_string())

    @property
    def is_alive(self) -> bool:
        """
        Check if the SMTP connection is alive.

        Returns:
            bool: True if connection is alive, False otherwise
        """
        if not self._is_connected:
            return False

        try:
            # Try to send NOOP command
            status, _ = self._connection.noop()
            return status == 250  # noqa: PLR2004
        except Exception:
            return False


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

    def __init__(self) -> None:
        super().__init__()
        self._host: str | None = None
        self._port: int | None = None
        self._username: str | None = None
        self._password: str | None = None
        self._use_tls: bool = False
        self._use_ssl: bool = False

    async def connect(
        self,
        host: str,
        port: int = 587,
        username: str | None = None,
        password: str | None = None,
        *,
        use_tls: bool = True,
        use_ssl: bool = False,
        **kwargs: Any,
    ) -> None:
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
        try:
            import aiosmtplib
        except ImportError:
            msg = 'aiosmtplib is required for AsyncEmailConnection. Install it with: pip install aiosmtplib'
            raise ImportError(msg) from None

        if self._is_connected:
            msg = 'Already connected'
            raise ConnectionError(msg)

        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._use_ssl = use_ssl

        try:
            if use_ssl:
                self._connection = aiosmtplib.SMTP(hostname=host, port=port, use_tls=True, **kwargs)
            else:
                self._connection = aiosmtplib.SMTP(hostname=host, port=port, use_tls=False, **kwargs)

            await self._connection.connect()

            if use_tls and not use_ssl:
                await self._connection.starttls()

            if username and password:
                await self._connection.login(username, password)

            self._is_connected = True
        except Exception as e:
            msg = f'Failed to connect to SMTP server: {e}'
            raise ConnectionError(msg) from e

    async def disconnect(self) -> None:
        """Close the async SMTP connection."""
        if self._connection:
            try:
                await self._connection.quit()
            except (OSError, Exception) as e:
                # Connection may already be closed or in bad state
                # Catch generic Exception since aiosmtplib may not be imported
                logger.debug(f'Cought error on attempt of closing connection: {e}')
            finally:
                self._connection = None
                self._is_connected = False

    async def send_email(
        self,
        from_addr: str,
        to_addrs: list[str] | str,
        subject: str,
        body: str | None = None,
        html_body: str | None = None,
        cc_addrs: list[str] | None = None,
        bcc_addrs: list[str] | None = None,
    ) -> None:
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
        if not self._is_connected:
            msg = 'Not connected to SMTP server'
            raise ConnectionError(msg)

        if not body and not html_body:
            msg = 'Either body or html_body must be provided'
            raise ValueError(msg)

        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addrs) if isinstance(to_addrs, list) else to_addrs
        msg['Subject'] = subject

        if cc_addrs:
            msg['Cc'] = ', '.join(cc_addrs)

        # Add plain text part
        if body:
            msg.attach(MIMEText(body, 'plain'))

        # Add HTML part
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))

        # Prepare recipients
        all_recipients = []
        if isinstance(to_addrs, str):
            all_recipients.append(to_addrs)
        else:
            all_recipients.extend(to_addrs)

        if cc_addrs:
            all_recipients.extend(cc_addrs)
        if bcc_addrs:
            all_recipients.extend(bcc_addrs)

        # Send
        await self._connection.sendmail(from_addr, all_recipients, msg.as_string())

    @property
    async def is_alive(self) -> bool:
        """
        Check if the async SMTP connection is alive.

        Returns:
            bool: True if connection is alive, False otherwise
        """
        if not self._is_connected:
            return False

        try:
            # Try to send NOOP command
            await self._connection.noop()
            return True
        except Exception:
            return False
