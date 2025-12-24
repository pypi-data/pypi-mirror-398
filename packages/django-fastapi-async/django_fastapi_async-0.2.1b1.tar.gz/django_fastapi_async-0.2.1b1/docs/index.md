# FastDjango Documentation

Welcome to FastDjango - a Django-like framework built on FastAPI.

**GitHub**: https://github.com/TWFBusiness/fastdjango

**PyPI**: https://pypi.org/project/django-fastapi-async/

## Quick Start

### Installation

```bash
pip install django-fastapi-async
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

## Documentation

### Getting Started
1. [Installation](installation.md)
2. [Tutorial](tutorial.md)

### Core Features
3. [Models & ORM](models.md)
4. [Views & Routing](routing.md)
5. [Templates](templates.md)
6. [Forms](forms.md)

### Authentication & Admin
7. [Authentication](auth.md)
8. [Admin Interface](admin.md)

### Advanced Features
9. [WebSocket](websocket.md)
10. [Cache](cache.md)
11. [Email](email.md)
12. [Signals](signals.md)
13. [Migrations](migrations.md)

### Reference
14. [Settings](settings.md)
15. [CLI Commands](cli.md)
16. [API Reference](api.md)

## Why FastDjango?

| Feature | Django | FastDjango |
|---------|--------|------------|
| ORM | Synchronous | **Async native** |
| Performance | Good | **Excellent** |
| WebSocket | Channels (separate) | **Built-in** |
| API | DRF (separate) | **FastAPI integrated** |
| Type hints | Partial | **Full (Pydantic)** |
| API docs | Manual | **Automatic (OpenAPI)** |

### Key Benefits

- **Django Developer Experience**: Familiar syntax for Django developers
- **FastAPI Performance**: Built on FastAPI/Starlette for high performance
- **100% Async**: Native async/await throughout
- **WebSocket Native**: No need for Django Channels
- **Type Hints**: Full Pydantic integration
- **Auto API Docs**: OpenAPI/Swagger out of the box
- **Cache Framework**: Memory, Redis, File, Database backends
- **Email Framework**: SMTP, Console, File backends
- **Signals**: Async event system
- **Admin**: Automatic CRUD interface

## Getting Help

- **GitHub Issues**: https://github.com/TWFBusiness/fastdjango/issues
- **Discussions**: https://github.com/TWFBusiness/fastdjango/discussions
