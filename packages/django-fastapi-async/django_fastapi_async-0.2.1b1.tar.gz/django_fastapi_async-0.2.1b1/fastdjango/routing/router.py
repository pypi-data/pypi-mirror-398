"""
FastDjango Router.
Extended FastAPI router with Django-like features.
"""

from __future__ import annotations

import importlib
from typing import Any, Callable, Sequence, TYPE_CHECKING
from fastapi import APIRouter, Request, Response
from fastapi.routing import APIRoute

if TYPE_CHECKING:
    from pydantic import BaseModel


class Router(APIRouter):
    """
    Extended FastAPI router with Django-like features.

    Usage:
        router = Router()

        @router.get("/posts")
        async def list_posts():
            return await Post.objects.all()

        @router.get("/posts/{pk}")
        async def get_post(pk: int):
            return await Post.objects.get_or_404(pk=pk)

        @router.post("/posts")
        async def create_post(data: PostCreate):
            return await Post.objects.create(**data.model_dump())
    """

    def __init__(
        self,
        *,
        prefix: str = "",
        tags: list[str] | None = None,
        dependencies: Sequence | None = None,
        responses: dict[int | str, dict[str, Any]] | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            responses=responses,
            **kwargs,
        )
        self._websocket_routes: list[tuple[str, Callable]] = []

    def websocket(self, path: str):
        """
        Decorator to add a WebSocket route.

        Usage:
            @router.websocket("/ws/chat")
            async def chat(websocket: WebSocket):
                await websocket.accept()
                async for message in websocket.iter_text():
                    await websocket.send_text(f"Echo: {message}")
        """
        def decorator(func: Callable) -> Callable:
            self.add_api_websocket_route(path, func)
            self._websocket_routes.append((path, func))
            return func
        return decorator

    def view(self, path: str, *, methods: list[str] | None = None, **kwargs: Any):
        """
        Decorator for class-based views (CBV).

        Usage:
            @router.view("/posts")
            class PostView:
                async def get(self, request: Request):
                    return await Post.objects.all()

                async def post(self, request: Request, data: PostCreate):
                    return await Post.objects.create(**data.model_dump())
        """
        def decorator(cls: type) -> type:
            instance = cls()

            # Register methods as routes
            for method_name in ["get", "post", "put", "patch", "delete", "head", "options"]:
                if hasattr(instance, method_name):
                    method = getattr(instance, method_name)
                    route_methods = [method_name.upper()]
                    self.add_api_route(
                        path,
                        method,
                        methods=route_methods,
                        **kwargs,
                    )

            return cls

        return decorator

    def include(self, router: Router, prefix: str = "") -> None:
        """Include another router."""
        self.include_router(router, prefix=prefix)


class ViewSet:
    """
    Base class for ViewSets.
    Provides automatic CRUD routing.

    Usage:
        class PostViewSet(ViewSet):
            model = Post
            schema = PostSchema
            create_schema = PostCreate
            update_schema = PostUpdate

            # Optional overrides
            async def get_queryset(self):
                return self.model.objects.filter(published=True)

        # In routes.py
        router = Router()
        PostViewSet.register(router, prefix="/posts")
    """

    model: type = None  # type: ignore
    schema: type = None  # type: ignore
    create_schema: type = None  # type: ignore
    update_schema: type = None  # type: ignore
    lookup_field: str = "pk"
    lookup_url_kwarg: str | None = None

    def __init__(self):
        self.request: Request | None = None

    async def get_queryset(self):
        """Get the base queryset. Override for filtering."""
        return self.model.objects.all()

    async def get_object(self, **kwargs):
        """Get a single object."""
        qs = await self.get_queryset()
        return await qs.get_or_404(**kwargs)

    async def list(self, request: Request):
        """List all objects."""
        qs = await self.get_queryset()
        return await qs

    async def retrieve(self, request: Request, pk: int):
        """Get a single object."""
        return await self.get_object(pk=pk)

    async def create(self, request: Request, data: Any):
        """Create a new object."""
        return await self.model.objects.create(**data.model_dump())

    async def update(self, request: Request, pk: int, data: Any):
        """Update an object."""
        obj = await self.get_object(pk=pk)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        await obj.save()
        return obj

    async def partial_update(self, request: Request, pk: int, data: Any):
        """Partially update an object."""
        return await self.update(request, pk, data)

    async def destroy(self, request: Request, pk: int):
        """Delete an object."""
        obj = await self.get_object(pk=pk)
        await obj.delete()
        return {"detail": "Deleted successfully"}

    @classmethod
    def register(cls, router: Router, prefix: str = "") -> None:
        """Register viewset routes on a router."""
        instance = cls()

        # List and Create
        @router.get(prefix or "/")
        async def list_view(request: Request):
            return await instance.list(request)

        @router.post(prefix or "/")
        async def create_view(request: Request, data: cls.create_schema):
            return await instance.create(request, data)

        # Retrieve, Update, Delete
        detail_path = f"{prefix}/{{pk}}" if prefix else "/{pk}"

        @router.get(detail_path)
        async def retrieve_view(request: Request, pk: int):
            return await instance.retrieve(request, pk)

        @router.put(detail_path)
        async def update_view(request: Request, pk: int, data: cls.update_schema):
            return await instance.update(request, pk, data)

        @router.patch(detail_path)
        async def partial_update_view(request: Request, pk: int, data: cls.update_schema):
            return await instance.partial_update(request, pk, data)

        @router.delete(detail_path)
        async def destroy_view(request: Request, pk: int):
            return await instance.destroy(request, pk)


def include(path: str, module: str) -> tuple[str, Router]:
    """
    Include routes from a module.

    Usage:
        urlpatterns = [
            include("/api/blog", "blog.routes"),
            include("/api/users", "users.routes"),
        ]
    """
    try:
        mod = importlib.import_module(module)
        router = getattr(mod, "router", None)
        if router is None:
            raise ImportError(f"Module {module} has no 'router' attribute")
        return (path, router)
    except ImportError as e:
        raise ImportError(f"Could not import {module}: {e}")


def path(route: str, endpoint: Callable, *, methods: list[str] | None = None, **kwargs) -> dict:
    """
    Create a route definition.

    Usage:
        urlpatterns = [
            path("/", home_view),
            path("/about", about_view, methods=["GET"]),
        ]
    """
    return {
        "path": route,
        "endpoint": endpoint,
        "methods": methods or ["GET"],
        **kwargs,
    }
