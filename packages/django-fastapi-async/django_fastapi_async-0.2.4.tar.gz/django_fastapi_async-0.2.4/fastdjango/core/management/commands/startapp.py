"""
startapp command - Create a new FastDjango app.
"""

import re
from pathlib import Path
import typer
from rich.console import Console

console = Console()


def _find_settings_file(start_dir: Path) -> Path | None:
    """Find settings.py in the project."""
    # Look for settings.py in subdirectories
    for settings_file in start_dir.rglob("settings.py"):
        # Skip if it's in a venv or site-packages
        if "venv" in str(settings_file) or "site-packages" in str(settings_file):
            continue
        # Check if it contains INSTALLED_APPS
        content = settings_file.read_text()
        if "INSTALLED_APPS" in content:
            return settings_file
    return None


def _find_urls_file(start_dir: Path) -> Path | None:
    """Find urls.py in the project."""
    for urls_file in start_dir.rglob("urls.py"):
        if "venv" in str(urls_file) or "site-packages" in str(urls_file):
            continue
        content = urls_file.read_text()
        if "urlpatterns" in content:
            return urls_file
    return None


def _add_to_installed_apps(settings_file: Path, app_name: str) -> bool:
    """Add app to INSTALLED_APPS in settings.py."""
    content = settings_file.read_text()

    # Check if already added
    if f'"{app_name}"' in content or f"'{app_name}'" in content:
        return False

    # Find INSTALLED_APPS and add the app
    # Pattern to match INSTALLED_APPS = [...] with the comment "# Your apps here"
    pattern = r'(INSTALLED_APPS\s*=\s*\[.*?)(# Your apps here)'
    replacement = rf'\1"{app_name}",\n    \2'

    new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)

    if count == 0:
        # Try alternative pattern without the comment
        pattern = r'(INSTALLED_APPS\s*=\s*\[[^\]]*?)(\])'
        replacement = rf'\1    "{app_name}",\n\2'
        new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)

    if count > 0:
        settings_file.write_text(new_content)
        return True
    return False


def _add_to_urlpatterns(urls_file: Path, app_name: str) -> bool:
    """Add app routes to urlpatterns in urls.py."""
    content = urls_file.read_text()

    # Check if already added (not in a comment)
    # Look for uncommented include with this app
    pattern_check = rf'^[^#]*include\s*\([^)]*{app_name}\.routes'
    if re.search(pattern_check, content, re.MULTILINE):
        return False

    # Find urlpatterns and add the include
    pattern = r'(urlpatterns\s*=\s*\[)'
    include_line = f'    include("/{app_name}", "{app_name}.routes"),'
    replacement = rf'\1\n{include_line}'

    new_content, count = re.subn(pattern, replacement, content)

    if count > 0:
        urls_file.write_text(new_content)
        return True
    return False


def startapp(
    name: str = typer.Argument(..., help="App name"),
    directory: str = typer.Option(".", help="Directory to create app in"),
):
    """Create a new FastDjango app."""
    app_dir = Path(directory) / name

    if app_dir.exists():
        console.print(f"[red]Error: Directory '{name}' already exists[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Creating app '{name}'...[/green]")

    # Create directory structure
    app_dir.mkdir(parents=True)
    (app_dir / "templates" / name).mkdir(parents=True)
    (app_dir / "migrations").mkdir()

    # Create files
    _create_file(app_dir / "__init__.py", INIT_PY.format(app_name=name))
    _create_file(app_dir / "models.py", MODELS_PY.format(app_name=name))
    _create_file(app_dir / "routes.py", ROUTES_PY.format(app_name=name))
    _create_file(app_dir / "schemas.py", SCHEMAS_PY.format(app_name=name))
    _create_file(app_dir / "admin.py", ADMIN_PY.format(app_name=name))
    _create_file(app_dir / "migrations" / "__init__.py", "")

    console.print(f"[green]App '{name}' created successfully![/green]")

    # Auto-add to INSTALLED_APPS
    base_dir = Path(directory).resolve()
    settings_file = _find_settings_file(base_dir)
    if settings_file:
        if _add_to_installed_apps(settings_file, name):
            console.print(f"[blue]Added '{name}' to INSTALLED_APPS in {settings_file.name}[/blue]")
        else:
            console.print(f"[yellow]'{name}' already in INSTALLED_APPS or could not be added automatically[/yellow]")
    else:
        console.print(f"[yellow]Could not find settings.py - add '{name}' to INSTALLED_APPS manually[/yellow]")

    # Auto-add to urlpatterns
    urls_file = _find_urls_file(base_dir)
    if urls_file:
        if _add_to_urlpatterns(urls_file, name):
            console.print(f"[blue]Added '{name}' routes to urlpatterns in {urls_file.name}[/blue]")
        else:
            console.print(f"[yellow]'{name}' routes already in urlpatterns or could not be added automatically[/yellow]")
    else:
        console.print(f"[yellow]Could not find urls.py - add routes manually[/yellow]")


