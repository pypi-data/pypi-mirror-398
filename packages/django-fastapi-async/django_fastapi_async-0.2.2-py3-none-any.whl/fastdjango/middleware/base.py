"""
FastDjango Middleware Base.
"""

from __future__ import annotations

from typing import Callable, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class Middleware(BaseHTTPMiddleware):
    """
    Base middleware class.
    Subclass this to create custom middleware.

    Usage:
        class MyMiddleware(Middleware):
            async def before_request(self, request: Request) -> Request | Response | None:
                # Called before the request is processed
                # Return Response to short-circuit, or None to continue
                return None

            async def after_request(self, request: Request, response: Response) -> Response:
                # Called after the request is processed
                # Modify and return the response
                return response

        # Or override dispatch for full control:
        class MyMiddleware(Middleware):
            async def dispatch(self, request: Request, call_next) -> Response:
                # Before
                response = await call_next(request)
                # After
                return response
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Before request hook
        result = await self.before_request(request)
        if isinstance(result, Response):
            return result

        # Process request
        response = await call_next(request)

        # After request hook
        response = await self.after_request(request, response)

        return response

    async def before_request(self, request: Request) -> Request | Response | None:
        """
        Called before the request is processed.

        Return:
            - None: Continue processing
            - Response: Short-circuit and return this response
        """
        return None

    async def after_request(self, request: Request, response: Response) -> Response:
        """
        Called after the request is processed.

        Args:
            request: The original request
            response: The response from the view

        Returns:
            The (possibly modified) response
        """
        return response
