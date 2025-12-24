"""
FastDjango example project settings.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "example-secret-key-change-in-production"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "fastdjango.contrib.admin",
    "fastdjango.contrib.auth",
    "fastdjango.contrib.sessions",
    "blog",
]

MIDDLEWARE = [
    "fastdjango.middleware.SessionMiddleware",
    "fastdjango.middleware.AuthMiddleware",
    "fastdjango.middleware.CSRFMiddleware",
]

ROOT_URLCONF = "urls"

TEMPLATES = {
    "DIRS": [BASE_DIR / "templates"],
    "OPTIONS": {
        "autoescape": True,
        "auto_reload": True,
    },
}

DATABASES = {
    "default": {
        "ENGINE": "aiosqlite",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

AUTH_USER_MODEL = "auth.User"
LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/"

SESSION_ENGINE = "fastdjango.contrib.sessions.backends.db"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
