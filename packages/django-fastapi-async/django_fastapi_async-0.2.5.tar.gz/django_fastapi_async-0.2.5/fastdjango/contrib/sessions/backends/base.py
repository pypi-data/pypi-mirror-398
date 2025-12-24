"""
FastDjango Session Base.
"""

from __future__ import annotations

import secrets
import json
from datetime import datetime, timedelta
from typing import Any, Iterator
from abc import ABC, abstractmethod

from fastdjango.conf import settings


class SessionBase(ABC):
    """
    Base session class.
    Similar to Django's SessionBase.
    """

    def __init__(self, session_key: str | None = None):
        self._session_key = session_key
        self._session_cache: dict[str, Any] = {}
        self._modified = False
        self._accessed = False

    @property
    def session_key(self) -> str | None:
        return self._session_key

    @property
    def modified(self) -> bool:
        return self._modified

    @modified.setter
    def modified(self, value: bool) -> None:
        self._modified = value

    @property
    def accessed(self) -> bool:
        return self._accessed

    @accessed.setter
    def accessed(self, value: bool) -> None:
        self._accessed = value

    def __contains__(self, key: str) -> bool:
        return key in self._session_cache

    def __getitem__(self, key: str) -> Any:
        self._accessed = True
        return self._session_cache[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._session_cache[key] = value
        self._modified = True

    def __delitem__(self, key: str) -> None:
        del self._session_cache[key]
        self._modified = True

    def __iter__(self) -> Iterator[str]:
        return iter(self._session_cache)

    def __len__(self) -> int:
        return len(self._session_cache)

    def get(self, key: str, default: Any = None) -> Any:
        self._accessed = True
        return self._session_cache.get(key, default)

    def pop(self, key: str, default: Any = None) -> Any:
        self._modified = True
        return self._session_cache.pop(key, default)

    def setdefault(self, key: str, value: Any) -> Any:
        if key not in self._session_cache:
            self._session_cache[key] = value
            self._modified = True
        return self._session_cache[key]

    def update(self, data: dict[str, Any]) -> None:
        self._session_cache.update(data)
        self._modified = True

    def keys(self):
        return self._session_cache.keys()

    def values(self):
        return self._session_cache.values()

    def items(self):
        return self._session_cache.items()

    def clear(self) -> None:
        self._session_cache.clear()
        self._modified = True

    def is_empty(self) -> bool:
        return not self._session_cache

    def _get_new_session_key(self) -> str:
        """Generate a new session key."""
        return secrets.token_urlsafe(32)

    def _get_session_expiry_age(self) -> int:
        """Get session expiry age in seconds."""
        return settings.SESSION_COOKIE_AGE

    def get_expiry_date(self) -> datetime:
        """Get the session expiry date."""
        return datetime.utcnow() + timedelta(seconds=self._get_session_expiry_age())

    def encode(self, data: dict[str, Any]) -> str:
        """Encode session data."""
        return json.dumps(data)

    def decode(self, data: str) -> dict[str, Any]:
        """Decode session data."""
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}

    @abstractmethod
    async def load(self) -> dict[str, Any]:
        """Load session data."""
        pass

    @abstractmethod
    async def save(self, must_create: bool = False) -> None:
        """Save session data."""
        pass

    @abstractmethod
    async def delete(self, session_key: str | None = None) -> None:
        """Delete the session."""
        pass

    @abstractmethod
    async def exists(self, session_key: str) -> bool:
        """Check if a session key exists."""
        pass

    async def create(self) -> None:
        """Create a new session."""
        while True:
            self._session_key = self._get_new_session_key()
            if not await self.exists(self._session_key):
                break
        self._modified = True

    async def flush(self) -> None:
        """Remove the current session and create a new one."""
        await self.delete()
        await self.create()
        self._session_cache.clear()

    async def cycle_key(self) -> None:
        """Create a new session key while keeping data."""
        data = dict(self._session_cache)
        await self.flush()
        self._session_cache = data
        self._modified = True
