# FastDjango Documentation

Welcome to FastDjango - a Django-like framework built on FastAPI.

**GitHub**: https://github.com/TWFBusiness/fastdjango

## Quick Start

### Installation

```bash
pip install fastdjango
```

### Create a Project

```bash
fastdjango startproject mysite
cd mysite
fastdjango startapp blog
```

### Configure Settings

Edit `mysite/settings.py`:

```python
INSTALLED_APPS = [
    "fastdjango.contrib.admin",
    "fastdjango.contrib.auth",
    "fastdjango.contrib.sessions",
    "blog",  # Your app
]

DATABASES = {
    "default": {
        "ENGINE": "asyncpg",  # PostgreSQL
        "NAME": "mydb",
        "USER": "postgres",
        "PASSWORD": "password",
        "HOST": "localhost",
    }
}
```

### Define Models

```python
# blog/models.py
from fastdjango.db.models import Model
from fastdjango.db import fields

class Post(Model):
    title = fields.CharField(max_length=200)
    content = fields.TextField()
    published = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(auto_now_add=True)

    class Meta:
        table = "blog_post"
        ordering = ["-created_at"]
```

### Create Routes

```python
# blog/routes.py
from fastapi import Request
from fastdjango.routing import Router
from fastdjango.templates import render
from .models import Post

router = Router()

@router.get("/")
async def list_posts(request: Request):
    posts = await Post.objects.filter(published=True)
    return render("blog/list.html", {"posts": posts}, request=request)

@router.get("/api/posts")
async def api_posts():
    return await Post.objects.filter(published=True)
```

### Run

```bash
fastdjango migrate
fastdjango createsuperuser
fastdjango runserver
```

## Contents

1. [Installation](installation.md)
2. [Tutorial](tutorial.md)
3. [Models & ORM](models.md)
4. [Views & Routing](routing.md)
5. [Templates](templates.md)
6. [Authentication](auth.md)
7. [Admin](admin.md)
8. [WebSocket](websocket.md)
9. [Forms](forms.md)
10. [Settings](settings.md)
11. [CLI Commands](cli.md)
12. [API Reference](api.md)

## Why FastDjango?

- **Django Developer Experience**: Familiar syntax for Django developers
- **FastAPI Performance**: Built on FastAPI/Starlette for high performance
- **100% Async**: Native async/await throughout
- **WebSocket Native**: No need for Django Channels
- **Type Hints**: Full Pydantic integration
- **Auto API Docs**: OpenAPI/Swagger out of the box
