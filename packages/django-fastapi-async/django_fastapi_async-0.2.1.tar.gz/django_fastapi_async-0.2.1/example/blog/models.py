"""
Blog models.
"""

from fastdjango.db.models import Model
from fastdjango.db import fields


class Category(Model):
    """Blog category."""

    id = fields.IntegerField(primary_key=True)
    name = fields.CharField(max_length=100)
    slug = fields.SlugField(unique=True)
    description = fields.TextField(blank=True)

    class Meta:
        table = "blog_category"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Post(Model):
    """Blog post."""

    id = fields.IntegerField(primary_key=True)
    title = fields.CharField(max_length=200)
    slug = fields.SlugField(unique=True)
    content = fields.TextField()
    excerpt = fields.TextField(blank=True)
    published = fields.BooleanField(default=False)
    featured = fields.BooleanField(default=False)
    views = fields.IntegerField(default=0)
    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)

    # Relationships
    author = fields.ForeignKey("models.User", related_name="posts", null=True)
    category = fields.ForeignKey("models.Category", related_name="posts", null=True)

    class Meta:
        table = "blog_post"
        ordering = ["-created_at"]

    class Admin:
        list_display = ["title", "author", "category", "published", "created_at"]
        list_filter = ["published", "featured", "category"]
        search_fields = ["title", "content"]
        ordering = ["-created_at"]
        date_hierarchy = "created_at"

    def __str__(self):
        return self.title


class Comment(Model):
    """Blog comment."""

    id = fields.IntegerField(primary_key=True)
    post = fields.ForeignKey("models.Post", related_name="comments")
    author = fields.ForeignKey("models.User", related_name="comments", null=True)
    name = fields.CharField(max_length=100)
    email = fields.EmailField()
    content = fields.TextField()
    approved = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(auto_now_add=True)

    class Meta:
        table = "blog_comment"
        ordering = ["-created_at"]

    class Admin:
        list_display = ["name", "post", "approved", "created_at"]
        list_filter = ["approved"]
        search_fields = ["name", "content"]

    def __str__(self):
        return f"Comment by {self.name} on {self.post}"


class Tag(Model):
    """Blog tag."""

    id = fields.IntegerField(primary_key=True)
    name = fields.CharField(max_length=50, unique=True)
    slug = fields.SlugField(unique=True)

    class Meta:
        table = "blog_tag"
        ordering = ["name"]

    def __str__(self):
        return self.name
