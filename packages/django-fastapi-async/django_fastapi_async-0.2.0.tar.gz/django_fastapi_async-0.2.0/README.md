# FastDjango

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/TWFBusiness/fastdjango.svg)](https://github.com/TWFBusiness/fastdjango/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/TWFBusiness/fastdjango.svg)](https://github.com/TWFBusiness/fastdjango/issues)

**Django-like framework built on FastAPI - 100% async**

FastDjango combina a facilidade de uso do Django com a performance do FastAPI. WebSocket nativo, ORM async, admin automático, e tudo que você precisa para construir aplicações web modernas.

## Features

- **100% Async** - Baseado em FastAPI/Starlette, totalmente assíncrono
- **ORM Django-like** - Sintaxe familiar: `Model.objects.filter(...)`
- **Admin Automático** - CRUD gerado automaticamente dos models
- **Autenticação Completa** - User, Group, Permission, sessions, JWT
- **WebSocket Nativo** - Sem precisar de Channels
- **Templates Jinja2** - Com filtros e tags estilo Django
- **CLI Completo** - startproject, startapp, migrate, runserver, etc.
- **Forms/Schemas** - Pydantic integrado com API Django-like

## Instalação

```bash
pip install fastdjango
```

## Quick Start

### Criar projeto

```bash
fastdjango startproject meusite
cd meusite
```

### Criar app

```bash
fastdjango startapp blog
```

### Definir models

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

    class Admin:
        list_display = ["title", "published", "created_at"]
        search_fields = ["title", "content"]
```

### Criar rotas

```python
# blog/routes.py
from fastapi import Request, WebSocket
from fastdjango.routing import Router
from fastdjango.templates import render
from fastdjango.contrib.auth.decorators import login_required

from .models import Post

router = Router()

# HTML view
@router.get("/")
async def index(request: Request):
    posts = await Post.objects.filter(published=True)
    return render("blog/index.html", {"posts": posts}, request=request)

# API endpoint
@router.get("/api/posts")
async def list_posts():
    return await Post.objects.filter(published=True)

# Protected route
@router.post("/api/posts")
@login_required
async def create_post(request: Request, data: PostCreate):
    return await Post.objects.create(**data.model_dump(), author=request.state.user)

# WebSocket
@router.websocket("/ws/live")
async def live_updates(websocket: WebSocket):
    await websocket.accept()
    async for message in websocket.iter_text():
        await websocket.send_text(f"Received: {message}")
```

### Configurar admin

```python
# blog/admin.py
from fastdjango.contrib.admin import register, ModelAdmin
from .models import Post

@register(Post)
class PostAdmin(ModelAdmin):
    list_display = ["title", "published", "created_at"]
    list_filter = ["published"]
    search_fields = ["title", "content"]
```

### Rodar

```bash
fastdjango migrate
fastdjango createsuperuser
fastdjango runserver
```

Acesse:
- Site: http://localhost:8000
- Admin: http://localhost:8000/admin
- API Docs: http://localhost:8000/api/docs

## Comparação com Django

| Feature | Django | FastDjango |
|---------|--------|------------|
| ORM | Síncrono | **Async nativo** |
| Performance | Boa | **Excelente** |
| WebSocket | Channels (separado) | **Nativo** |
| API | DRF (separado) | **Integrado (FastAPI)** |
| Tipagem | Parcial | **Completa (Pydantic)** |
| Docs API | Manual | **Automática (OpenAPI)** |
| Admin | Excelente | Bom (em desenvolvimento) |
| Maturidade | Alta | Inicial |

## Estrutura do Projeto

```
meusite/
├── manage.py
├── meusite/
│   ├── __init__.py
│   ├── settings.py      # Configurações (igual Django)
│   ├── urls.py          # URL patterns
│   └── asgi.py          # ASGI application
├── blog/
│   ├── __init__.py
│   ├── models.py        # Models ORM
│   ├── routes.py        # Views/API endpoints
│   ├── schemas.py       # Pydantic schemas
│   ├── admin.py         # Admin config
│   └── templates/
│       └── blog/
│           └── index.html
└── templates/
    └── base.html
```

## Settings

```python
# settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "your-secret-key"
DEBUG = True

INSTALLED_APPS = [
    "fastdjango.contrib.admin",
    "fastdjango.contrib.auth",
    "fastdjango.contrib.sessions",
    "blog",
]

MIDDLEWARE = [
    "fastdjango.middleware.SessionMiddleware",
    "fastdjango.middleware.AuthMiddleware",
    "fastdjango.middleware.CSRFMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "asyncpg",  # ou aiosqlite, asyncmy
        "NAME": "meusite",
        "USER": "postgres",
        "PASSWORD": "senha",
        "HOST": "localhost",
    }
}
```

## ORM

```python
# Queries (igual Django, mas async)
posts = await Post.objects.all()
posts = await Post.objects.filter(published=True)
posts = await Post.objects.filter(title__icontains="python")
posts = await Post.objects.exclude(published=False)
posts = await Post.objects.order_by("-created_at")

# Relacionamentos
posts = await Post.objects.select_related("author")
posts = await Post.objects.prefetch_related("comments")

# CRUD
post = await Post.objects.create(title="Hello", content="World")
post = await Post.objects.get(pk=1)
post = await Post.objects.get_or_404(pk=1)
await post.save()
await post.delete()

# Aggregations
from tortoise.functions import Count, Avg
posts = await Post.objects.annotate(comment_count=Count("comments"))
```

## Autenticação

```python
from fastdjango.contrib.auth import authenticate, login, logout
from fastdjango.contrib.auth.decorators import login_required, permission_required

# Login
user = await authenticate(request, username="john", password="secret")
if user:
    await login(request, user)

# Logout
await logout(request)

# Decorators
@router.get("/profile")
@login_required
async def profile(request: Request):
    return {"user": request.state.user.username}

@router.post("/admin/posts")
@permission_required("blog.add_post")
async def admin_create_post(request: Request):
    ...
```

## WebSocket

```python
from fastdjango.routing.websocket import ConnectionManager

manager = ConnectionManager()

@router.websocket("/ws/chat/{room}")
async def chat(websocket: WebSocket, room: str):
    await manager.connect(websocket, group=room)
    try:
        async for message in websocket.iter_text():
            # Broadcast para todos no room
            await manager.broadcast(message, room)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
```

## CLI Commands

```bash
fastdjango startproject <name>    # Criar projeto
fastdjango startapp <name>        # Criar app
fastdjango runserver              # Rodar servidor
fastdjango migrate                # Aplicar migrations
fastdjango makemigrations         # Criar migrations
fastdjango createsuperuser        # Criar superusuário
fastdjango shell                  # Shell interativo
fastdjango collectstatic          # Coletar static files
```

## Roadmap

- [x] Core framework
- [x] ORM wrapper (Tortoise)
- [x] Admin básico
- [x] Auth completo
- [x] Sessions
- [x] Middleware
- [x] Templates (Jinja2)
- [x] WebSocket
- [x] CLI
- [x] Forms/Schemas
- [ ] Migrations melhoradas (Aerich)
- [ ] Admin completo
- [ ] Signals async
- [ ] Cache
- [ ] Email
- [ ] Testes
- [ ] Documentação completa

## Contribuindo

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes.

## Links

- **GitHub**: https://github.com/TWFBusiness/fastdjango
- **Issues**: https://github.com/TWFBusiness/fastdjango/issues
- **Discussions**: https://github.com/TWFBusiness/fastdjango/discussions

## Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.
