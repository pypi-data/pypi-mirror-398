"""
FastDjango Admin Inlines.
Inline model editing in admin interface.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from fastapi import Request
    from fastdjango.db.models import Model
    from fastdjango.contrib.admin.site import AdminSite


class InlineModelAdmin:
    """
    Base class for inline model admins.

    Usage:
        class CommentInline(TabularInline):
            model = Comment
            extra = 3
            fields = ["author", "text", "created_at"]
            readonly_fields = ["created_at"]
    """

    model: type[Model] | None = None
    fk_name: str | None = None
    formset: type | None = None
    extra: int = 3
    min_num: int | None = None
    max_num: int | None = None
    can_delete: bool = True
    show_change_link: bool = False
    verbose_name: str | None = None
    verbose_name_plural: str | None = None

    # Field options
    fields: Sequence[str] | None = None
    exclude: Sequence[str] | None = None
    readonly_fields: Sequence[str] = []

    # Ordering
    ordering: Sequence[str] | None = None

    # Template
    template: str | None = None

    def __init__(self, parent_model: type[Model], admin_site: AdminSite):
        self.parent_model = parent_model
        self.admin_site = admin_site

        if self.verbose_name is None and self.model:
            self.verbose_name = self.model.__name__
        if self.verbose_name_plural is None and self.verbose_name:
            self.verbose_name_plural = f"{self.verbose_name}s"

    def get_queryset(self, request: Request, parent_obj: Model) -> Any:
        """Get queryset for inline objects related to parent."""
        if self.model is None:
            return []

        # Find the FK field name
        fk_name = self.fk_name
        if fk_name is None:
            # Auto-detect FK field
            for field_name, field in self.model._meta.fields_map.items():
                if hasattr(field, "related_model"):
                    if field.related_model is self.parent_model:
                        fk_name = field_name
                        break

        if fk_name is None:
            return []

        qs = self.model.objects.filter(**{fk_name: parent_obj})

        if self.ordering:
            qs = qs.order_by(*self.ordering)

        return qs

    def get_fields(self) -> list[str]:
        """Get fields to display."""
        if self.fields:
            return list(self.fields)

        if self.model is None:
            return []

        # Auto-discover fields
        fields = []
        for field_name in self.model._meta.fields_map:
            if field_name == "id":
                continue
            if self.exclude and field_name in self.exclude:
                continue
            fields.append(field_name)

        return fields

    def get_readonly_fields(self, request: Request) -> list[str]:
        """Get read-only fields."""
        return list(self.readonly_fields)

    def has_add_permission(self, request: Request, obj: Model | None = None) -> bool:
        """Check if user can add inline objects."""
        user = getattr(request.state, "user", None)
        if user is None:
            return False
        return getattr(user, "is_staff", False)

    def has_change_permission(self, request: Request, obj: Model | None = None) -> bool:
        """Check if user can change inline objects."""
        user = getattr(request.state, "user", None)
        if user is None:
            return False
        return getattr(user, "is_staff", False)

    def has_delete_permission(self, request: Request, obj: Model | None = None) -> bool:
        """Check if user can delete inline objects."""
        if not self.can_delete:
            return False
        user = getattr(request.state, "user", None)
        if user is None:
            return False
        return getattr(user, "is_staff", False)


class TabularInline(InlineModelAdmin):
    """
    Inline displayed as a table.
    Each inline object is a row in the table.
    """

    template = "admin/edit_inline/tabular.html"


class StackedInline(InlineModelAdmin):
    """
    Inline displayed as stacked forms.
    Each inline object is displayed vertically.
    """

    template = "admin/edit_inline/stacked.html"


__all__ = [
    "InlineModelAdmin",
    "TabularInline",
    "StackedInline",
]
