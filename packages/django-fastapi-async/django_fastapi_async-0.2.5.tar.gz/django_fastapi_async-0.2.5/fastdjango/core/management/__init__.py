"""
FastDjango Management Commands.
CLI interface using Typer.
"""

import typer
from rich.console import Console

from fastdjango.core.management.commands import (
    startproject,
    startapp,
    runserver,
    migrate,
    makemigrations,
    createsuperuser,
    shell,
    collectstatic,
)

console = Console()

# Main CLI app
app = typer.Typer(
    name="fastdjango",
    help="FastDjango - Django-like framework built on FastAPI",
    no_args_is_help=True,
)

# Register commands
app.command()(startproject.startproject)
app.command()(startapp.startapp)
app.command()(runserver.runserver)
app.command()(migrate.migrate)
app.command()(makemigrations.makemigrations)
app.command()(createsuperuser.createsuperuser)
app.command()(shell.shell)
app.command()(collectstatic.collectstatic)


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
