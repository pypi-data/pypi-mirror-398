"""
Cookie-based session backend.
Sessions stored in signed cookies.
"""

from __future__ import annotations

from typing import Any
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from fastdjango.conf import settings
from fastdjango.contrib.sessions.backends.base import SessionBase


class SignedCookieSession(SessionBase):
    """
    Session stored in a signed cookie.
    No server-side storage needed.
    """

    def __init__(self, session_key: str | None = None):
        super().__init__(session_key)
        self._serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

    async def load(self) -> dict[str, Any]:
        """Load and verify session data from cookie."""
        if not self._session_key:
            return {}

        try:
            data = self._serializer.loads(
                self._session_key,
                max_age=settings.SESSION_COOKIE_AGE,
            )
            self._session_cache = data if isinstance(data, dict) else {}
            return self._session_cache
        except (BadSignature, SignatureExpired):
            # Invalid or expired signature
            await self.create()
            return {}

    async def save(self, must_create: bool = False) -> None:
        """Sign and encode session data for cookie."""
        self._session_key = self._serializer.dumps(self._session_cache)

    async def delete(self, session_key: str | None = None) -> None:
        """Clear session data."""
        self._session_key = None
        self._session_cache.clear()

    async def exists(self, session_key: str) -> bool:
        """Check if session data can be decoded."""
        try:
            self._serializer.loads(session_key, max_age=settings.SESSION_COOKIE_AGE)
            return True
        except (BadSignature, SignatureExpired):
            return False

    def get_cookie_value(self) -> str:
        """Get the signed session data for the cookie."""
        return self._session_key or ""
