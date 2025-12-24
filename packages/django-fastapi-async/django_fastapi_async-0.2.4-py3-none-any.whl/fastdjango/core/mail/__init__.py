"""
FastDjango Email Framework.
Async email sending with multiple backends.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path
from typing import Any, Sequence
import aiosmtplib

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """
    Represents an email message.

    Usage:
        msg = EmailMessage(
            subject="Hello",
            body="World",
            from_email="sender@example.com",
            to=["recipient@example.com"],
        )
        await msg.send()
    """

    subject: str = ""
    body: str = ""
    from_email: str | None = None
    to: list[str] = field(default_factory=list)
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    reply_to: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    attachments: list[tuple[str, bytes, str]] = field(default_factory=list)

    # HTML content
    html_body: str | None = None

    # Connection
    connection: EmailBackend | None = None

    def __post_init__(self):
        if self.from_email is None:
            from fastdjango.conf import settings
            self.from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost")

    def attach(self, filename: str, content: bytes, mimetype: str = "application/octet-stream"):
        """Attach a file to the email."""
        self.attachments.append((filename, content, mimetype))

    def attach_file(self, path: str | Path, mimetype: str | None = None):
        """Attach a file from disk."""
        import mimetypes

        path = Path(path)
        if mimetype is None:
            mimetype, _ = mimetypes.guess_type(str(path))
            mimetype = mimetype or "application/octet-stream"

        with open(path, "rb") as f:
            content = f.read()

        self.attach(path.name, content, mimetype)

    def message(self) -> MIMEMultipart:
        """Build the MIME message."""
        if self.html_body:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(self.body, "plain", "utf-8"))
            msg.attach(MIMEText(self.html_body, "html", "utf-8"))
        else:
            msg = MIMEMultipart()
            msg.attach(MIMEText(self.body, "plain", "utf-8"))

        msg["Subject"] = self.subject
        msg["From"] = self.from_email
        msg["To"] = ", ".join(self.to)

        if self.cc:
            msg["Cc"] = ", ".join(self.cc)
        if self.reply_to:
            msg["Reply-To"] = ", ".join(self.reply_to)

        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()

        # Custom headers
        for key, value in self.headers.items():
            msg[key] = value

        # Attachments
        for filename, content, mimetype in self.attachments:
            maintype, subtype = mimetype.split("/", 1)
            attachment = MIMEBase(maintype, subtype)
            attachment.set_payload(content)

            from email import encoders
            encoders.encode_base64(attachment)

            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=filename,
            )
            msg.attach(attachment)

        return msg

    def recipients(self) -> list[str]:
        """Get all recipients."""
        return self.to + self.cc + self.bcc

    async def send(self, fail_silently: bool = False) -> int:
        """
        Send the email.

        Returns:
            Number of messages sent (0 or 1)
        """
        connection = self.connection or get_connection()
        return await connection.send_messages([self], fail_silently=fail_silently)


class EmailBackend(ABC):
    """
    Abstract base class for email backends.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 25,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = False,
        use_ssl: bool = False,
        timeout: int = 30,
        fail_silently: bool = False,
        **kwargs: Any,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.fail_silently = fail_silently

    @abstractmethod
    async def send_messages(
        self, email_messages: Sequence[EmailMessage], fail_silently: bool = False
    ) -> int:
        """Send one or more email messages. Returns number sent."""
        pass

    async def open(self) -> bool:
        """Open a connection to the email server."""
        return True

    async def close(self) -> None:
        """Close the connection to the email server."""
        pass


