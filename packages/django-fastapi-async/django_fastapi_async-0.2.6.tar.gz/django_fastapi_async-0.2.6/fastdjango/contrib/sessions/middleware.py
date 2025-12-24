"""
FastDjango Session Middleware.
"""

from __future__ import annotations

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from fastdjango.conf import settings


class SessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds session support to requests.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.cookie_name = settings.SESSION_COOKIE_NAME
        self.cookie_age = settings.SESSION_COOKIE_AGE
        self.cookie_httponly = settings.SESSION_COOKIE_HTTPONLY
        self.cookie_secure = settings.SESSION_COOKIE_SECURE
        self.cookie_samesite = settings.SESSION_COOKIE_SAMESITE

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get session key from cookie
        session_key = request.cookies.get(self.cookie_name)

        # Create session object
        session = await self._get_session(session_key)

        # Load session data
        await session.load()

        # Attach to request
        request.state.session = session

        # Process request
        response = await call_next(request)

        # Save session if modified
        if session.modified or session.accessed:
            await session.save()

            # Set cookie
            if session.session_key:
                response.set_cookie(
                    key=self.cookie_name,
                    value=session.session_key,
                    max_age=self.cookie_age,
                    httponly=self.cookie_httponly,
                    secure=self.cookie_secure,
                    samesite=self.cookie_samesite,
                )

        return response

    async def _get_session(self, session_key: str | None):
        """Get session backend instance."""
        engine = settings.SESSION_ENGINE

        if engine == "fastdjango.contrib.sessions.backends.signed_cookies":
            from fastdjango.contrib.sessions.backends.signed_cookies import SignedCookieSession
            return SignedCookieSession(session_key)
        else:
            # Default to database backend
            from fastdjango.contrib.sessions.backends.db import DatabaseSession
            return DatabaseSession(session_key)
