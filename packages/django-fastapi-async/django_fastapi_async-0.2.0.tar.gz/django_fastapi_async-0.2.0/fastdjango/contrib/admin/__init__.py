"""
FastDjango Admin module.
Automatic CRUD admin interface.
"""

from fastdjango.contrib.admin.site import AdminSite, admin_site
from fastdjango.contrib.admin.options import ModelAdmin
from fastdjango.contrib.admin.decorators import register
from fastdjango.contrib.admin.routes import router as admin_router

# Shortcuts
site = admin_site

__all__ = [
    "AdminSite",
    "admin_site",
    "site",
    "ModelAdmin",
    "register",
    "admin_router",
]
