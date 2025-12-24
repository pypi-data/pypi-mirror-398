"""
FastDjango Auth module.
Provides User model, authentication, permissions, and decorators.
"""

from fastdjango.contrib.auth.models import User, Group, Permission
from fastdjango.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from fastdjango.contrib.auth.hashers import make_password, check_password
from fastdjango.contrib.auth.backends import authenticate, login, logout

__all__ = [
    # Models
    "User",
    "Group",
    "Permission",
    # Decorators
    "login_required",
    "permission_required",
    "user_passes_test",
    # Password
    "make_password",
    "check_password",
    # Auth functions
    "authenticate",
    "login",
    "logout",
]
