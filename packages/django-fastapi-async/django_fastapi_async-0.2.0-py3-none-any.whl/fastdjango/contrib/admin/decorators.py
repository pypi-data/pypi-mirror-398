"""
FastDjango Admin Decorators.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from fastdjango.db.models import Model
    from fastdjango.contrib.admin.options import ModelAdmin


def register(*models: type[Model], site: Any | None = None):
    """
    Decorator to register a model with the admin site.

    Usage:
        @admin.register(Post)
        class PostAdmin(ModelAdmin):
            list_display = ["title", "author"]

        @admin.register(Post, Comment)
        class ContentAdmin(ModelAdmin):
            list_display = ["id", "created_at"]
    """
    from fastdjango.contrib.admin.site import admin_site
    from fastdjango.contrib.admin.options import ModelAdmin

    def decorator(admin_class: type[ModelAdmin]) -> type[ModelAdmin]:
        admin_site_instance = site or admin_site

        for model in models:
            if admin_site_instance.is_registered(model):
                raise ValueError(
                    f"The model {model.__name__} is already registered "
                    f"with {admin_site_instance.name}"
                )
            admin_site_instance.register(model, admin_class)

        return admin_class

    return decorator


def action(
    function: Any = None,
    *,
    permissions: list[str] | None = None,
    description: str | None = None,
):
    """
    Decorator to mark a method as an admin action.

    Usage:
        @admin.register(Post)
        class PostAdmin(ModelAdmin):
            actions = ["make_published", "make_draft"]

            @action(description="Mark selected posts as published")
            async def make_published(self, request, queryset):
                await queryset.update(status="published")

            @action(permissions=["can_publish"], description="Make draft")
            async def make_draft(self, request, queryset):
                await queryset.update(status="draft")
    """

    def decorator(func: Any) -> Any:
        func.action_permissions = permissions or []
        func.short_description = description or func.__name__.replace("_", " ").title()
        return func

    if function is not None:
        return decorator(function)
    return decorator


def display(
    function: Any = None,
    *,
    description: str | None = None,
    ordering: str | None = None,
    boolean: bool = False,
    empty_value: str = "-",
):
    """
    Decorator to configure a display method.

    Usage:
        @admin.register(Post)
        class PostAdmin(ModelAdmin):
            list_display = ["title", "is_recent", "author_name"]

            @display(description="Recent?", boolean=True)
            def is_recent(self, obj):
                return obj.created_at > datetime.now() - timedelta(days=7)

            @display(description="Author", ordering="author__name")
            def author_name(self, obj):
                return obj.author.get_full_name()
    """

    def decorator(func: Any) -> Any:
        func.short_description = description or func.__name__.replace("_", " ").title()
        func.admin_order_field = ordering
        func.boolean = boolean
        func.empty_value_display = empty_value
        return func

    if function is not None:
        return decorator(function)
    return decorator
