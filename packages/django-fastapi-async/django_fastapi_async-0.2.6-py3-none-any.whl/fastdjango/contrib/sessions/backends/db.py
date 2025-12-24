"""
Database session backend.
Sessions stored in database.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastdjango.db.models import Model
from fastdjango.db import fields
from fastdjango.contrib.sessions.backends.base import SessionBase


class Session(Model):
    """Session model for database-backed sessions."""

    session_key = fields.CharField(max_length=40, primary_key=True)
    session_data = fields.TextField()
    expire_date = fields.DateTimeField(index=True)

    class Meta:
        table = "fastdjango_session"


class DatabaseSession(SessionBase):
    """
    Session stored in database.
    """

    async def load(self) -> dict[str, Any]:
        """Load session data from database."""
        if not self._session_key:
            await self.create()
            return {}

        try:
            session = await Session.get_or_none(session_key=self._session_key)
            if session is None:
                await self.create()
                return {}

            # Check expiry
            if session.expire_date < datetime.utcnow():
                await self.delete()
                await self.create()
                return {}

            self._session_cache = self.decode(session.session_data)
            return self._session_cache

        except Exception:
            await self.create()
            return {}

    async def save(self, must_create: bool = False) -> None:
        """Save session data to database."""
        if self._session_key is None:
            await self.create()

        data = self.encode(self._session_cache)
        expire_date = self.get_expiry_date()

        session, created = await Session.update_or_create(
            session_key=self._session_key,
            defaults={
                "session_data": data,
                "expire_date": expire_date,
            },
        )

        self._modified = False

    async def delete(self, session_key: str | None = None) -> None:
        """Delete session from database."""
        key = session_key or self._session_key
        if key:
            await Session.filter(session_key=key).delete()

        if session_key is None:
            self._session_key = None
            self._session_cache.clear()

    async def exists(self, session_key: str) -> bool:
        """Check if session exists in database."""
        return await Session.filter(session_key=session_key).exists()

    @classmethod
    async def clear_expired(cls) -> int:
        """Delete all expired sessions. Returns count of deleted sessions."""
        count = await Session.filter(expire_date__lt=datetime.utcnow()).delete()
        return count
