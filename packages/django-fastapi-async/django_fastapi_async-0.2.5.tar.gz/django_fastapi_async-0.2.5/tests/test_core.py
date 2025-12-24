"""
Tests for core functionality.
"""

import pytest


class TestSettings:
    """Test settings configuration."""

    def test_settings_defaults(self, settings):
        """Test that default settings are loaded."""
        assert settings.DEBUG is True
        assert settings.SECRET_KEY == "test-secret-key-for-testing-only"

    def test_settings_get(self, settings):
        """Test settings.get() method."""
        assert settings.get("DEBUG") is True
        assert settings.get("NONEXISTENT", "default") == "default"


class TestExceptions:
    """Test custom exceptions."""

    def test_http404(self):
        """Test Http404 exception."""
        from fastdjango.core.exceptions import Http404

        exc = Http404("Not found")
        assert str(exc) == "Not found"
        assert exc.message == "Not found"

    def test_permission_denied(self):
        """Test PermissionDenied exception."""
        from fastdjango.core.exceptions import PermissionDenied

        exc = PermissionDenied("Access denied")
        assert str(exc) == "Access denied"

    def test_redirect(self):
        """Test Redirect exception."""
        from fastdjango.core.exceptions import Redirect

        exc = Redirect("/login", status_code=302)
        assert exc.url == "/login"
        assert exc.status_code == 302

    def test_validation_error(self):
        """Test ValidationError exception."""
        from fastdjango.core.exceptions import ValidationError

        # Test with dict
        exc = ValidationError({"field": ["Error 1", "Error 2"]})
        assert exc.error_dict == {"field": ["Error 1", "Error 2"]}

        # Test with list
        exc = ValidationError(["Error 1", "Error 2"])
        assert exc.error_list == ["Error 1", "Error 2"]

        # Test with string
        exc = ValidationError("Single error")
        assert exc.error_list == ["Single error"]


class TestSignals:
    """Test signal system."""

    @pytest.mark.asyncio
    async def test_signal_send(self):
        """Test sending signals."""
        from fastdjango.core.signals import Signal

        signal = Signal()
        received = []

        @signal.connect
        async def receiver(sender, **kwargs):
            received.append(kwargs.get("data"))

        await signal.send(sender=None, data="test")
        assert received == ["test"]

    @pytest.mark.asyncio
    async def test_signal_disconnect(self):
        """Test disconnecting signals."""
        from fastdjango.core.signals import Signal

        signal = Signal()
        received = []

        async def receiver(sender, **kwargs):
            received.append(kwargs.get("data"))

        signal.connect(receiver)
        signal.disconnect(receiver)

        await signal.send(sender=None, data="test")
        assert received == []
