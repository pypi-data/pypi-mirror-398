"""
FastDjango settings configuration.
Similar to Django's django.conf.settings
"""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any


class LazySettings:
    """
    Lazy settings loader - loads settings on first access.
    """

    _instance: LazySettings | None = None
    _configured: bool = False
    _settings_module: str | None = None
    _settings: dict[str, Any] = {}

    # Default settings
    _defaults = {
        "DEBUG": False,
        "SECRET_KEY": "",
        "ALLOWED_HOSTS": ["*"],
        "INSTALLED_APPS": [
            "fastdjango.contrib.admin",
            "fastdjango.contrib.auth",
            "fastdjango.contrib.sessions",
        ],
        "MIDDLEWARE": [
            "fastdjango.middleware.SessionMiddleware",
            "fastdjango.middleware.AuthMiddleware",
            "fastdjango.middleware.CSRFMiddleware",
        ],
        "DATABASES": {
            "default": {
                "ENGINE": "aiosqlite",
                "NAME": "db.sqlite3",
            }
        },
        "TEMPLATES": {
            "DIRS": [],
            "OPTIONS": {
                "autoescape": True,
                "auto_reload": True,
            },
        },
        "STATIC_URL": "/static/",
        "STATIC_ROOT": None,
        "MEDIA_URL": "/media/",
        "MEDIA_ROOT": None,
        "AUTH_USER_MODEL": "auth.User",
        "LOGIN_URL": "/auth/login/",
        "LOGIN_REDIRECT_URL": "/",
        "LOGOUT_REDIRECT_URL": "/",
        "SESSION_ENGINE": "fastdjango.contrib.sessions.backends.db",
        "SESSION_COOKIE_NAME": "sessionid",
        "SESSION_COOKIE_AGE": 60 * 60 * 24 * 14,  # 2 weeks
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SECURE": False,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "CSRF_COOKIE_NAME": "csrftoken",
        "CSRF_HEADER_NAME": "X-CSRFToken",
        "CSRF_TRUSTED_ORIGINS": [],
        "PASSWORD_HASHERS": [
            "fastdjango.contrib.auth.hashers.BCryptHasher",
            "fastdjango.contrib.auth.hashers.PBKDF2Hasher",
        ],
        "AUTH_PASSWORD_VALIDATORS": [],
        "LANGUAGE_CODE": "en-us",
        "TIME_ZONE": "UTC",
        "USE_TZ": True,
        "BASE_DIR": None,
        "ROOT_URLCONF": None,
        "APPEND_SLASH": True,
        "LOGGING": {},
    }

    def __new__(cls) -> LazySettings:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def configure(self, settings_module: str | None = None, **options: Any) -> None:
        """
        Configure settings from a module or keyword arguments.
        """
        if settings_module:
            self._settings_module = settings_module
            self._load_settings_module(settings_module)

        # Override with keyword arguments
        for key, value in options.items():
            self._settings[key.upper()] = value

        self._configured = True

    def _load_settings_module(self, settings_module: str) -> None:
        """Load settings from a Python module."""
        try:
            module = importlib.import_module(settings_module)
            for key in dir(module):
                if key.isupper():
                    self._settings[key] = getattr(module, key)
        except ImportError as e:
            raise ImportError(f"Could not import settings '{settings_module}': {e}")

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

        # First check if explicitly set
        if name in self._settings:
            return self._settings[name]

        # Then check environment variable
        env_value = os.environ.get(f"FASTDJANGO_{name}")
        if env_value is not None:
            return self._parse_env_value(env_value)

        # Finally check defaults
        if name in self._defaults:
            return self._defaults[name]

        raise AttributeError(f"Setting '{name}' not found")

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value."""
        # Try to parse as JSON
        import json

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

        # Check for boolean
        if value.lower() in ("true", "1", "yes"):
            return True
        if value.lower() in ("false", "0", "no"):
            return False

        return value

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self._settings[name] = value

    def get(self, name: str, default: Any = None) -> Any:
        """Get a setting with a default value."""
        try:
            return getattr(self, name)
        except AttributeError:
            return default

    def is_configured(self) -> bool:
        """Check if settings have been configured."""
        return self._configured

    def as_dict(self) -> dict[str, Any]:
        """Return all settings as a dictionary."""
        result = dict(self._defaults)
        result.update(self._settings)
        return result


# Global settings instance
settings = LazySettings()


class Settings:
    """
    Base class for user-defined settings classes.
    Provides type hints and validation.
    """

    DEBUG: bool = False
    SECRET_KEY: str = ""
    ALLOWED_HOSTS: list[str] = ["*"]
    INSTALLED_APPS: list[str] = []
    MIDDLEWARE: list[str] = []
    DATABASES: dict[str, dict[str, Any]] = {}
    TEMPLATES: dict[str, Any] = {}
    STATIC_URL: str = "/static/"
    STATIC_ROOT: str | None = None
    MEDIA_URL: str = "/media/"
    MEDIA_ROOT: str | None = None
    AUTH_USER_MODEL: str = "auth.User"
    LOGIN_URL: str = "/auth/login/"
    BASE_DIR: Path | None = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Register settings from the subclass
        for key in dir(cls):
            if key.isupper():
                value = getattr(cls, key)
                settings._settings[key] = value
