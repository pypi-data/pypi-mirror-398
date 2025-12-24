"""
shell command - Start interactive Python shell.
"""

import asyncio
import os
import typer
from rich.console import Console

console = Console()


def shell(
    ipython: bool = typer.Option(True, "--ipython/--no-ipython", help="Use IPython if available"),
):
    """Start an interactive Python shell with FastDjango context."""
    asyncio.run(_start_shell(ipython))


async def _start_shell(use_ipython: bool):
    """Start shell with database connection."""
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

    # Build database URL
    if db_config:
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

        # Initialize database
        await Tortoise.init(
            db_url=db_url,
            modules={"models": models_modules},
        )

    # Build context
    context = {
        "settings": settings,
        "asyncio": asyncio,
    }

    # Import commonly used modules
    try:
        from fastdjango.contrib.auth.models import User, Group, Permission
        context.update({
            "User": User,
            "Group": Group,
            "Permission": Permission,
        })
    except ImportError:
        pass

    # Import app models
    installed_apps = getattr(settings, "INSTALLED_APPS", [])
    for app_name in installed_apps:
        if app_name.startswith("fastdjango."):
            continue
        try:
            import importlib
            models = importlib.import_module(f"{app_name}.models")
            for name in dir(models):
                obj = getattr(models, name)
                if hasattr(obj, "__mro__") and "Model" in str(obj.__mro__):
                    context[name] = obj
        except ImportError:
            pass

    console.print("[green]FastDjango Shell[/green]")
    console.print("[dim]Type 'exit()' or Ctrl+D to exit[/dim]")
    console.print(f"[dim]Available: {', '.join(context.keys())}[/dim]\n")

    # Try IPython first
    if use_ipython:
        try:
            from IPython import embed
            embed(user_ns=context, colors="neutral")
            return
        except ImportError:
            pass

    # Fall back to standard Python shell
    import code
    code.interact(local=context, banner="")
