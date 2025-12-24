"""
startproject command - Create a new FastDjango project.
"""

import os
from pathlib import Path
import typer
from rich.console import Console

console = Console()


def startproject(
    name: str = typer.Argument(..., help="Project name"),
    directory: str = typer.Option(".", help="Directory to create project in"),
):
    """Create a new FastDjango project."""
    project_dir = Path(directory) / name

    if project_dir.exists():
        console.print(f"[red]Error: Directory '{name}' already exists[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Creating project '{name}'...[/green]")

    # Create directory structure
    project_dir.mkdir(parents=True)
    (project_dir / name).mkdir()

    # Create files
    _create_file(project_dir / "manage.py", MANAGE_PY.format(project_name=name))
    _create_file(project_dir / name / "__init__.py", "")
    _create_file(project_dir / name / "settings.py", SETTINGS_PY.format(project_name=name))
    _create_file(project_dir / name / "urls.py", URLS_PY)
    _create_file(project_dir / name / "asgi.py", ASGI_PY.format(project_name=name))
    _create_file(project_dir / "requirements.txt", REQUIREMENTS_TXT)
    _create_file(project_dir / ".env.example", ENV_EXAMPLE)

    # Create templates directory
    (project_dir / "templates").mkdir()
    _create_file(project_dir / "templates" / "base.html", BASE_HTML)

    # Create static directory
    (project_dir / "static").mkdir()

    console.print(f"[green]Project '{name}' created successfully![/green]")
    console.print(f"\nNext steps:")
    console.print(f"  cd {name}")
    console.print(f"  pip install -r requirements.txt")
    console.print(f"  fastdjango migrate")
    console.print(f"  fastdjango runserver")


def _create_file(path: Path, content: str):
    """Create a file with content."""
    path.write_text(content)


MANAGE_PY = '''#!/usr/bin/env python
"""FastDjango management script."""
import os
import sys

def main():
    os.environ.setdefault("FASTDJANGO_SETTINGS_MODULE", "{project_name}.settings")
    from fastdjango.core.management import main as cli_main
    cli_main()

if __name__ == "__main__":
    main()
'''

SETTINGS_PY = '''"""
FastDjango settings for {project_name} project.
"""

from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "change-me-in-production"

# SECURITY WARNING: don\'t run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS = [
    "fastdjango.contrib.admin",
    "fastdjango.contrib.auth",
    "fastdjango.contrib.sessions",
    # Your apps here
]

MIDDLEWARE = [
    "fastdjango.middleware.SessionMiddleware",
    "fastdjango.middleware.AuthMiddleware",
    "fastdjango.middleware.CSRFMiddleware",
]

ROOT_URLCONF = "{project_name}.urls"

TEMPLATES = {{
    "DIRS": [BASE_DIR / "templates"],
    "OPTIONS": {{
        "autoescape": True,
        "auto_reload": True,
    }},
}}

# Database
DATABASES = {{
    "default": {{
        "ENGINE": "aiosqlite",
        "NAME": BASE_DIR / "db.sqlite3",
    }}
}}

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Auth
AUTH_USER_MODEL = "auth.User"
LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/"

# Session
SESSION_ENGINE = "fastdjango.contrib.sessions.backends.db"

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
'''

URLS_PY = '''"""
URL configuration.
"""

from fastdjango.routing import include

urlpatterns = [
    # include("/api/blog", "blog.routes"),
]
'''

ASGI_PY = '''"""
ASGI config for {project_name} project.
"""

import os
from fastdjango import FastDjango

os.environ.setdefault("FASTDJANGO_SETTINGS_MODULE", "{project_name}.settings")

app = FastDjango(settings_module="{project_name}.settings")
application = app.app
'''

REQUIREMENTS_TXT = '''fastdjango>=0.1.0
uvicorn[standard]>=0.27.0
'''

ENV_EXAMPLE = '''# Environment variables
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
'''

BASE_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}FastDjango{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    {% block extra_css %}{% endblock %}
</head>
<body class="bg-gray-100">
    <nav class="bg-white shadow-lg">
        <div class="max-w-6xl mx-auto px-4">
            <div class="flex justify-between">
                <div class="flex space-x-7">
                    <a href="/" class="flex items-center py-4 px-2">
                        <span class="font-semibold text-gray-500 text-lg">FastDjango</span>
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <main class="max-w-6xl mx-auto mt-6 px-4">
        {% block content %}{% endblock %}
    </main>

    {% block extra_js %}{% endblock %}
</body>
</html>
'''
