"""
FastDjango Middleware.
"""

from __future__ import annotations

import importlib
from typing import Any

from fastdjango.middleware.base import Middleware
from fastdjango.middleware.csrf import CSRFMiddleware
from fastdjango.middleware.cors import CORSMiddleware
from fastdjango.middleware.auth import AuthMiddleware


def get_middleware_class(path: str) -> type | None:
    """
    Get middleware class from dotted path.

    Examples:
        get_middleware_class("fastdjango.middleware.SessionMiddleware")
        get_middleware_class("myapp.middleware.CustomMiddleware")
    """
    # Handle shortcuts
    shortcuts = {
        "fastdjango.middleware.SessionMiddleware": (
            "fastdjango.contrib.sessions.middleware",
            "SessionMiddleware",
        ),
        "fastdjango.middleware.AuthMiddleware": (
            "fastdjango.middleware.auth",
            "AuthMiddleware",
        ),
        "fastdjango.middleware.CSRFMiddleware": (
            "fastdjango.middleware.csrf",
            "CSRFMiddleware",
        ),
        "fastdjango.middleware.CORSMiddleware": (
            "fastdjango.middleware.cors",
            "CORSMiddleware",
        ),
    }

    if path in shortcuts:
        module_path, class_name = shortcuts[path]
    else:
        # Parse dotted path
        parts = path.rsplit(".", 1)
        if len(parts) != 2:
            return None
        module_path, class_name = parts

    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name, None)
    except ImportError:
        return None


__all__ = [
    "Middleware",
    "CSRFMiddleware",
    "CORSMiddleware",
    "AuthMiddleware",
    "get_middleware_class",
]
