"""
FastDjango Auth Middleware.
"""

from __future__ import annotations

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from fastdjango.contrib.auth.models import AnonymousUser


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds user to request.state.

    Sets request.state.user to the authenticated user or AnonymousUser.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Try to get user from session
        user = await self._get_user_from_session(request)

        # If no session user, try token auth
        if user is None or not getattr(user, "is_authenticated", False):
            user = await self._get_user_from_token(request)

        # Default to anonymous
        if user is None:
            user = AnonymousUser()

        # Attach to request
        request.state.user = user

        return await call_next(request)

    async def _get_user_from_session(self, request: Request):
        """Get user from session."""
        from fastdjango.contrib.auth.models import User

        session = getattr(request.state, "session", None)
        if session is None:
            return None

        user_id = session.get("_auth_user_id")
        if user_id is None:
            return None

        return await User.get_or_none(id=user_id, is_active=True)

    async def _get_user_from_token(self, request: Request):
        """Get user from Authorization header (JWT)."""
        from fastdjango.contrib.auth.backends import TokenBackend

        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix
        backend = TokenBackend()
        return await backend.authenticate(request=request, token=token)
