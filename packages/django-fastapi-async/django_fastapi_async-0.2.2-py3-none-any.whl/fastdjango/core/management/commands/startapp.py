"""
startapp command - Create a new FastDjango app.
"""

from pathlib import Path
import typer
from rich.console import Console

console = Console()


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
    console.print(f"\nDon't forget to add '{name}' to INSTALLED_APPS in settings.py")


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
