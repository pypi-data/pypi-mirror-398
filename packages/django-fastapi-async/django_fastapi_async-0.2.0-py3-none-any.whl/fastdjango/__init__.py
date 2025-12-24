"""
FastDjango - Django-like framework built on FastAPI
100% async, WebSocket native, high performance
"""

__version__ = "0.1.0"

from fastdjango.app import FastDjango
from fastdjango.routing import Router, include
from fastdjango.templates import render, render_to_string
from fastdjango.db.models import Model
from fastdjango.db import fields
from fastdjango.forms import Form, ModelForm
from fastdjango.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from fastdjango.core.exceptions import (
    Http404,
    PermissionDenied,
    BadRequest,
    Redirect,
)
from fastdjango.middleware import Middleware

__all__ = [
    # Core
    "FastDjango",
    "__version__",
    # Routing
    "Router",
    "include",
    # Templates
    "render",
    "render_to_string",
    # DB
    "Model",
    "fields",
    # Forms
    "Form",
    "ModelForm",
    # Auth
    "login_required",
    "permission_required",
    "user_passes_test",
    # Exceptions
    "Http404",
    "PermissionDenied",
    "BadRequest",
    "Redirect",
    # Middleware
    "Middleware",
]
