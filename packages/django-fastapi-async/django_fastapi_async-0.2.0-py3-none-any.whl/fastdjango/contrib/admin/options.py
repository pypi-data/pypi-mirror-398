"""
FastDjango Admin Options (ModelAdmin).
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING, Sequence
from pydantic import BaseModel, create_model

if TYPE_CHECKING:
    from fastdjango.db.models import Model
    from fastdjango.contrib.admin.site import AdminSite


class ModelAdmin:
    """
    Admin configuration for a model.
    Similar to Django's ModelAdmin.

    Usage:
        @admin.register(Post)
        class PostAdmin(ModelAdmin):
            list_display = ["title", "author", "created_at"]
            list_filter = ["status", "created_at"]
            search_fields = ["title", "content"]
            ordering = ["-created_at"]
    """

    # List view options
    list_display: Sequence[str] = ["__str__"]
    list_display_links: Sequence[str] | None = None
    list_filter: Sequence[str] = []
    list_select_related: bool | Sequence[str] = False
    list_per_page: int = 25
    list_max_show_all: int = 200
    search_fields: Sequence[str] = []
    ordering: Sequence[str] | None = None

    # Detail view options
    fields: Sequence[str] | None = None
    exclude: Sequence[str] | None = None
    readonly_fields: Sequence[str] = []
    fieldsets: Sequence[tuple[str | None, dict[str, Any]]] | None = None

    # Form options
    form: type | None = None
    add_form: type | None = None

    # Relationships
    raw_id_fields: Sequence[str] = []
    autocomplete_fields: Sequence[str] = []
    prepopulated_fields: dict[str, Sequence[str]] = {}
    filter_horizontal: Sequence[str] = []
    filter_vertical: Sequence[str] = []

    # Actions
    actions: Sequence[str] = ["delete_selected"]
    actions_on_top: bool = True
    actions_on_bottom: bool = False
    actions_selection_counter: bool = True

    # Other options
    date_hierarchy: str | None = None
    save_as: bool = False
    save_as_continue: bool = True
    save_on_top: bool = False
    preserve_filters: bool = True
    show_full_result_count: bool = True

    def __init__(self, model: type[Model], admin_site: AdminSite):
        self.model = model
        self.admin_site = admin_site
        self.opts = model._meta

    def get_list_display(self) -> list[str]:
        """Get fields to display in list view."""
        return list(self.list_display)

    def get_list_filter(self) -> list[str]:
        """Get fields for filtering."""
        return list(self.list_filter)

    def get_search_fields(self) -> list[str]:
        """Get fields for searching."""
        return list(self.search_fields)

    def get_ordering(self) -> list[str]:
        """Get ordering for list view."""
        if self.ordering:
            return list(self.ordering)
        return getattr(self.opts, "ordering", []) or ["-pk"]

    def get_queryset(self):
        """Get the queryset for the list view."""
        qs = self.model.objects.all()

        # Apply ordering
        ordering = self.get_ordering()
        if ordering:
            qs = qs.order_by(*ordering)

        # Apply select_related
        if self.list_select_related is True:
            qs = qs.select_related()
        elif self.list_select_related:
            qs = qs.select_related(*self.list_select_related)

        return qs

    def get_fields(self) -> list[str]:
        """Get fields for detail/edit form."""
        if self.fields:
            return list(self.fields)

        # Auto-discover fields from model
        fields = []
        for field_name in self.model._meta.fields_map:
            if self.exclude and field_name in self.exclude:
                continue
            fields.append(field_name)

        return fields

    def get_readonly_fields(self) -> list[str]:
        """Get read-only fields."""
        return list(self.readonly_fields)

    def get_fieldsets(self) -> list[tuple[str | None, dict[str, Any]]]:
        """Get fieldsets for detail view."""
        if self.fieldsets:
            return list(self.fieldsets)

        # Default: single fieldset with all fields
        return [(None, {"fields": self.get_fields()})]

    async def get_object(self, pk: Any) -> Model | None:
        """Get a single object by primary key."""
        return await self.model.objects.get_or_none(pk=pk)

    async def save_model(self, obj: Model, form_data: dict[str, Any], change: bool) -> None:
        """Save the model instance."""
        for key, value in form_data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await obj.save()

    async def delete_model(self, obj: Model) -> None:
        """Delete the model instance."""
        await obj.delete()

    def get_pydantic_schema(self) -> type[BaseModel]:
        """Generate Pydantic schema for the model."""
        fields_dict: dict[str, Any] = {}

        for field_name in self.get_fields():
            if field_name in self.get_readonly_fields():
                continue

            field = self.model._meta.fields_map.get(field_name)
            if field is None:
                continue

            # Map field types to Python types
            field_type = self._get_python_type(field)
            if field_type:
                # Check if field is optional
                if getattr(field, "null", False):
                    fields_dict[field_name] = (field_type | None, None)
                else:
                    default = getattr(field, "default", ...)
                    fields_dict[field_name] = (field_type, default if default is not None else ...)

        return create_model(f"{self.model.__name__}Schema", **fields_dict)

    def _get_python_type(self, field: Any) -> type | None:
        """Map a model field to a Python type."""
        field_class_name = field.__class__.__name__

        type_mapping = {
            "IntField": int,
            "BigIntField": int,
            "SmallIntField": int,
            "CharField": str,
            "TextField": str,
            "BooleanField": bool,
            "FloatField": float,
            "DecimalField": float,
            "DateField": str,  # ISO format
            "DatetimeField": str,
            "TimeField": str,
            "JSONField": dict,
            "UUIDField": str,
        }

        return type_mapping.get(field_class_name, str)

    def has_add_permission(self, request: Any) -> bool:
        """Check if user can add objects."""
        user = getattr(request.state, "user", None)
        if user is None:
            return False
        return getattr(user, "is_staff", False)

    def has_change_permission(self, request: Any, obj: Model | None = None) -> bool:
        """Check if user can change objects."""
        user = getattr(request.state, "user", None)
        if user is None:
            return False
        return getattr(user, "is_staff", False)

    def has_delete_permission(self, request: Any, obj: Model | None = None) -> bool:
        """Check if user can delete objects."""
        user = getattr(request.state, "user", None)
        if user is None:
            return False
        return getattr(user, "is_staff", False)

    def has_view_permission(self, request: Any, obj: Model | None = None) -> bool:
        """Check if user can view objects."""
        user = getattr(request.state, "user", None)
        if user is None:
            return False
        return getattr(user, "is_staff", False)
