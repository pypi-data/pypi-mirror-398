"""
createsuperuser command - Create a superuser.
"""

import asyncio
import os
import typer
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def createsuperuser(
    username: str = typer.Option(None, "--username", "-u", help="Username"),
    email: str = typer.Option(None, "--email", "-e", help="Email address"),
    password: str = typer.Option(None, "--password", "-p", help="Password (not recommended)"),
    noinput: bool = typer.Option(False, "--noinput", help="Don't prompt for input"),
):
    """Create a superuser account."""
    asyncio.run(_create_superuser(username, email, password, noinput))


async def _create_superuser(
    username: str | None,
    email: str | None,
    password: str | None,
    noinput: bool,
):
    """Create superuser async."""
    from tortoise import Tortoise

    # Load settings
    settings_module = os.environ.get("FASTDJANGO_SETTINGS_MODULE")
    if settings_module:
        import importlib
        settings = importlib.import_module(settings_module)
    else:
        from fastdjango.conf import settings

    # Get database config
    db_config = getattr(settings, "DATABASES", {}).get("default", {})

    if not db_config:
        console.print("[red]No database configured[/red]")
        return

    # Build database URL
    engine = db_config.get("ENGINE", "aiosqlite")
    if engine == "aiosqlite":
        db_url = f"sqlite://{db_config.get('NAME', 'db.sqlite3')}"
    elif engine == "asyncpg":
        db_url = (
            f"postgres://{db_config.get('USER', '')}:"
            f"{db_config.get('PASSWORD', '')}@"
            f"{db_config.get('HOST', 'localhost')}:"
            f"{db_config.get('PORT', 5432)}/"
            f"{db_config.get('NAME', '')}"
        )
    else:
        db_url = engine

    # Initialize database
    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["fastdjango.contrib.auth.models"]},
    )

    # Prompt for input if not provided
    if not noinput:
        if not username:
            username = Prompt.ask("Username")
        if not email:
            email = Prompt.ask("Email")
        if not password:
            import getpass
            password = getpass.getpass("Password: ")
            password2 = getpass.getpass("Password (again): ")
            if password != password2:
                console.print("[red]Passwords don't match[/red]")
                await Tortoise.close_connections()
                return

    if not all([username, email, password]):
        console.print("[red]Username, email, and password are required[/red]")
        await Tortoise.close_connections()
        return

    try:
        from fastdjango.contrib.auth.models import User

        # Check if user exists
        existing = await User.filter(username=username).first()
        if existing:
            console.print(f"[red]User '{username}' already exists[/red]")
            await Tortoise.close_connections()
            return

        # Create superuser
        user = await User.create_superuser(
            username=username,
            email=email,
            password=password,
        )

        console.print(f"[green]Superuser '{username}' created successfully![/green]")

    except Exception as e:
        console.print(f"[red]Error creating superuser: {e}[/red]")

    finally:
        await Tortoise.close_connections()
