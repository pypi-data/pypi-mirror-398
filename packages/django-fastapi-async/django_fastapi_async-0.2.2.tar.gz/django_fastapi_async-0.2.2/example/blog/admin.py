"""
Blog admin configuration.
"""

from fastdjango.contrib.admin import admin_site, ModelAdmin, register
from .models import Post, Category, Comment, Tag


@register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@register(Post)
class PostAdmin(ModelAdmin):
    list_display = ["title", "category", "published", "featured", "views", "created_at"]
    list_filter = ["published", "featured", "category", "created_at"]
    search_fields = ["title", "content", "excerpt"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ["author"]

    fieldsets = [
        (None, {"fields": ["title", "slug", "content", "excerpt"]}),
        ("Categorization", {"fields": ["category"]}),
        ("Status", {"fields": ["published", "featured"]}),
        ("Metadata", {"fields": ["author", "views"]}),
    ]


@register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ["name", "email", "post", "approved", "created_at"]
    list_filter = ["approved", "created_at"]
    search_fields = ["name", "email", "content"]
    ordering = ["-created_at"]
    actions = ["approve_comments", "disapprove_comments"]

    async def approve_comments(self, request, queryset):
        """Approve selected comments."""
        await queryset.update(approved=True)

    async def disapprove_comments(self, request, queryset):
        """Disapprove selected comments."""
        await queryset.update(approved=False)


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
