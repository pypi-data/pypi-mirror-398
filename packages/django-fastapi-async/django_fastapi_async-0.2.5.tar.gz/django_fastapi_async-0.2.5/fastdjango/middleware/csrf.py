"""
FastDjango CSRF Middleware.
"""

from __future__ import annotations

import secrets
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from fastdjango.conf import settings
from fastdjango.core.exceptions import CSRFError


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware.
    """

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or create CSRF token
        csrf_token = self._get_csrf_token(request)
        if csrf_token is None:
            csrf_token = self._generate_token()

        # Store in request state
        request.state.csrf_token = csrf_token

        # Validate for unsafe methods
        if request.method not in self.SAFE_METHODS:
            if not await self._check_csrf(request, csrf_token):
                # Skip for API endpoints with token auth
                if not self._is_api_authenticated(request):
                    raise CSRFError("CSRF token missing or invalid")

        response = await call_next(request)

        # Set CSRF cookie
        response.set_cookie(
            key=settings.CSRF_COOKIE_NAME,
            value=csrf_token,
            httponly=False,  # JS needs to read it
            samesite="Lax",
            secure=settings.SESSION_COOKIE_SECURE,
        )

        return response

    def _get_csrf_token(self, request: Request) -> str | None:
        """Get CSRF token from cookie."""
        return request.cookies.get(settings.CSRF_COOKIE_NAME)

    def _generate_token(self) -> str:
        """Generate a new CSRF token."""
        return secrets.token_urlsafe(32)

    async def _check_csrf(self, request: Request, expected_token: str) -> bool:
        """Validate CSRF token from request."""
        # Check header first
        header_token = request.headers.get(settings.CSRF_HEADER_NAME)
        if header_token and secrets.compare_digest(header_token, expected_token):
            return True

        # Check form data
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            try:
                form = await request.form()
                form_token = form.get("csrfmiddlewaretoken", "")
                if form_token and secrets.compare_digest(str(form_token), expected_token):
                    return True
            except Exception:
                pass

        return False

    def _is_api_authenticated(self, request: Request) -> bool:
        """Check if request has API token authentication."""
        auth_header = request.headers.get("Authorization", "")
        return auth_header.startswith("Bearer ")


def get_csrf_token(request: Request) -> str:
    """Get CSRF token from request."""
    return getattr(request.state, "csrf_token", "")


def csrf_token_tag(request: Request) -> str:
    """Generate HTML hidden input for CSRF token."""
    token = get_csrf_token(request)
    return f'<input type="hidden" name="csrfmiddlewaretoken" value="{token}">'
