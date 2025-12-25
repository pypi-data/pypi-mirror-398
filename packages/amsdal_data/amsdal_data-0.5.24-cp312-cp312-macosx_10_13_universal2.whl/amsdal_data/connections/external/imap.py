import email
import imaplib
import logging
from email.header import decode_header
from email.message import Message
from typing import Any

from amsdal_data.connections.external.base import AsyncExternalServiceConnection
from amsdal_data.connections.external.base import ExternalServiceConnection

logger = logging.getLogger(__name__)


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

    def __init__(self) -> None:
        super().__init__()
        self._host: str | None = None
        self._port: int | None = None
        self._username: str | None = None
        self._password: str | None = None
        self._use_ssl: bool = True
        self._current_folder: str | None = None

    def connect(  # type: ignore[override]
        self,
        host: str,
        port: int = 993,
        username: str | None = None,
        password: str | None = None,
        *,
        use_ssl: bool = True,
        **kwargs: Any,
    ) -> None:
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
        if self._is_connected:
            msg = 'Already connected'
            raise ConnectionError(msg)

        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_ssl = use_ssl

        try:
            if use_ssl:
                self._connection = imaplib.IMAP4_SSL(host, port, **kwargs)
            else:
                self._connection = imaplib.IMAP4(host, port, **kwargs)

            if username and password:
                status, response = self._connection.login(username, password)
                if status != 'OK':
                    msg = f'IMAP login failed: {response}'
                    raise ConnectionError(msg)

            self._is_connected = True
        except Exception as e:
            msg = f'Failed to connect to IMAP server: {e}'
            raise ConnectionError(msg) from e

    def disconnect(self) -> None:
        """Close the IMAP connection."""
        if self._connection:
            try:
                if self._current_folder:
                    self._connection.close()
                self._connection.logout()
            except (OSError, imaplib.IMAP4.error):
                # Connection may already be closed or in bad state
                pass
            finally:
                self._connection = None
                self._is_connected = False
                self._current_folder = None

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
        if not self._is_connected:
            msg = 'Not connected to IMAP server'
            raise ConnectionError(msg)

        try:
            status, data = self._connection.select(folder, readonly=readonly)
            if status != 'OK':
                msg = f'Failed to select folder {folder}: {data}'
                raise ConnectionError(msg)

            self._current_folder = folder
            message_count = int(data[0]) if data and data[0] else 0
            return {'folder': folder, 'message_count': message_count}
        except Exception as e:
            msg = f'Failed to select folder {folder}: {e}'
            raise ConnectionError(msg) from e

    def get_folders(self) -> list[str]:
        """
        Get list of available mailbox folders.

        Returns:
            list[str]: List of folder names

        Raises:
            ConnectionError: If not connected
        """
        if not self._is_connected:
            msg = 'Not connected to IMAP server'
            raise ConnectionError(msg)

        try:
            status, folders = self._connection.list()
            if status != 'OK':
                msg = f'Failed to list folders: {folders}'
                raise ConnectionError(msg)

            folder_names = []
            for folder_line in folders:
                # Parse folder list response: '(\\HasNoChildren) "/" "INBOX"'
                decoded_line = folder_line.decode() if isinstance(folder_line, bytes) else folder_line
                parts = decoded_line.split('"')
                if len(parts) >= 3:  # noqa: PLR2004
                    folder_names.append(parts[-2])
            return folder_names
        except Exception as e:
            msg = f'Failed to get folders: {e}'
            raise ConnectionError(msg) from e

    def fetch_emails(
        self,
        folder: str = 'INBOX',
        criteria: str = 'ALL',
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch emails from a folder.

        Args:
            folder: Folder name (default 'INBOX')
            criteria: Search criteria (default 'ALL'). Examples:
                - 'ALL': All messages
                - 'UNSEEN': Unread messages
                - 'SEEN': Read messages
                - 'SUBJECT "keyword"': Messages with keyword in subject
                - 'FROM "email@example.com"': Messages from specific sender
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
        """
        if not self._is_connected:
            msg = 'Not connected to IMAP server'
            raise ConnectionError(msg)

        try:
            self.select_folder(folder, readonly=True)

            # Search for messages
            status, messages = self._connection.search(None, criteria)
            if status != 'OK':
                msg = f'Failed to search emails: {messages}'
                raise ConnectionError(msg)

            email_ids = messages[0].split()
            if limit:
                email_ids = email_ids[-limit:]  # Get the most recent emails

            emails = []
            for email_id in email_ids:
                status, msg_data = self._connection.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue

                # Parse email
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        email_msg = email.message_from_bytes(response_part[1])
                        email_dict = self._parse_email(email_msg, email_id.decode())
                        emails.append(email_dict)

            return emails
        except Exception as e:
            error_msg = f'Failed to fetch emails: {e}'
            raise ConnectionError(error_msg) from e

    def _parse_email(self, msg: Message, uid: str) -> dict[str, Any]:
        """
        Parse email message into a dictionary.

        Args:
            msg: Email message object
            uid: Email unique ID

        Returns:
            dict: Email information
        """
        # Decode subject
        subject = self._decode_header(msg.get('Subject', ''))

        # Get sender and recipient
        from_addr = self._decode_header(msg.get('From', ''))
        to_addr = self._decode_header(msg.get('To', ''))
        date = msg.get('Date', '')

        # Get email body
        body = None
        html_body = None

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))

                # Skip attachments
                if 'attachment' in content_disposition:
                    continue

                if content_type == 'text/plain' and not body:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body = payload.decode('utf-8', errors='ignore')
                elif content_type == 'text/html' and not html_body:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        html_body = payload.decode('utf-8', errors='ignore')
        else:
            content_type = msg.get_content_type()
            if content_type == 'text/plain':
                payload = msg.get_payload(decode=True)
                if isinstance(payload, bytes):
                    body = payload.decode('utf-8', errors='ignore')
            elif content_type == 'text/html':
                payload = msg.get_payload(decode=True)
                if isinstance(payload, bytes):
                    html_body = payload.decode('utf-8', errors='ignore')

        return {
            'uid': uid,
            'subject': subject,
            'from': from_addr,
            'to': to_addr,
            'date': date,
            'body': body,
            'html_body': html_body,
        }

    def _decode_header(self, header: str | None) -> str:
        """
        Decode email header.

        Args:
            header: Header string

        Returns:
            str: Decoded header
        """
        if not header:
            return ''

        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
            else:
                decoded_parts.append(part)
        return ''.join(decoded_parts)

    @property
    def is_alive(self) -> bool:
        """
        Check if the IMAP connection is alive.

        Returns:
            bool: True if connection is alive, False otherwise
        """
        if not self._is_connected:
            return False

        try:
            # Try to send NOOP command
            status, _ = self._connection.noop()
            return status == 'OK'
        except Exception:
            return False


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

    def __init__(self) -> None:
        super().__init__()
        self._host: str | None = None
        self._port: int | None = None
        self._username: str | None = None
        self._password: str | None = None
        self._use_ssl: bool = True
        self._current_folder: str | None = None

    async def connect(  # type: ignore[override]
        self,
        host: str,
        port: int = 993,
        username: str | None = None,
        password: str | None = None,
        *,
        use_ssl: bool = True,
        **kwargs: Any,
    ) -> None:
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
        try:
            import aioimaplib  # type: ignore[import-not-found]
        except ImportError:
            msg = 'aioimaplib is required for AsyncImapConnection. Install it with: pip install aioimaplib'
            raise ImportError(msg) from None

        if self._is_connected:
            msg = 'Already connected'
            raise ConnectionError(msg)

        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_ssl = use_ssl

        try:
            if use_ssl:
                self._connection = aioimaplib.IMAP4_SSL(host=host, port=port, **kwargs)
            else:
                self._connection = aioimaplib.IMAP4(host=host, port=port, **kwargs)

            await self._connection.wait_hello_from_server()

            if username and password:
                response = await self._connection.login(username, password)
                if response.result != 'OK':
                    msg = f'IMAP login failed: {response}'
                    raise ConnectionError(msg)

            self._is_connected = True
        except Exception as e:
            msg = f'Failed to connect to IMAP server: {e}'
            raise ConnectionError(msg) from e

    async def disconnect(self) -> None:
        """Close the async IMAP connection."""
        if self._connection:
            try:
                if self._current_folder:
                    await self._connection.close()
                await self._connection.logout()
            except (OSError, Exception) as e:
                # Connection may already be closed or in bad state
                logger.debug(f'Caught error on attempt of closing connection: {e}')
            finally:
                self._connection = None
                self._is_connected = False
                self._current_folder = None

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
        if not self._is_connected:
            msg = 'Not connected to IMAP server'
            raise ConnectionError(msg)

        try:
            if readonly:
                response = await self._connection.select(folder)
            else:
                response = await self._connection.select(folder, readonly=False)

            if response.result != 'OK':
                msg = f'Failed to select folder {folder}: {response}'
                raise ConnectionError(msg)

            self._current_folder = folder
            message_count = int(response.lines[0]) if response.lines else 0
            return {'folder': folder, 'message_count': message_count}
        except Exception as e:
            msg = f'Failed to select folder {folder}: {e}'
            raise ConnectionError(msg) from e

    async def get_folders(self) -> list[str]:
        """
        Get list of available mailbox folders.

        Returns:
            list[str]: List of folder names

        Raises:
            ConnectionError: If not connected
        """
        if not self._is_connected:
            msg = 'Not connected to IMAP server'
            raise ConnectionError(msg)

        try:
            response = await self._connection.list()
            if response.result != 'OK':
                msg = f'Failed to list folders: {response}'
                raise ConnectionError(msg)

            folder_names = []
            for line in response.lines:
                # Parse folder list response: '(\\HasNoChildren) "/" "INBOX"'
                parts = line.split(b'"') if isinstance(line, bytes) else line.split('"')
                if len(parts) >= 3:  # noqa: PLR2004
                    folder_name = parts[-2]
                    if isinstance(folder_name, bytes):
                        folder_name = folder_name.decode()
                    folder_names.append(folder_name)
            return folder_names
        except Exception as e:
            msg = f'Failed to get folders: {e}'
            raise ConnectionError(msg) from e

    async def fetch_emails(
        self,
        folder: str = 'INBOX',
        criteria: str = 'ALL',
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch emails from a folder.

        Args:
            folder: Folder name (default 'INBOX')
            criteria: Search criteria (default 'ALL'). Examples:
                - 'ALL': All messages
                - 'UNSEEN': Unread messages
                - 'SEEN': Read messages
                - 'SUBJECT "keyword"': Messages with keyword in subject
                - 'FROM "email@example.com"': Messages from specific sender
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
        """
        if not self._is_connected:
            msg = 'Not connected to IMAP server'
            raise ConnectionError(msg)

        try:
            await self.select_folder(folder, readonly=True)

            # Search for messages
            response = await self._connection.search(criteria)
            if response.result != 'OK':
                msg = f'Failed to search emails: {response}'
                raise ConnectionError(msg)

            email_ids_str = response.lines[0].decode() if isinstance(response.lines[0], bytes) else response.lines[0]
            email_ids = email_ids_str.split()
            if limit:
                email_ids = email_ids[-limit:]  # Get the most recent emails

            emails = []
            for email_id in email_ids:
                response = await self._connection.fetch(email_id, '(RFC822)')
                if response.result != 'OK':
                    continue

                # Parse email - the response format is different in async version
                for line in response.lines:
                    if isinstance(line, bytes) and b'RFC822' in line:
                        # Extract the email data from the response
                        start = line.find(b'{')
                        if start != -1:
                            # The actual email data follows in the next lines
                            continue
                    elif isinstance(line, bytes) and len(line) > 100:  # noqa: PLR2004
                        # This is likely the email data
                        email_msg = email.message_from_bytes(line)
                        email_dict = self._parse_email(email_msg, email_id)
                        emails.append(email_dict)
                        break

            return emails
        except Exception as e:
            error_msg = f'Failed to fetch emails: {e}'
            raise ConnectionError(error_msg) from e

    def _parse_email(self, msg: Message, uid: str) -> dict[str, Any]:
        """
        Parse email message into a dictionary.

        Args:
            msg: Email message object
            uid: Email unique ID

        Returns:
            dict: Email information
        """
        # Decode subject
        subject = self._decode_header(msg.get('Subject', ''))

        # Get sender and recipient
        from_addr = self._decode_header(msg.get('From', ''))
        to_addr = self._decode_header(msg.get('To', ''))
        date = msg.get('Date', '')

        # Get email body
        body = None
        html_body = None

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))

                # Skip attachments
                if 'attachment' in content_disposition:
                    continue

                if content_type == 'text/plain' and not body:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body = payload.decode('utf-8', errors='ignore')
                elif content_type == 'text/html' and not html_body:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        html_body = payload.decode('utf-8', errors='ignore')
        else:
            content_type = msg.get_content_type()
            if content_type == 'text/plain':
                payload = msg.get_payload(decode=True)
                if isinstance(payload, bytes):
                    body = payload.decode('utf-8', errors='ignore')
            elif content_type == 'text/html':
                payload = msg.get_payload(decode=True)
                if isinstance(payload, bytes):
                    html_body = payload.decode('utf-8', errors='ignore')

        return {
            'uid': uid,
            'subject': subject,
            'from': from_addr,
            'to': to_addr,
            'date': date,
            'body': body,
            'html_body': html_body,
        }

    def _decode_header(self, header: str | None) -> str:
        """
        Decode email header.

        Args:
            header: Header string

        Returns:
            str: Decoded header
        """
        if not header:
            return ''

        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
            else:
                decoded_parts.append(part)
        return ''.join(decoded_parts)

    @property
    async def is_alive(self) -> bool:
        """
        Check if the async IMAP connection is alive.

        Returns:
            bool: True if connection is alive, False otherwise
        """
        if not self._is_connected:
            return False

        try:
            # Try to send NOOP command
            response = await self._connection.noop()
            return response.result == 'OK'
        except Exception:
            return False
