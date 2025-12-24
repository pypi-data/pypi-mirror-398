"""
migrate command - Run database migrations.
"""

import asyncio
import os
import typer
from rich.console import Console

console = Console()


def migrate(
    app_label: str = typer.Argument(None, help="App to migrate (optional)"),
    fake: bool = typer.Option(False, "--fake", help="Mark migrations as run without executing"),
):
    """Run database migrations."""
    console.print("[green]Running migrations...[/green]")

    asyncio.run(_run_migrations(app_label, fake))


async def _run_migrations(app_label: str | None, fake: bool):
    """Run migrations async."""
    from tortoise import Tortoise
    from aerich import Command

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

    # Discover models
    installed_apps = getattr(settings, "INSTALLED_APPS", [])
    models_modules = ["fastdjango.contrib.auth.models"]

    for app_name in installed_apps:
        if app_name.startswith("fastdjango."):
            continue
        models_modules.append(f"{app_name}.models")

    # Initialize Tortoise
    try:
        await Tortoise.init(
            db_url=db_url,
            modules={"models": models_modules},
        )

        # Generate schemas
        await Tortoise.generate_schemas(safe=True)

        console.print("[green]Migrations applied successfully![/green]")

    except Exception as e:
        console.print(f"[red]Migration error: {e}[/red]")
        raise

    finally:
        await Tortoise.close_connections()
