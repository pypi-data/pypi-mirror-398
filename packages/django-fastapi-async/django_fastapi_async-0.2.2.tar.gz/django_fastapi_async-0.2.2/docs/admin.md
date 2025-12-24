# Admin Interface

FastDjango provides an automatic admin interface for managing your models.

## Setup

1. Add admin to installed apps:

```python
# settings.py
INSTALLED_APPS = [
    "fastdjango.contrib.admin",
    "fastdjango.contrib.auth",
    "fastdjango.contrib.sessions",
    # ...
]
```

2. Include admin routes:

```python
# urls.py
from fastdjango.contrib.admin import admin_router

app.include_router(admin_router, prefix="/admin")
```

3. Access at: `http://localhost:8000/admin/`

## Registering Models

### Basic Registration

```python
# blog/admin.py
from fastdjango.contrib.admin import register, ModelAdmin
from .models import Post

@register(Post)
class PostAdmin(ModelAdmin):
    pass
```

### With Options

```python
@register(Post)
class PostAdmin(ModelAdmin):
    # List view
    list_display = ["title", "author", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "content"]
    ordering = ["-created_at"]
    list_per_page = 25

    # Detail view
    fields = ["title", "content", "status", "author"]
    readonly_fields = ["created_at", "updated_at"]

    # Fieldsets (grouped fields)
    fieldsets = [
        (None, {"fields": ["title", "content"]}),
        ("Status", {"fields": ["status", "published_at"]}),
        ("Metadata", {"fields": ["author", "created_at"]}),
    ]
```

## ModelAdmin Options

### List View

```python
class PostAdmin(ModelAdmin):
    # Columns to display
    list_display = ["title", "author", "created_at"]

    # Clickable columns (first by default)
    list_display_links = ["title"]

    # Filter sidebar
    list_filter = ["status", "author", "created_at"]

    # Search box
    search_fields = ["title", "content", "author__username"]

    # Default ordering
    ordering = ["-created_at"]

    # Items per page
    list_per_page = 25

    # Related fields to fetch
    list_select_related = ["author"]
```

### Detail View

```python
class PostAdmin(ModelAdmin):
    # Fields to show (simple)
    fields = ["title", "content", "status"]

    # Fields to exclude
    exclude = ["slug"]

    # Read-only fields
    readonly_fields = ["created_at", "view_count"]

    # Grouped fields
    fieldsets = [
        (None, {
            "fields": ["title", "slug", "content"],
            "description": "Main content",
        }),
        ("Publishing", {
            "fields": ["status", "published_at"],
            "classes": ["collapse"],
        }),
    ]
```

## Filters

### Built-in Filters

```python
from fastdjango.contrib.admin import (
    BooleanFieldListFilter,
    DateFieldListFilter,
    ChoicesFieldListFilter,
)

class PostAdmin(ModelAdmin):
    list_filter = [
        "status",  # Auto-detect filter type
        ("is_featured", BooleanFieldListFilter),
        ("created_at", DateFieldListFilter),
    ]
```

### Custom Filter

```python
from fastdjango.contrib.admin import SimpleListFilter

class PublishedFilter(SimpleListFilter):
    title = "Published Status"
    parameter_name = "published"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Published"),
            ("no", "Not Published"),
            ("scheduled", "Scheduled"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(status="published")
        elif self.value() == "no":
            return queryset.filter(status="draft")
        elif self.value() == "scheduled":
            return queryset.filter(status="scheduled")
        return queryset

class PostAdmin(ModelAdmin):
    list_filter = [PublishedFilter]
```

## Inline Models

Edit related models inline:

### Tabular Inline

```python
from fastdjango.contrib.admin import TabularInline, register, ModelAdmin
from .models import Post, Comment

class CommentInline(TabularInline):
    model = Comment
    extra = 1  # Empty forms to show
    fields = ["author", "content", "created_at"]
    readonly_fields = ["created_at"]

@register(Post)
class PostAdmin(ModelAdmin):
    inlines = [CommentInline]
```

### Stacked Inline

```python
from fastdjango.contrib.admin import StackedInline

class CommentInline(StackedInline):
    model = Comment
    extra = 1
    max_num = 10  # Maximum inline items
    min_num = 0   # Minimum inline items
    can_delete = True
```

## Actions

### Built-in Actions

```python
class PostAdmin(ModelAdmin):
    actions = ["delete_selected"]  # Default
```

### Custom Actions

```python
class PostAdmin(ModelAdmin):
    actions = ["make_published", "make_draft"]

    async def make_published(self, request, queryset):
        """Mark selected posts as published."""
        await queryset.update(status="published")
        # Return message
        return f"Marked {await queryset.count()} posts as published"

    async def make_draft(self, request, queryset):
        """Mark selected posts as draft."""
        await queryset.update(status="draft")
```

## Permissions

```python
class PostAdmin(ModelAdmin):
    def has_add_permission(self, request):
        """Can user add posts?"""
        return request.state.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """Can user edit this post?"""
        if obj is None:
            return True
        return obj.author == request.state.user or request.state.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Can user delete this post?"""
        return request.state.user.is_superuser

    def has_view_permission(self, request, obj=None):
        """Can user view this post?"""
        return True
```

## Customization

### Custom Queryset

```python
class PostAdmin(ModelAdmin):
    def get_queryset(self):
        qs = super().get_queryset()
        # Only show user's own posts
        if not self.request.state.user.is_superuser:
            qs = qs.filter(author=self.request.state.user)
        return qs
```

### Custom Save

```python
class PostAdmin(ModelAdmin):
    async def save_model(self, obj, form_data, change):
        if not change:
            # New object - set author
            obj.author = self.request.state.user
        await super().save_model(obj, form_data, change)
```

## Admin Site Configuration

```python
from fastdjango.contrib.admin import admin_site

admin_site.site_header = "My Admin"
admin_site.site_title = "My Site Admin"
admin_site.index_title = "Dashboard"
```

## API Endpoints

Admin provides both HTML views and JSON API:

```
GET  /admin/                          # Dashboard
GET  /admin/api/models                # List all models
GET  /admin/{app}/{model}/            # List objects (HTML)
GET  /admin/api/{app}/{model}         # List objects (JSON)
GET  /admin/{app}/{model}/add/        # Add form (HTML)
POST /admin/api/{app}/{model}         # Create object (JSON)
GET  /admin/{app}/{model}/{pk}/change # Edit form (HTML)
PUT  /admin/api/{app}/{model}/{pk}    # Update object (JSON)
DELETE /admin/api/{app}/{model}/{pk}  # Delete object (JSON)
```
