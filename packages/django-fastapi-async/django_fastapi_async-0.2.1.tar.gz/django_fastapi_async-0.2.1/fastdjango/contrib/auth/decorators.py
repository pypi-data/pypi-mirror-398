"""
FastDjango Auth Decorators.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar
from fastapi import Request

from fastdjango.core.exceptions import PermissionDenied, Redirect
from fastdjango.conf import settings


F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])


def login_required(
    func: F | None = None,
    *,
    login_url: str | None = None,
    redirect_field_name: str = "next",
) -> F | Callable[[F], F]:
    """
    Decorator to require login for a view.

    Usage:
        @router.get("/profile")
        @login_required
        async def profile(request: Request):
            return {"user": request.state.user.username}

        @router.get("/dashboard")
        @login_required(login_url="/auth/signin")
        async def dashboard(request: Request):
            return {"user": request.state.user}
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Find request in args/kwargs
            request = _get_request(args, kwargs)
            if request is None:
                raise ValueError("login_required requires a Request parameter")

            user = getattr(request.state, "user", None)

            if user is None or not getattr(user, "is_authenticated", False):
                # Redirect to login
                url = login_url or settings.LOGIN_URL
                if redirect_field_name:
                    url = f"{url}?{redirect_field_name}={request.url.path}"
                raise Redirect(url)

            return await func(*args, **kwargs)

        return wrapper  # type: ignore

    if func is not None:
        return decorator(func)
    return decorator


def permission_required(
    perm: str | list[str],
    *,
    login_url: str | None = None,
    raise_exception: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to require specific permissions.

    Usage:
        @router.post("/posts")
        @permission_required("blog.add_post")
        async def create_post(request: Request, data: PostCreate):
            ...

        @router.delete("/posts/{id}")
        @permission_required(["blog.delete_post", "blog.change_post"])
        async def delete_post(request: Request, id: int):
            ...
    """
    perms = [perm] if isinstance(perm, str) else list(perm)

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _get_request(args, kwargs)
            if request is None:
                raise ValueError("permission_required requires a Request parameter")

            user = getattr(request.state, "user", None)

            if user is None or not getattr(user, "is_authenticated", False):
                url = login_url or settings.LOGIN_URL
                raise Redirect(url)

            # Check permissions
            has_perms = await user.has_perms(perms)
            if not has_perms:
                if raise_exception:
                    raise PermissionDenied(
                        f"You don't have permission to access this resource. "
                        f"Required: {', '.join(perms)}"
                    )
                url = login_url or settings.LOGIN_URL
                raise Redirect(url)

            return await func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def user_passes_test(
    test_func: Callable[[Any], Coroutine[Any, Any, bool] | bool],
    *,
    login_url: str | None = None,
    redirect_field_name: str = "next",
) -> Callable[[F], F]:
    """
    Decorator that allows access only if the test function returns True.

    Usage:
        async def is_adult(user):
            return user.age >= 18

        @router.get("/adult-content")
        @user_passes_test(is_adult)
        async def adult_content(request: Request):
            ...

        # Simpler lambda-based test
        @router.get("/staff-only")
        @user_passes_test(lambda u: u.is_staff)
        async def staff_only(request: Request):
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _get_request(args, kwargs)
            if request is None:
                raise ValueError("user_passes_test requires a Request parameter")

            user = getattr(request.state, "user", None)

            if user is None or not getattr(user, "is_authenticated", False):
                url = login_url or settings.LOGIN_URL
                if redirect_field_name:
                    url = f"{url}?{redirect_field_name}={request.url.path}"
                raise Redirect(url)

            # Run test function
            result = test_func(user)
            if hasattr(result, "__await__"):
                result = await result

            if not result:
                raise PermissionDenied("You don't have permission to access this resource.")

            return await func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def staff_member_required(
    func: F | None = None,
    *,
    login_url: str | None = None,
) -> F | Callable[[F], F]:
    """
    Decorator to require staff status.

    Usage:
        @router.get("/admin/dashboard")
        @staff_member_required
        async def admin_dashboard(request: Request):
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _get_request(args, kwargs)
            if request is None:
                raise ValueError("staff_member_required requires a Request parameter")

            user = getattr(request.state, "user", None)

            if user is None or not getattr(user, "is_authenticated", False):
                url = login_url or settings.LOGIN_URL
                raise Redirect(url)

            if not getattr(user, "is_staff", False):
                raise PermissionDenied("Staff access required")

            return await func(*args, **kwargs)

        return wrapper  # type: ignore

    if func is not None:
        return decorator(func)
    return decorator


def superuser_required(
    func: F | None = None,
    *,
    login_url: str | None = None,
) -> F | Callable[[F], F]:
    """
    Decorator to require superuser status.

    Usage:
        @router.get("/admin/system")
        @superuser_required
        async def system_settings(request: Request):
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _get_request(args, kwargs)
            if request is None:
                raise ValueError("superuser_required requires a Request parameter")

            user = getattr(request.state, "user", None)

            if user is None or not getattr(user, "is_authenticated", False):
                url = login_url or settings.LOGIN_URL
                raise Redirect(url)

            if not getattr(user, "is_superuser", False):
                raise PermissionDenied("Superuser access required")

            return await func(*args, **kwargs)

        return wrapper  # type: ignore

    if func is not None:
        return decorator(func)
    return decorator


def _get_request(args: tuple, kwargs: dict) -> Request | None:
    """Extract Request from function arguments."""
    # Check kwargs first
    if "request" in kwargs:
        return kwargs["request"]

    # Check positional args
    for arg in args:
        if isinstance(arg, Request):
            return arg

    return None
