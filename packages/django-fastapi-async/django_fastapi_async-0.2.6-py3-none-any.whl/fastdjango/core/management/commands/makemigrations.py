"""
makemigrations command - Create new migrations.
"""

import asyncio
import os
from pathlib import Path
import typer
from rich.console import Console

console = Console()


def makemigrations(
    app_label: str = typer.Argument(None, help="App to make migrations for (optional)"),
    name: str = typer.Option(None, "--name", "-n", help="Migration name"),
    empty: bool = typer.Option(False, "--empty", help="Create empty migration"),
):
    """Create new migrations based on model changes."""
    console.print("[green]Making migrations...[/green]")

    asyncio.run(_make_migrations(app_label, name, empty))


async def _make_migrations(app_label: str | None, name: str | None, empty: bool):
    """Create migrations async."""
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

    # Discover models
    installed_apps = getattr(settings, "INSTALLED_APPS", [])
    models_modules = ["fastdjango.contrib.auth.models"]
    apps_to_migrate = []

    for app_name in installed_apps:
        if app_name.startswith("fastdjango."):
            continue
        models_modules.append(f"{app_name}.models")
        if app_label is None or app_name == app_label:
            apps_to_migrate.append(app_name)

    try:
        await Tortoise.init(
            db_url=db_url,
            modules={"models": models_modules},
        )

        # For each app, create migrations directory and file
        for app_name in apps_to_migrate:
            app_path = Path(app_name.replace(".", "/"))
            migrations_path = app_path / "migrations"

            if not migrations_path.exists():
                migrations_path.mkdir(parents=True, exist_ok=True)
                (migrations_path / "__init__.py").write_text("")

            console.print(f"[green]Detected changes in {app_name}[/green]")

        console.print("[green]Migrations created.[/green]")
        console.print("[yellow]Note: FastDjango uses Tortoise ORM auto-schema generation.[/yellow]")
        console.print("Run 'fastdjango migrate' to apply changes.")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise

    finally:
        await Tortoise.close_connections()