class SMTPBackend(EmailBackend):
    """
    SMTP email backend using aiosmtplib.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._connection: aiosmtplib.SMTP | None = None

    async def open(self) -> bool:
        """Open connection to SMTP server."""
        if self._connection is not None:
            return True

        try:
            self._connection = aiosmtplib.SMTP(
                hostname=self.host,
                port=self.port,
                timeout=self.timeout,
                use_tls=self.use_ssl,
            )
            await self._connection.connect()

            if self.use_tls and not self.use_ssl:
                await self._connection.starttls()

            if self.username and self.password:
                await self._connection.login(self.username, self.password)

            return True
        except Exception as e:
            if not self.fail_silently:
                raise
            logger.error(f"Failed to connect to SMTP server: {e}")
            return False

    async def close(self) -> None:
        """Close SMTP connection."""
        if self._connection is not None:
            try:
                await self._connection.quit()
            except Exception:
                pass
            self._connection = None

    async def send_messages(
        self, email_messages: Sequence[EmailMessage], fail_silently: bool = False
    ) -> int:
        """Send email messages via SMTP."""
        if not email_messages:
            return 0

        fail_silently = fail_silently or self.fail_silently
        num_sent = 0

        try:
            if not await self.open():
                return 0

            for message in email_messages:
                try:
                    mime_message = message.message()
                    await self._connection.send_message(mime_message)
                    num_sent += 1
                except Exception as e:
                    if not fail_silently:
                        raise
                    logger.error(f"Failed to send email: {e}")

        finally:
            await self.close()

        return num_sent


class ConsoleBackend(EmailBackend):
    """
    Email backend that writes to console/stdout.
    Useful for development.
    """

    async def send_messages(
        self, email_messages: Sequence[EmailMessage], fail_silently: bool = False
    ) -> int:
        """Print emails to console."""
        for message in email_messages:
            print("-" * 60)
            print(f"From: {message.from_email}")
            print(f"To: {', '.join(message.to)}")
            if message.cc:
                print(f"Cc: {', '.join(message.cc)}")
            print(f"Subject: {message.subject}")
            print("-" * 60)
            print(message.body)
            if message.html_body:
                print("-" * 30)
                print("HTML:")
                print(message.html_body)
            print("-" * 60)
            print()

        return len(email_messages)


class FileBackend(EmailBackend):
    """
    Email backend that writes to files.
    Useful for development and testing.
    """

    def __init__(self, file_path: str = "emails", **kwargs: Any):
        super().__init__(**kwargs)
        self.file_path = Path(file_path)
        self.file_path.mkdir(parents=True, exist_ok=True)

    async def send_messages(
        self, email_messages: Sequence[EmailMessage], fail_silently: bool = False
    ) -> int:
        """Write emails to files."""
        import aiofiles
        from datetime import datetime

        for i, message in enumerate(email_messages):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.file_path / f"{timestamp}_{i}.eml"

            mime_message = message.message()

            async with aiofiles.open(filename, "w") as f:
                await f.write(mime_message.as_string())

        return len(email_messages)


class InMemoryBackend(EmailBackend):
    """
    Email backend that stores emails in memory.
    Useful for testing.
    """

    outbox: list[EmailMessage] = []

    async def send_messages(
        self, email_messages: Sequence[EmailMessage], fail_silently: bool = False
    ) -> int:
        """Store emails in memory."""
        self.outbox.extend(email_messages)
        return len(email_messages)

    @classmethod
    def clear(cls):
        """Clear the outbox."""
        cls.outbox = []


class DummyBackend(EmailBackend):
    """
    Email backend that does nothing.
    Useful when you want to disable email sending.
    """

    async def send_messages(
        self, email_messages: Sequence[EmailMessage], fail_silently: bool = False
    ) -> int:
        """Do nothing, return count."""
        return len(email_messages)


# Connection management
_connection: EmailBackend | None = None


def get_connection(
    backend: str | None = None,
    fail_silently: bool = False,
    **kwargs: Any,
) -> EmailBackend:
    """
    Get an email connection.

    Args:
        backend: Backend class name or alias
        fail_silently: Whether to suppress exceptions
        **kwargs: Additional backend arguments
    """
    from fastdjango.conf import settings

    # Get settings
    email_settings = {
        "host": getattr(settings, "EMAIL_HOST", "localhost"),
        "port": getattr(settings, "EMAIL_PORT", 25),
        "username": getattr(settings, "EMAIL_HOST_USER", None),
        "password": getattr(settings, "EMAIL_HOST_PASSWORD", None),
        "use_tls": getattr(settings, "EMAIL_USE_TLS", False),
        "use_ssl": getattr(settings, "EMAIL_USE_SSL", False),
        "timeout": getattr(settings, "EMAIL_TIMEOUT", 30),
        "fail_silently": fail_silently,
    }
    email_settings.update(kwargs)

    # Determine backend
    if backend is None:
        backend = getattr(settings, "EMAIL_BACKEND", "smtp")

    backends = {
        "smtp": SMTPBackend,
        "console": ConsoleBackend,
        "file": FileBackend,
        "memory": InMemoryBackend,
        "dummy": DummyBackend,
    }

    backend_class = backends.get(backend, SMTPBackend)
    return backend_class(**email_settings)


# Convenience functions
async def send_mail(
    subject: str,
    message: str,
    from_email: str | None = None,
    recipient_list: list[str] | None = None,
    fail_silently: bool = False,
    auth_user: str | None = None,
    auth_password: str | None = None,
    connection: EmailBackend | None = None,
    html_message: str | None = None,
) -> int:
    """
    Send a single email.

    Usage:
        await send_mail(
            "Subject",
            "Body text",
            "from@example.com",
            ["to@example.com"],
        )
    """
    if recipient_list is None:
        recipient_list = []

    connection = connection or get_connection(
        username=auth_user,
        password=auth_password,
        fail_silently=fail_silently,
    )

    mail = EmailMessage(
        subject=subject,
        body=message,
        from_email=from_email,
        to=recipient_list,
        html_body=html_message,
        connection=connection,
    )

    return await mail.send(fail_silently=fail_silently)


async def send_mass_mail(
    datatuple: Sequence[tuple[str, str, str, list[str]]],
    fail_silently: bool = False,
    auth_user: str | None = None,
    auth_password: str | None = None,
    connection: EmailBackend | None = None,
) -> int:
    """
    Send multiple emails efficiently.

    Args:
        datatuple: Sequence of (subject, message, from_email, recipient_list) tuples
    """
    connection = connection or get_connection(
        username=auth_user,
        password=auth_password,
        fail_silently=fail_silently,
    )

    messages = [
        EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=recipients,
            connection=connection,
        )
        for subject, message, from_email, recipients in datatuple
    ]

    return await connection.send_messages(messages, fail_silently=fail_silently)


async def mail_admins(
    subject: str,
    message: str,
    fail_silently: bool = False,
    connection: EmailBackend | None = None,
    html_message: str | None = None,
) -> int:
    """Send email to site admins."""
    from fastdjango.conf import settings

    admins = getattr(settings, "ADMINS", [])
    if not admins:
        return 0

    recipient_list = [email for name, email in admins]
    subject_prefix = getattr(settings, "EMAIL_SUBJECT_PREFIX", "[FastDjango] ")

    return await send_mail(
        subject=f"{subject_prefix}{subject}",
        message=message,
        recipient_list=recipient_list,
        fail_silently=fail_silently,
        connection=connection,
        html_message=html_message,
    )


async def mail_managers(
    subject: str,
    message: str,
    fail_silently: bool = False,
    connection: EmailBackend | None = None,
    html_message: str | None = None,
) -> int:
    """Send email to site managers."""
    from fastdjango.conf import settings

    managers = getattr(settings, "MANAGERS", [])
    if not managers:
        return 0

    recipient_list = [email for name, email in managers]
    subject_prefix = getattr(settings, "EMAIL_SUBJECT_PREFIX", "[FastDjango] ")

    return await send_mail(
        subject=f"{subject_prefix}{subject}",
        message=message,
        recipient_list=recipient_list,
        fail_silently=fail_silently,
        connection=connection,
        html_message=html_message,
    )


__all__ = [
    "EmailMessage",
    "EmailBackend",
    "SMTPBackend",
    "ConsoleBackend",
    "FileBackend",
    "InMemoryBackend",
    "DummyBackend",
    "get_connection",
    "send_mail",
    "send_mass_mail",
    "mail_admins",
    "mail_managers",
]
