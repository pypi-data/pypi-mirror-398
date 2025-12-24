"""
FastDjango Admin module.
Automatic CRUD admin interface.
"""

from fastdjango.contrib.admin.site import AdminSite, admin_site
from fastdjango.contrib.admin.options import ModelAdmin
from fastdjango.contrib.admin.decorators import register
from fastdjango.contrib.admin.routes import router as admin_router
from fastdjango.contrib.admin.filters import (
    ListFilter,
    SimpleListFilter,
    FieldListFilter,
    BooleanFieldListFilter,
    ChoicesFieldListFilter,
    DateFieldListFilter,
    AllValuesFieldListFilter,
    RelatedFieldListFilter,
    EmptyFieldListFilter,
)
from fastdjango.contrib.admin.inlines import (
    InlineModelAdmin,
    TabularInline,
    StackedInline,
)

# Shortcuts
site = admin_site

__all__ = [
    # Site
    "AdminSite",
    "admin_site",
    "site",
    # Options
    "ModelAdmin",
    # Decorators
    "register",
    # Router
    "admin_router",
    # Filters
    "ListFilter",
    "SimpleListFilter",
    "FieldListFilter",
    "BooleanFieldListFilter",
    "ChoicesFieldListFilter",
    "DateFieldListFilter",
    "AllValuesFieldListFilter",
    "RelatedFieldListFilter",
    "EmptyFieldListFilter",
    # Inlines
    "InlineModelAdmin",
    "TabularInline",
    "StackedInline",
]
