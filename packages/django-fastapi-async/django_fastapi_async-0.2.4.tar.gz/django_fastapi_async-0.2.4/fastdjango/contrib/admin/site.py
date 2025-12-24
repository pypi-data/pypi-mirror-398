"""
FastDjango Admin Site.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from fastdjango.db.models import Model
    from fastdjango.contrib.admin.options import ModelAdmin


class AdminSite:
    """
    Admin site that holds all registered models.
    Similar to Django's AdminSite.
    """

    def __init__(self, name: str = "admin"):
        self.name = name
        self._registry: dict[type[Model], type[ModelAdmin]] = {}
        self.site_header = "FastDjango Administration"
        self.site_title = "FastDjango Admin"
        self.index_title = "Dashboard"

    def register(
        self,
        model: type[Model] | list[type[Model]],
        admin_class: type[ModelAdmin] | None = None,
        **options: Any,
    ) -> None:
        """
        Register a model (or list of models) with the admin site.

        Usage:
            admin.site.register(User)
            admin.site.register(User, UserAdmin)
            admin.site.register([Post, Comment], PostAdmin)
        """
        from fastdjango.contrib.admin.options import ModelAdmin

        if admin_class is None:
            admin_class = ModelAdmin

        if isinstance(model, (list, tuple)):
            for m in model:
                self._registry[m] = admin_class
        else:
            self._registry[model] = admin_class

    def unregister(self, model: type[Model] | list[type[Model]]) -> None:
        """Unregister a model from the admin site."""
        if isinstance(model, (list, tuple)):
            for m in model:
                self._registry.pop(m, None)
        else:
            self._registry.pop(model, None)

    def is_registered(self, model: type[Model]) -> bool:
        """Check if a model is registered."""
        return model in self._registry

    def get_model_admin(self, model: type[Model]) -> ModelAdmin | None:
        """Get the ModelAdmin for a registered model."""
        admin_class = self._registry.get(model)
        if admin_class:
            return admin_class(model, self)
        return None

    def get_registry(self) -> dict[type[Model], type[ModelAdmin]]:
        """Get all registered models."""
        return self._registry.copy()

    def get_app_list(self) -> list[dict[str, Any]]:
        """
        Get list of apps with their models for the admin index.
        Groups models by app_label.
        """
        apps: dict[str, list[dict[str, Any]]] = {}

        for model, admin_class in self._registry.items():
            app_label = getattr(model._meta, "app_label", None) or "app"
            model_name = model.__name__

            if app_label not in apps:
                apps[app_label] = []

            apps[app_label].append({
                "name": model_name,
                "object_name": model_name,
                "verbose_name": getattr(model._meta, "verbose_name", model_name),
                "verbose_name_plural": getattr(
                    model._meta, "verbose_name_plural", f"{model_name}s"
                ),
                "admin_url": f"/admin/{app_label}/{model_name.lower()}/",
                "add_url": f"/admin/{app_label}/{model_name.lower()}/add/",
                "model": model,
            })

        return [
            {
                "name": app_label,
                "app_label": app_label,
                "models": models,
            }
            for app_label, models in sorted(apps.items())
        ]

    def autodiscover(self) -> None:
        """
        Auto-discover admin modules in installed apps.
        Imports admin.py from each installed app.
        """
        import importlib
        from fastdjango.conf import settings

        for app_name in settings.INSTALLED_APPS:
            if app_name.startswith("fastdjango."):
                continue

            try:
                importlib.import_module(f"{app_name}.admin")
            except ImportError:
                pass


# Global admin site instance
admin_site = AdminSite()
