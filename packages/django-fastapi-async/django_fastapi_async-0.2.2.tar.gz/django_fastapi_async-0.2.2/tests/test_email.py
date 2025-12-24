"""
Tests for email framework.
"""

import pytest


class TestEmailMessage:
    """Test EmailMessage class."""

    def test_create_message(self):
        """Test creating an email message."""
        from fastdjango.core.mail import EmailMessage

        msg = EmailMessage(
            subject="Test Subject",
            body="Test body content",
            from_email="sender@example.com",
            to=["recipient@example.com"],
        )

        assert msg.subject == "Test Subject"
        assert msg.body == "Test body content"
        assert msg.from_email == "sender@example.com"
        assert msg.to == ["recipient@example.com"]

    def test_recipients(self):
        """Test getting all recipients."""
        from fastdjango.core.mail import EmailMessage

        msg = EmailMessage(
            subject="Test",
            body="Body",
            to=["to@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )

        recipients = msg.recipients()
        assert "to@example.com" in recipients
        assert "cc@example.com" in recipients
        assert "bcc@example.com" in recipients

    def test_attach(self):
        """Test attaching content."""
        from fastdjango.core.mail import EmailMessage

        msg = EmailMessage(subject="Test", body="Body")
        msg.attach("file.txt", b"content", "text/plain")

        assert len(msg.attachments) == 1
        filename, content, mimetype = msg.attachments[0]
        assert filename == "file.txt"
        assert content == b"content"
        assert mimetype == "text/plain"

    def test_html_message(self):
        """Test HTML message."""
        from fastdjango.core.mail import EmailMessage

        msg = EmailMessage(
            subject="Test",
            body="Plain text",
            html_body="<h1>HTML Content</h1>",
        )

        mime = msg.message()
        assert mime.is_multipart()

    def test_message_headers(self):
        """Test custom headers."""
        from fastdjango.core.mail import EmailMessage

        msg = EmailMessage(
            subject="Test",
            body="Body",
            from_email="from@example.com",
            to=["to@example.com"],
            headers={"X-Custom": "value"},
        )

        mime = msg.message()
        assert mime["X-Custom"] == "value"


class TestInMemoryBackend:
    """Test in-memory email backend."""

    @pytest.mark.asyncio
    async def test_send_stores_message(self):
        """Test that messages are stored in outbox."""
        from fastdjango.core.mail import EmailMessage, InMemoryBackend

        backend = InMemoryBackend()
        InMemoryBackend.clear()

        msg = EmailMessage(
            subject="Test",
            body="Body",
            from_email="from@example.com",
            to=["to@example.com"],
        )

        count = await backend.send_messages([msg])
        assert count == 1
        assert len(InMemoryBackend.outbox) == 1
        assert InMemoryBackend.outbox[0].subject == "Test"

    @pytest.mark.asyncio
    async def test_clear_outbox(self):
        """Test clearing the outbox."""
        from fastdjango.core.mail import InMemoryBackend, EmailMessage

        backend = InMemoryBackend()
        msg = EmailMessage(subject="Test", body="Body")
        await backend.send_messages([msg])

        InMemoryBackend.clear()
        assert len(InMemoryBackend.outbox) == 0


class TestConsoleBackend:
    """Test console email backend."""

    @pytest.mark.asyncio
    async def test_send_prints_message(self, capsys):
        """Test that messages are printed to console."""
        from fastdjango.core.mail import EmailMessage, ConsoleBackend

        backend = ConsoleBackend()
        msg = EmailMessage(
            subject="Test Subject",
            body="Test body",
            from_email="from@example.com",
            to=["to@example.com"],
        )

        count = await backend.send_messages([msg])
        assert count == 1

        captured = capsys.readouterr()
        assert "Test Subject" in captured.out
        assert "Test body" in captured.out
        assert "from@example.com" in captured.out


class TestDummyBackend:
    """Test dummy email backend."""

    @pytest.mark.asyncio
    async def test_send_does_nothing(self):
        """Test that dummy backend does nothing but returns count."""
        from fastdjango.core.mail import EmailMessage, DummyBackend

        backend = DummyBackend()
        msg = EmailMessage(subject="Test", body="Body")

        count = await backend.send_messages([msg])
        assert count == 1


class TestSendMail:
    """Test send_mail function."""

    @pytest.mark.asyncio
    async def test_send_mail(self):
        """Test send_mail convenience function."""
        from fastdjango.core.mail import send_mail, InMemoryBackend

        InMemoryBackend.clear()
        backend = InMemoryBackend()

        count = await send_mail(
            subject="Hello",
            message="World",
            from_email="from@example.com",
            recipient_list=["to@example.com"],
            connection=backend,
        )

        assert count == 1
        assert len(InMemoryBackend.outbox) == 1
