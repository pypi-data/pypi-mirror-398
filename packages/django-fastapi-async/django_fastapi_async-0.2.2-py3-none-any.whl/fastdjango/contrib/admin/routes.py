"""
FastDjango Admin Routes.
API and HTML endpoints for admin interface.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Request, HTTPException, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from fastdjango.contrib.admin.site import admin_site
from fastdjango.contrib.auth.decorators import staff_member_required
from fastdjango.templates import templates

router = APIRouter()


# ============== API Endpoints ==============

@router.get("/api/models")
@staff_member_required
async def list_models(request: Request):
    """List all registered models."""
    return admin_site.get_app_list()


@router.get("/api/{app_label}/{model_name}")
@staff_member_required
async def list_objects(
    request: Request,
    app_label: str,
    model_name: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    search: str | None = None,
    ordering: str | None = None,
):
    """List objects for a model."""
    model_admin = _get_model_admin(app_label, model_name)
    if model_admin is None:
        raise HTTPException(status_code=404, detail="Model not found")

    # Get queryset
    qs = model_admin.get_queryset()

    # Apply search
    if search:
        search_fields = model_admin.get_search_fields()
        if search_fields:
            from tortoise.expressions import Q
            q = Q()
            for field in search_fields:
                q |= Q(**{f"{field}__icontains": search})
            qs = qs.filter(q)

    # Apply ordering
    if ordering:
        qs = qs.order_by(ordering)

    # Count total
    total = await qs.count()

    # Paginate
    offset = (page - 1) * per_page
    objects = await qs.offset(offset).limit(per_page)

    # Serialize
    list_display = model_admin.get_list_display()
    items = []
    for obj in objects:
        item = {"pk": obj.pk}
        for field in list_display:
            if field == "__str__":
                item["__str__"] = str(obj)
            elif hasattr(obj, field):
                value = getattr(obj, field)
                # Handle callables
                if callable(value):
                    value = value()
                item[field] = value
        items.append(item)

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/api/{app_label}/{model_name}/{pk}")
@staff_member_required
async def get_object(
    request: Request,
    app_label: str,
    model_name: str,
    pk: int,
):
    """Get a single object."""
    model_admin = _get_model_admin(app_label, model_name)
    if model_admin is None:
        raise HTTPException(status_code=404, detail="Model not found")

    obj = await model_admin.get_object(pk)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")

    # Serialize all fields
    fields = model_admin.get_fields()
    data = {"pk": obj.pk}
    for field in fields:
        if hasattr(obj, field):
            data[field] = getattr(obj, field)

    return data


@router.post("/api/{app_label}/{model_name}")
@staff_member_required
async def create_object(
    request: Request,
    app_label: str,
    model_name: str,
):
    """Create a new object."""
    model_admin = _get_model_admin(app_label, model_name)
    if model_admin is None:
        raise HTTPException(status_code=404, detail="Model not found")

    if not model_admin.has_add_permission(request):
        raise HTTPException(status_code=403, detail="Permission denied")

    data = await request.json()
    obj = model_admin.model()
    await model_admin.save_model(obj, data, change=False)

    return {"pk": obj.pk, "message": "Created successfully"}


@router.put("/api/{app_label}/{model_name}/{pk}")
@staff_member_required
async def update_object(
    request: Request,
    app_label: str,
    model_name: str,
    pk: int,
):
    """Update an object."""
    model_admin = _get_model_admin(app_label, model_name)
    if model_admin is None:
        raise HTTPException(status_code=404, detail="Model not found")

    obj = await model_admin.get_object(pk)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")

    if not model_admin.has_change_permission(request, obj):
        raise HTTPException(status_code=403, detail="Permission denied")

    data = await request.json()
    await model_admin.save_model(obj, data, change=True)

    return {"pk": obj.pk, "message": "Updated successfully"}


@router.delete("/api/{app_label}/{model_name}/{pk}")
@staff_member_required
async def delete_object(
    request: Request,
    app_label: str,
    model_name: str,
    pk: int,
):
    """Delete an object."""
    model_admin = _get_model_admin(app_label, model_name)
    if model_admin is None:
        raise HTTPException(status_code=404, detail="Model not found")

    obj = await model_admin.get_object(pk)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")

    if not model_admin.has_delete_permission(request, obj):
        raise HTTPException(status_code=403, detail="Permission denied")

    await model_admin.delete_model(obj)

    return {"message": "Deleted successfully"}


@router.post("/api/{app_label}/{model_name}/action/{action_name}")
@staff_member_required
async def execute_action(
    request: Request,
    app_label: str,
    model_name: str,
    action_name: str,
):
    """Execute a bulk action on selected objects."""
    model_admin = _get_model_admin(app_label, model_name)
    if model_admin is None:
        raise HTTPException(status_code=404, detail="Model not found")

    data = await request.json()
    pks = data.get("pks", [])

    if not pks:
        raise HTTPException(status_code=400, detail="No objects selected")

    # Get action method
    action_method = getattr(model_admin, action_name, None)
    if action_method is None or action_name not in model_admin.actions:
        raise HTTPException(status_code=404, detail="Action not found")

    # Get queryset
    qs = model_admin.model.objects.filter(pk__in=pks)

    # Execute action
    result = action_method(request, qs)
    if hasattr(result, "__await__"):
        result = await result

    return {"message": f"Action '{action_name}' executed on {len(pks)} objects"}


# ============== HTML Views ==============

@router.get("/", response_class=HTMLResponse)
@staff_member_required
async def admin_index(request: Request):
    """Admin dashboard."""
    app_list = admin_site.get_app_list()
    return templates.TemplateResponse(
        request=request,
        name="admin/index.html",
        context={
            "app_list": app_list,
            "site_header": admin_site.site_header,
            "site_title": admin_site.site_title,
            "index_title": admin_site.index_title,
        },
    )


@router.get("/{app_label}/{model_name}/", response_class=HTMLResponse)
@staff_member_required
async def admin_changelist(
    request: Request,
    app_label: str,
    model_name: str,
    page: int = Query(1, ge=1),
):
    """Model list view."""
    model_admin = _get_model_admin(app_label, model_name)
    if model_admin is None:
        raise HTTPException(status_code=404, detail="Model not found")

    return templates.TemplateResponse(
        request=request,
        name="admin/changelist.html",
        context={
            "app_label": app_label,
            "model_name": model_name,
            "model_admin": model_admin,
            "site_header": admin_site.site_header,
            "list_display": model_admin.get_list_display(),
            "search_fields": model_admin.get_search_fields(),
        },
    )


@router.get("/{app_label}/{model_name}/add/", response_class=HTMLResponse)
@staff_member_required
async def admin_add(
    request: Request,
    app_label: str,
    model_name: str,
):
    """Add object view."""
    model_admin = _get_model_admin(app_label, model_name)
    if model_admin is None:
        raise HTTPException(status_code=404, detail="Model not found")

    if not model_admin.has_add_permission(request):
        raise HTTPException(status_code=403, detail="Permission denied")

    return templates.TemplateResponse(
        request=request,
        name="admin/change_form.html",
        context={
            "app_label": app_label,
            "model_name": model_name,
            "model_admin": model_admin,
            "site_header": admin_site.site_header,
            "fieldsets": model_admin.get_fieldsets(),
            "is_add": True,
            "object": None,
        },
    )


@router.get("/{app_label}/{model_name}/{pk}/change/", response_class=HTMLResponse)
@staff_member_required
async def admin_change(
    request: Request,
    app_label: str,
    model_name: str,
    pk: int,
):
    """Edit object view."""
    model_admin = _get_model_admin(app_label, model_name)
    if model_admin is None:
        raise HTTPException(status_code=404, detail="Model not found")

    obj = await model_admin.get_object(pk)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")

    if not model_admin.has_change_permission(request, obj):
        raise HTTPException(status_code=403, detail="Permission denied")

    return templates.TemplateResponse(
        request=request,
        name="admin/change_form.html",
        context={
            "app_label": app_label,
            "model_name": model_name,
            "model_admin": model_admin,
            "site_header": admin_site.site_header,
            "fieldsets": model_admin.get_fieldsets(),
            "is_add": False,
            "object": obj,
        },
    )


# ============== Helpers ==============

def _get_model_admin(app_label: str, model_name: str):
    """Get ModelAdmin by app_label and model_name."""
    for model, admin_class in admin_site.get_registry().items():
        model_app = getattr(model._meta, "app_label", None) or "app"
        if model_app == app_label and model.__name__.lower() == model_name.lower():
            return admin_class(model, admin_site)
    return None
