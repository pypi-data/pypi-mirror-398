"""
FastDjango exceptions.
"""

from typing import Any


class FastDjangoException(Exception):
    """Base exception for FastDjango."""

    pass


class ImproperlyConfigured(FastDjangoException):
    """Configuration error."""

    pass


class Http404(FastDjangoException):
    """Resource not found."""

    def __init__(self, message: str = "Not found"):
        self.message = message
        super().__init__(message)


class PermissionDenied(FastDjangoException):
    """Permission denied."""

    def __init__(self, message: str = "Permission denied"):
        self.message = message
        super().__init__(message)


class BadRequest(FastDjangoException):
    """Bad request."""

    def __init__(self, message: str = "Bad request"):
        self.message = message
        super().__init__(message)


class Redirect(FastDjangoException):
    """Redirect to another URL."""

    def __init__(self, url: str, status_code: int = 302):
        self.url = url
        self.status_code = status_code
        super().__init__(f"Redirect to {url}")


class ValidationError(FastDjangoException):
    """Validation error with field-level errors."""

    def __init__(
        self,
        message: str | dict[str, list[str]] | list[str],
        code: str | None = None,
        params: dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code
        self.params = params or {}

        if isinstance(message, dict):
            self.error_dict = message
            self.error_list = []
        elif isinstance(message, list):
            self.error_dict = {}
            self.error_list = message
        else:
            self.error_dict = {}
            self.error_list = [message]

        super().__init__(str(message))

    def __iter__(self):
        if self.error_dict:
            for field, errors in self.error_dict.items():
                yield field, errors
        else:
            for error in self.error_list:
                yield error

    def as_dict(self) -> dict[str, list[str]]:
        """Return errors as a dictionary."""
        if self.error_dict:
            return self.error_dict
        return {"__all__": self.error_list}


class SuspiciousOperation(FastDjangoException):
    """Suspicious operation detected."""

    pass


class CSRFError(SuspiciousOperation):
    """CSRF validation failed."""

    pass


class SessionError(FastDjangoException):
    """Session error."""

    pass
