"""
FastDjango Auth Models.
User, Group, Permission models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar
from tortoise import fields as tortoise_fields

from fastdjango.db.models import Model
from fastdjango.db import fields
from fastdjango.db.manager import Manager


class Permission(Model):
    """
    Permission model.
    Similar to Django's Permission model.
    """

    id = fields.IntegerField(primary_key=True)
    name = fields.CharField(max_length=255)
    codename = fields.CharField(max_length=100, unique=True)
    content_type = fields.CharField(max_length=100)  # app_label.model_name

    class Meta:
        table = "auth_permission"
        ordering = ["content_type", "codename"]
        unique_together = [("content_type", "codename")]

    def __str__(self) -> str:
        return f"{self.content_type} | {self.name}"

    @classmethod
    async def get_or_create_for_model(
        cls,
        model: type[Model],
        codename: str,
        name: str,
    ) -> Permission:
        """Create or get a permission for a model."""
        content_type = f"{model._meta.app_label or 'app'}.{model._meta.model_name}"
        perm, _ = await cls.get_or_create(
            codename=codename,
            content_type=content_type,
            defaults={"name": name},
        )
        return perm


class Group(Model):
    """
    Group model.
    Similar to Django's Group model.
    """

    id = fields.IntegerField(primary_key=True)
    name = fields.CharField(max_length=150, unique=True)
    permissions = fields.ManyToManyField(
        "models.Permission",
        related_name="groups",
        through="auth_group_permissions",
    )

    class Meta:
        table = "auth_group"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class AbstractUser(Model):
    """
    Abstract base user model.
    Provides core user fields and functionality.
    """

    id = fields.IntegerField(primary_key=True)
    username = fields.CharField(max_length=150, unique=True, index=True)
    email = fields.EmailField(max_length=254, unique=True, index=True)
    password = fields.CharField(max_length=128)

    first_name = fields.CharField(max_length=150, blank=True)
    last_name = fields.CharField(max_length=150, blank=True)

    is_active = fields.BooleanField(default=True)
    is_staff = fields.BooleanField(default=False)
    is_superuser = fields.BooleanField(default=False)

    date_joined = fields.DateTimeField(auto_now_add=True)
    last_login = fields.DateTimeField(null=True)

    class Meta:
        abstract = True

    # Username field for authentication
    USERNAME_FIELD: ClassVar[str] = "username"
    EMAIL_FIELD: ClassVar[str] = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = ["email"]

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return True

    @property
    def is_anonymous(self) -> bool:
        """Check if user is anonymous."""
        return False

    def get_username(self) -> str:
        """Return the username."""
        return getattr(self, self.USERNAME_FIELD)

    def get_full_name(self) -> str:
        """Return full name."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username

    def get_short_name(self) -> str:
        """Return short name."""
        return self.first_name or self.username

    async def set_password(self, raw_password: str) -> None:
        """Set the password (hashed)."""
        from fastdjango.contrib.auth.hashers import make_password

        self.password = make_password(raw_password)

    async def check_password(self, raw_password: str) -> bool:
        """Check if password is correct."""
        from fastdjango.contrib.auth.hashers import check_password

        return check_password(raw_password, self.password)

    async def set_unusable_password(self) -> None:
        """Set an unusable password."""
        self.password = "!"

    def has_usable_password(self) -> bool:
        """Check if user has a usable password."""
        return self.password and not self.password.startswith("!")


class PermissionsMixin(Model):
    """
    Mixin for permission-related functionality.
    """

    groups = fields.ManyToManyField(
        "models.Group",
        related_name="users",
        through="auth_user_groups",
    )
    user_permissions = fields.ManyToManyField(
        "models.Permission",
        related_name="users",
        through="auth_user_permissions",
    )

    class Meta:
        abstract = True

    async def get_user_permissions(self) -> set[str]:
        """Get all permissions for this user."""
        if not self.is_active:
            return set()

        perms = await self.user_permissions.all()
        return {f"{p.content_type}.{p.codename}" for p in perms}

    async def get_group_permissions(self) -> set[str]:
        """Get all permissions from groups."""
        if not self.is_active:
            return set()

        groups = await self.groups.all().prefetch_related("permissions")
        perms = set()
        for group in groups:
            group_perms = await group.permissions.all()
            for p in group_perms:
                perms.add(f"{p.content_type}.{p.codename}")
        return perms

    async def get_all_permissions(self) -> set[str]:
        """Get all permissions (user + group)."""
        if not self.is_active:
            return set()

        if self.is_superuser:
            # Superuser has all permissions
            all_perms = await Permission.objects.all()
            return {f"{p.content_type}.{p.codename}" for p in all_perms}

        user_perms = await self.get_user_permissions()
        group_perms = await self.get_group_permissions()
        return user_perms | group_perms

    async def has_perm(self, perm: str) -> bool:
        """Check if user has a specific permission."""
        if not self.is_active:
            return False

        if self.is_superuser:
            return True

        all_perms = await self.get_all_permissions()
        return perm in all_perms

    async def has_perms(self, perms: list[str]) -> bool:
        """Check if user has all specified permissions."""
        for perm in perms:
            if not await self.has_perm(perm):
                return False
        return True

    async def has_module_perms(self, app_label: str) -> bool:
        """Check if user has any permission in the given app."""
        if not self.is_active:
            return False

        if self.is_superuser:
            return True

        all_perms = await self.get_all_permissions()
        return any(p.startswith(f"{app_label}.") for p in all_perms)


class User(AbstractUser, PermissionsMixin):
    """
    Default User model.
    Combine AbstractUser with PermissionsMixin.
    """

    class Meta:
        table = "auth_user"
        ordering = ["-date_joined"]

    class Admin:
        list_display = ["username", "email", "first_name", "last_name", "is_staff"]
        list_filter = ["is_staff", "is_superuser", "is_active"]
        search_fields = ["username", "email", "first_name", "last_name"]
        ordering = ["-date_joined"]
        fieldsets = [
            (None, {"fields": ["username", "password"]}),
            ("Personal info", {"fields": ["first_name", "last_name", "email"]}),
            (
                "Permissions",
                {
                    "fields": [
                        "is_active",
                        "is_staff",
                        "is_superuser",
                        "groups",
                        "user_permissions",
                    ]
                },
            ),
            ("Important dates", {"fields": ["last_login", "date_joined"]}),
        ]

    def __str__(self) -> str:
        return self.username

    @classmethod
    async def create_user(
        cls,
        username: str,
        email: str,
        password: str,
        **extra_fields: Any,
    ) -> User:
        """Create a regular user."""
        from fastdjango.contrib.auth.hashers import make_password

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = cls(
            username=username,
            email=email.lower(),
            password=make_password(password),
            **extra_fields,
        )
        await user.save()
        return user

    @classmethod
    async def create_superuser(
        cls,
        username: str,
        email: str,
        password: str,
        **extra_fields: Any,
    ) -> User:
        """Create a superuser."""
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True

        return await cls.create_user(username, email, password, **extra_fields)


class AnonymousUser:
    """
    Anonymous user class for unauthenticated requests.
    """

    id = None
    pk = None
    username = ""
    email = ""
    is_active = False
    is_staff = False
    is_superuser = False
    is_authenticated = False
    is_anonymous = True

    def __str__(self) -> str:
        return "AnonymousUser"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, AnonymousUser)

    def __hash__(self) -> int:
        return 1

    async def has_perm(self, perm: str) -> bool:
        return False

    async def has_perms(self, perms: list[str]) -> bool:
        return False

    async def has_module_perms(self, app_label: str) -> bool:
        return False

    async def get_all_permissions(self) -> set[str]:
        return set()
