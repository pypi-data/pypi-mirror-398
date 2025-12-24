"""
FastDjango Authentication Backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING
from datetime import datetime

from fastdjango.conf import settings
from fastdjango.contrib.auth.hashers import check_password
from fastdjango.core.signals import user_logged_in, user_logged_out, user_login_failed

if TYPE_CHECKING:
    from fastapi import Request
    from fastdjango.contrib.auth.models import User, AnonymousUser


class BaseBackend(ABC):
    """Base authentication backend."""

    @abstractmethod
    async def authenticate(
        self,
        request: Request | None = None,
        **credentials: Any,
    ) -> User | None:
        """
        Authenticate a user with given credentials.
        Returns User if successful, None otherwise.
        """
        pass

    async def get_user(self, user_id: int) -> User | None:
        """Get a user by ID."""
        from fastdjango.contrib.auth.models import User

        return await User.get_or_none(id=user_id, is_active=True)


class ModelBackend(BaseBackend):
    """
    Default authentication backend.
    Authenticates against username/email and password.
    """

    async def authenticate(
        self,
        request: Request | None = None,
        username: str | None = None,
        email: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        """
        Authenticate with username/email and password.
        """
        from fastdjango.contrib.auth.models import User

        if password is None:
            return None

        # Try username first, then email
        user = None
        if username:
            user = await User.get_or_none(username=username)
        elif email:
            user = await User.get_or_none(email=email.lower())

        if user is None:
            # Run password check anyway to prevent timing attacks
            check_password(password, "!")
            return None

        if not user.is_active:
            return None

        if await user.check_password(password):
            return user

        return None


class TokenBackend(BaseBackend):
    """
    Token-based authentication backend.
    For API authentication with JWT or similar tokens.
    """

    async def authenticate(
        self,
        request: Request | None = None,
        token: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        """Authenticate with a token."""
        if token is None:
            return None

        try:
            from jose import jwt, JWTError

            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
            )
            user_id = payload.get("sub")
            if user_id is None:
                return None

            return await self.get_user(int(user_id))
        except (JWTError, ValueError):
            return None


# Default backends
_backends: list[BaseBackend] = [ModelBackend()]


def get_backends() -> list[BaseBackend]:
    """Get all authentication backends."""
    return _backends


async def authenticate(
    request: Request | None = None,
    **credentials: Any,
) -> User | None:
    """
    Authenticate a user with the given credentials.
    Tries all backends in order until one succeeds.

    Usage:
        user = await authenticate(request, username="john", password="secret")
        user = await authenticate(request, email="john@example.com", password="secret")
        user = await authenticate(request, token="jwt_token_here")
    """
    for backend in get_backends():
        try:
            user = await backend.authenticate(request=request, **credentials)
            if user is not None:
                # Store which backend authenticated the user
                user._backend = f"{backend.__class__.__module__}.{backend.__class__.__name__}"
                return user
        except Exception:
            continue

    # All backends failed
    await user_login_failed.send(
        sender=None,
        credentials=_clean_credentials(credentials),
        request=request,
    )
    return None


def _clean_credentials(credentials: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive data from credentials for logging."""
    clean = credentials.copy()
    for key in ["password", "token", "secret"]:
        if key in clean:
            clean[key] = "***"
    return clean


async def login(request: Request, user: User) -> None:
    """
    Log in a user and create a session.

    Usage:
        user = await authenticate(request, username="john", password="secret")
        if user:
            await login(request, user)
    """
    from fastdjango.contrib.auth.models import User

    # Update last_login
    user.last_login = datetime.utcnow()
    await user.save(update_fields=["last_login"])

    # Store user ID in session
    session = getattr(request.state, "session", None)
    if session is not None:
        session["_auth_user_id"] = user.pk
        session["_auth_user_backend"] = getattr(
            user, "_backend", "fastdjango.contrib.auth.backends.ModelBackend"
        )
        session.modified = True

    # Store user in request state
    request.state.user = user

    # Send signal
    await user_logged_in.send(
        sender=user.__class__,
        request=request,
        user=user,
    )


async def logout(request: Request) -> None:
    """
    Log out the current user and clear the session.

    Usage:
        await logout(request)
    """
    from fastdjango.contrib.auth.models import AnonymousUser

    user = getattr(request.state, "user", None)

    # Clear session
    session = getattr(request.state, "session", None)
    if session is not None:
        session.clear()

    # Set anonymous user
    request.state.user = AnonymousUser()

    # Send signal
    if user and getattr(user, "is_authenticated", False):
        await user_logged_out.send(
            sender=user.__class__,
            request=request,
            user=user,
        )


async def get_user(request: Request) -> User | AnonymousUser:
    """
    Get the current user from the request.
    Returns AnonymousUser if not authenticated.
    """
    from fastdjango.contrib.auth.models import User, AnonymousUser

    # Check if already set
    if hasattr(request.state, "user"):
        return request.state.user

    # Try to get from session
    session = getattr(request.state, "session", None)
    if session is None:
        return AnonymousUser()

    user_id = session.get("_auth_user_id")
    if user_id is None:
        return AnonymousUser()

    # Get user from database
    user = await User.get_or_none(id=user_id, is_active=True)
    if user is None:
        return AnonymousUser()

    return user


def create_access_token(user: User, expires_delta: int | None = None) -> str:
    """
    Create a JWT access token for the user.

    Args:
        user: The user to create token for
        expires_delta: Token expiration in seconds (default: 24 hours)

    Returns:
        JWT token string
    """
    from datetime import timedelta
    from jose import jwt

    expires_delta = expires_delta or 60 * 60 * 24  # 24 hours

    expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    payload = {
        "sub": str(user.pk),
        "username": user.username,
        "exp": expire,
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(user: User, expires_delta: int | None = None) -> str:
    """
    Create a JWT refresh token for the user.

    Args:
        user: The user to create token for
        expires_delta: Token expiration in seconds (default: 7 days)

    Returns:
        JWT token string
    """
    from datetime import timedelta
    from jose import jwt

    expires_delta = expires_delta or 60 * 60 * 24 * 7  # 7 days

    expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    payload = {
        "sub": str(user.pk),
        "type": "refresh",
        "exp": expire,
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
