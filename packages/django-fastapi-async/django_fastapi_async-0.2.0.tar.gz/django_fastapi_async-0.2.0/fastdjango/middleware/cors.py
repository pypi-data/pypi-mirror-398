"""
FastDjango CORS Middleware.
"""

from __future__ import annotations

from typing import Callable, Sequence
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware as StarletteCORS

from fastdjango.conf import settings


class CORSMiddleware(StarletteCORS):
    """
    CORS middleware wrapper.
    Uses settings from FastDjango configuration.
    """

    def __init__(self, app, **kwargs):
        # Get CORS settings
        allow_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", ["*"])
        allow_methods = getattr(settings, "CORS_ALLOW_METHODS", ["*"])
        allow_headers = getattr(settings, "CORS_ALLOW_HEADERS", ["*"])
        allow_credentials = getattr(settings, "CORS_ALLOW_CREDENTIALS", True)
        expose_headers = getattr(settings, "CORS_EXPOSE_HEADERS", [])
        max_age = getattr(settings, "CORS_MAX_AGE", 600)

        super().__init__(
            app,
            allow_origins=allow_origins,
            allow_credentials=allow_credentials,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
            expose_headers=expose_headers,
            max_age=max_age,
        )
