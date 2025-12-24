"""
FastDjango Application - Main entry point
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Sequence

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware import Middleware as StarletteMiddleware
from tortoise import Tortoise

from fastdjango.conf import settings
from fastdjango.core.exceptions import Http404, PermissionDenied, BadRequest, Redirect
from fastdjango.templates import templates

if TYPE_CHECKING:
    from fastdjango.routing import Router


class FastDjango:
    """
    Main FastDjango application class.
    Similar to Django's WSGIApplication but async-first.
    """

    def __init__(
        self,
        settings_module: str | None = None,
        *,
        debug: bool | None = None,
        title: str = "FastDjango",
        version: str = "0.1.0",
    ):
        self.settings_module = settings_module
        self._app: FastAPI | None = None
        self._debug = debug
        self._title = title
        self._version = version
        self._routers: list[tuple[str, Router]] = []
        self._startup_handlers: list[Callable] = []
        self._shutdown_handlers: list[Callable] = []

    @property
    def app(self) -> FastAPI:
        """Get or create the FastAPI application."""
        if self._app is None:
            self._app = self._create_app()
        return self._app

    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        # Load settings
        if self.settings_module:
            settings.configure(self.settings_module)

        debug = self._debug if self._debug is not None else settings.DEBUG

        # Create FastAPI app
        app = FastAPI(
            title=self._title,
            version=self._version,
            debug=debug,
            docs_url="/api/docs" if debug else None,
            redoc_url="/api/redoc" if debug else None,
            openapi_url="/api/openapi.json" if debug else None,
        )

        # Register exception handlers
        self._register_exception_handlers(app)

        # Register middleware
        self._register_middleware(app)

        # Register startup/shutdown events
        self._register_events(app)

        # Auto-discover and register apps
        self._autodiscover_apps(app)

        # Mount static files
        self._mount_static_files(app)

        return app

    def _register_exception_handlers(self, app: FastAPI) -> None:
        """Register custom exception handlers."""

        @app.exception_handler(Http404)
        async def handle_404(request: Request, exc: Http404):
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=404,
                    content={"detail": str(exc) or "Not found"},
                )
            return templates.TemplateResponse(
                request=request,
                name="errors/404.html",
                status_code=404,
                context={"message": str(exc)},
            )

        @app.exception_handler(PermissionDenied)
        async def handle_403(request: Request, exc: PermissionDenied):
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=403,
                    content={"detail": str(exc) or "Permission denied"},
                )
            return templates.TemplateResponse(
                request=request,
                name="errors/403.html",
                status_code=403,
                context={"message": str(exc)},
            )

        @app.exception_handler(BadRequest)
        async def handle_400(request: Request, exc: BadRequest):
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=400,
                    content={"detail": str(exc) or "Bad request"},
                )
            return templates.TemplateResponse(
                request=request,
                name="errors/400.html",
                status_code=400,
                context={"message": str(exc)},
            )

        @app.exception_handler(Redirect)
        async def handle_redirect(request: Request, exc: Redirect):
            from starlette.responses import RedirectResponse
            return RedirectResponse(url=exc.url, status_code=exc.status_code)

    def _register_middleware(self, app: FastAPI) -> None:
        """Register middleware from settings."""
        from fastdjango.middleware import get_middleware_class

        for middleware_path in reversed(settings.MIDDLEWARE):
            middleware_class = get_middleware_class(middleware_path)
            if middleware_class:
                app.add_middleware(middleware_class)

    def _register_events(self, app: FastAPI) -> None:
        """Register startup and shutdown events."""

        @app.on_event("startup")
        async def startup():
            # Initialize database
            await self._init_database()

            # Initialize templates
            self._init_templates()

            # Run custom startup handlers
            for handler in self._startup_handlers:
                result = handler()
                if hasattr(result, "__await__"):
                    await result

        @app.on_event("shutdown")
        async def shutdown():
            # Close database connections
            await Tortoise.close_connections()

            # Run custom shutdown handlers
            for handler in self._shutdown_handlers:
                result = handler()
                if hasattr(result, "__await__"):
                    await result

    async def _init_database(self) -> None:
        """Initialize Tortoise ORM."""
        db_config = settings.DATABASES.get("default", {})

        if not db_config:
            return

        # Build Tortoise config
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
        elif engine == "asyncmy":
            db_url = (
                f"mysql://{db_config.get('USER', '')}:"
                f"{db_config.get('PASSWORD', '')}@"
                f"{db_config.get('HOST', 'localhost')}:"
                f"{db_config.get('PORT', 3306)}/"
                f"{db_config.get('NAME', '')}"
            )
        else:
            db_url = engine  # Assume it's a full URL

        # Discover models from installed apps
        models_modules = ["fastdjango.contrib.auth.models"]
        for app_name in settings.INSTALLED_APPS:
            if app_name.startswith("fastdjango."):
                continue
            models_modules.append(f"{app_name}.models")

        await Tortoise.init(
            db_url=db_url,
            modules={"models": models_modules},
        )

    def _init_templates(self) -> None:
        """Initialize Jinja2 templates."""
        from fastdjango.templates import configure_templates

        template_dirs = list(settings.TEMPLATES.get("DIRS", []))

        # Add app template directories
        for app_name in settings.INSTALLED_APPS:
            try:
                module = importlib.import_module(app_name)
                if hasattr(module, "__path__"):
                    app_path = Path(module.__path__[0])
                    templates_path = app_path / "templates"
                    if templates_path.exists():
                        template_dirs.append(str(templates_path))
            except ImportError:
                pass

        # Add contrib templates
        contrib_templates = Path(__file__).parent / "contrib" / "admin" / "templates"
        if contrib_templates.exists():
            template_dirs.append(str(contrib_templates))

        configure_templates(template_dirs)

    def _autodiscover_apps(self, app: FastAPI) -> None:
        """Auto-discover and register routes from installed apps."""
        for app_name in settings.INSTALLED_APPS:
            # Skip fastdjango contrib apps, they're registered separately
            if app_name == "fastdjango.contrib.admin":
                self._register_admin(app)
                continue
            elif app_name.startswith("fastdjango.contrib."):
                continue

            # Try to import routes module
            try:
                routes_module = importlib.import_module(f"{app_name}.routes")
                if hasattr(routes_module, "router"):
                    router = routes_module.router
                    prefix = getattr(router, "prefix", f"/{app_name.split('.')[-1]}")
                    app.include_router(router, prefix=prefix)
            except ImportError:
                pass

            # Try to import admin module for model registration
            try:
                importlib.import_module(f"{app_name}.admin")
            except ImportError:
                pass

    def _register_admin(self, app: FastAPI) -> None:
        """Register admin routes."""
        from fastdjango.contrib.admin import admin_router

        app.include_router(admin_router, prefix="/admin", tags=["admin"])

    def _mount_static_files(self, app: FastAPI) -> None:
        """Mount static files."""
        static_url = settings.STATIC_URL.rstrip("/")
        static_root = settings.STATIC_ROOT

        if static_root and Path(static_root).exists():
            app.mount(static_url, StaticFiles(directory=static_root), name="static")

        # Mount admin static files
        admin_static = Path(__file__).parent / "contrib" / "admin" / "static"
        if admin_static.exists():
            app.mount("/static/admin", StaticFiles(directory=str(admin_static)), name="admin_static")

    def include_router(self, router: Router, prefix: str = "") -> None:
        """Include a router in the application."""
        self._routers.append((prefix, router))
        if self._app:
            self._app.include_router(router, prefix=prefix)

    def on_startup(self, handler: Callable) -> Callable:
        """Register a startup handler."""
        self._startup_handlers.append(handler)
        return handler

    def on_shutdown(self, handler: Callable) -> Callable:
        """Register a shutdown handler."""
        self._shutdown_handlers.append(handler)
        return handler

    def __call__(self, scope, receive, send):
        """ASGI interface."""
        return self.app(scope, receive, send)


def get_application(settings_module: str | None = None) -> FastDjango:
    """
    Factory function to create a FastDjango application.

    Usage in asgi.py:
        from fastdjango import get_application
        app = get_application("myproject.settings")
    """
    return FastDjango(settings_module=settings_module)
