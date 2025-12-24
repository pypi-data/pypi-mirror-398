"""
FastDjango - Django-like framework built on FastAPI
100% async, WebSocket native, high performance
"""

__version__ = "0.2.4"

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

# Signals
from fastdjango.core.signals import (
    Signal,
    pre_save,
    post_save,
    pre_delete,
    post_delete,
    request_started,
    request_finished,
    user_logged_in,
    user_logged_out,
)

# Cache
from fastdjango.core.cache import (
    cache,
    get_cache,
    cached,
    cache_page,
)

# Mail
from fastdjango.core.mail import (
    send_mail,
    send_mass_mail,
    mail_admins,
    mail_managers,
    EmailMessage,
)

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
    # Signals
    "Signal",
    "pre_save",
    "post_save",
    "pre_delete",
    "post_delete",
    "request_started",
    "request_finished",
    "user_logged_in",
    "user_logged_out",
    # Cache
    "cache",
    "get_cache",
    "cached",
    "cache_page",
    # Mail
    "send_mail",
    "send_mass_mail",
    "mail_admins",
    "mail_managers",
    "EmailMessage",
]
