"""
runserver command - Run the development server.
"""

import os
import typer
from rich.console import Console

console = Console()


def runserver(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Enable auto-reload"),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of workers"),
):
    """Run the development server."""
    import uvicorn

    # Get settings module from environment
    settings_module = os.environ.get("FASTDJANGO_SETTINGS_MODULE")

    if not settings_module:
        # Try to find settings in current directory
        if os.path.exists("manage.py"):
            # Read manage.py to find settings module
            with open("manage.py") as f:
                content = f.read()
                if "FASTDJANGO_SETTINGS_MODULE" in content:
                    import re
                    match = re.search(r'"(\w+\.settings)"', content)
                    if match:
                        settings_module = match.group(1)

    if not settings_module:
        console.print("[yellow]Warning: FASTDJANGO_SETTINGS_MODULE not set[/yellow]")
        console.print("Using default settings")

    # Find ASGI application
    asgi_app = None
    if settings_module:
        project_name = settings_module.split(".")[0]
        asgi_module = f"{project_name}.asgi:application"

        if os.path.exists(f"{project_name}/asgi.py"):
            asgi_app = asgi_module

    if not asgi_app:
        # Create a default app
        asgi_app = "fastdjango:FastDjango"
        console.print("[yellow]Using default FastDjango app[/yellow]")

    console.print(f"[green]Starting server at http://{host}:{port}[/green]")
    console.print(f"[dim]Press Ctrl+C to stop[/dim]")

    uvicorn.run(
        asgi_app,
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
        log_level="info",
    )