def _create_file(path: Path, content: str):
    """Create a file with content."""
    path.write_text(content)


INIT_PY = '''"""
{app_name} app.
"""

default_app_config = "{app_name}"
'''

MODELS_PY = '''"""
{app_name} models.
"""

from fastdjango.db.models import Model
from fastdjango.db import fields


# Example model - customize as needed
# class Example(Model):
#     title = fields.CharField(max_length=200)
#     content = fields.TextField(blank=True)
#     created_at = fields.DateTimeField(auto_now_add=True)
#     updated_at = fields.DateTimeField(auto_now=True)
#
#     class Meta:
#         table = "{app_name}_example"
#         ordering = ["-created_at"]
#
#     def __str__(self):
#         return self.title
'''

ROUTES_PY = '''"""
{app_name} routes.
"""

from fastapi import Request
from fastdjango.routing import Router
from fastdjango.templates import render
# from .models import Example
# from .schemas import ExampleCreate, ExampleUpdate

router = Router()


@router.get("/")
async def index(request: Request):
    """List view."""
    # items = await Example.objects.all()
    # return render("{app_name}/index.html", {{"items": items}}, request=request)
    return {{"message": "Hello from {app_name}!"}}


# @router.get("/{{pk}}")
# async def detail(request: Request, pk: int):
#     """Detail view."""
#     item = await Example.objects.get_or_404(pk=pk)
#     return render("{app_name}/detail.html", {{"item": item}}, request=request)


# @router.post("/")
# async def create(data: ExampleCreate):
#     """Create view."""
#     item = await Example.objects.create(**data.model_dump())
#     return item


# @router.put("/{{pk}}")
# async def update(pk: int, data: ExampleUpdate):
#     """Update view."""
#     item = await Example.objects.get_or_404(pk=pk)
#     for key, value in data.model_dump(exclude_unset=True).items():
#         setattr(item, key, value)
#     await item.save()
#     return item


# @router.delete("/{{pk}}")
# async def delete(pk: int):
#     """Delete view."""
#     item = await Example.objects.get_or_404(pk=pk)
#     await item.delete()
#     return {{"message": "Deleted"}}
'''

SCHEMAS_PY = '''"""
{app_name} schemas (Pydantic models).
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Example schemas - customize as needed
# class ExampleBase(BaseModel):
#     title: str
#     content: str = ""


# class ExampleCreate(ExampleBase):
#     pass


# class ExampleUpdate(BaseModel):
#     title: Optional[str] = None
#     content: Optional[str] = None


# class ExampleResponse(ExampleBase):
#     id: int
#     created_at: datetime
#     updated_at: datetime
#
#     class Config:
#         from_attributes = True
'''

ADMIN_PY = '''"""
{app_name} admin configuration.
"""

from fastdjango.contrib.admin import admin_site, ModelAdmin, register
# from .models import Example


# @register(Example)
# class ExampleAdmin(ModelAdmin):
#     list_display = ["title", "created_at"]
#     list_filter = ["created_at"]
#     search_fields = ["title", "content"]
#     ordering = ["-created_at"]
'''
