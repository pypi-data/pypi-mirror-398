"""
collectstatic command - Collect static files.
"""

import os
import shutil
from pathlib import Path
import typer
from rich.console import Console

console = Console()


def collectstatic(
    noinput: bool = typer.Option(False, "--noinput", "-n", help="Don't prompt for confirmation"),
    clear: bool = typer.Option(False, "--clear", "-c", help="Clear existing static files first"),
):
    """Collect static files into STATIC_ROOT."""

    # Load settings
    settings_module = os.environ.get("FASTDJANGO_SETTINGS_MODULE")
    if settings_module:
        import importlib
        settings = importlib.import_module(settings_module)
    else:
        from fastdjango.conf import settings

    static_root = getattr(settings, "STATIC_ROOT", None)

    if not static_root:
        console.print("[red]STATIC_ROOT is not configured[/red]")
        raise typer.Exit(1)

    static_root = Path(static_root)

    # Confirm if not noinput
    if not noinput:
        if static_root.exists():
            confirm = typer.confirm(
                f"This will overwrite files in {static_root}. Continue?"
            )
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(0)

    # Clear if requested
    if clear and static_root.exists():
        console.print(f"[yellow]Clearing {static_root}...[/yellow]")
        shutil.rmtree(static_root)

    # Create directory
    static_root.mkdir(parents=True, exist_ok=True)

    collected = 0

    # Collect from each installed app
    installed_apps = getattr(settings, "INSTALLED_APPS", [])

    for app_name in installed_apps:
        try:
            if app_name.startswith("fastdjango."):
                # Handle contrib apps
                parts = app_name.split(".")
                import fastdjango
                base_path = Path(fastdjango.__file__).parent
                for part in parts[1:]:
                    base_path = base_path / part
                app_static = base_path / "static"
            else:
                import importlib
                module = importlib.import_module(app_name)
                app_path = Path(module.__file__).parent
                app_static = app_path / "static"

            if app_static.exists():
                console.print(f"Copying from {app_name}...")
                collected += _copy_directory(app_static, static_root)

        except (ImportError, AttributeError):
            continue

    # Collect from project static directories
    base_dir = getattr(settings, "BASE_DIR", Path.cwd())
    project_static = Path(base_dir) / "static"

    if project_static.exists() and project_static != static_root:
        console.print("Copying from project static...")
        collected += _copy_directory(project_static, static_root)

    console.print(f"[green]Collected {collected} static files to {static_root}[/green]")


def _copy_directory(src: Path, dst: Path) -> int:
    """Copy directory contents recursively. Returns number of files copied."""
    count = 0

    for item in src.rglob("*"):
        if item.is_file():
            relative = item.relative_to(src)
            dest_file = dst / relative
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest_file)
            count += 1

    return count
