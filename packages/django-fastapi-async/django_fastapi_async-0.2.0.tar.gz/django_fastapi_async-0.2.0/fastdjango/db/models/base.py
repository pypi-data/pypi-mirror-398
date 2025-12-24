"""
FastDjango Model base class.
Wrapper around Tortoise Model with Django-like features.
"""

from __future__ import annotations

from typing import Any, ClassVar, TYPE_CHECKING
from tortoise import Model as TortoiseModel
from tortoise import fields as tortoise_fields
from pydantic import BaseModel

from fastdjango.db.manager import Manager
from fastdjango.core.signals import pre_save, post_save, pre_delete, post_delete

if TYPE_CHECKING:
    from fastdjango.db.queryset import QuerySet


class ModelMeta:
    """
    Model metadata container.
    Similar to Django's Model._meta
    """

    def __init__(self, model: type[Model], meta: type | None = None):
        self.model = model
        self.model_name = model.__name__.lower()
        self.verbose_name = getattr(meta, "verbose_name", model.__name__)
        self.verbose_name_plural = getattr(
            meta, "verbose_name_plural", f"{self.verbose_name}s"
        )
        self.db_table = getattr(meta, "table", None) or getattr(
            meta, "db_table", self.model_name
        )
        self.ordering = getattr(meta, "ordering", [])
        self.unique_together = getattr(meta, "unique_together", [])
        self.indexes = getattr(meta, "indexes", [])
        self.abstract = getattr(meta, "abstract", False)
        self.app_label = getattr(meta, "app_label", None)
        self.permissions = getattr(meta, "permissions", [])

        # Field introspection
        self._fields: dict[str, Any] = {}
        self._field_names: list[str] = []
        self._pk_field: str | None = None

    def get_fields(self) -> list[Any]:
        """Get all field objects."""
        return list(self._fields.values())

    def get_field(self, name: str) -> Any:
        """Get a field by name."""
        return self._fields.get(name)

    @property
    def pk(self) -> str:
        """Get primary key field name."""
        return self._pk_field or "id"


class Model(TortoiseModel):
    """
    FastDjango Model base class.

    Usage:
        class Post(Model):
            title = fields.CharField(max_length=200)
            content = fields.TextField()
            created_at = fields.DateTimeField(auto_now_add=True)

            class Meta:
                table = "posts"
                ordering = ["-created_at"]

            class Admin:
                list_display = ["title", "created_at"]
                search_fields = ["title", "content"]
    """

    # Class-level attributes
    objects: ClassVar[Manager] = Manager()
    _meta: ClassVar[ModelMeta]
    _admin: ClassVar[type | None] = None

    class Meta:
        abstract = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Skip for abstract models
        meta = getattr(cls, "Meta", None)
        if meta and getattr(meta, "abstract", False):
            return

        # Create manager
        cls.objects = Manager(cls)

        # Create meta
        cls._meta = ModelMeta(cls, meta)

        # Register admin config
        if hasattr(cls, "Admin"):
            cls._admin = cls.Admin

        # Introspect fields
        for name, field in cls._meta.fields_map.items() if hasattr(cls, "_meta") else []:
            cls._meta._fields[name] = field
            cls._meta._field_names.append(name)
            if getattr(field, "pk", False):
                cls._meta._pk_field = name

    @classmethod
    def _get_pk_field_name(cls) -> str:
        """Get the primary key field name."""
        if hasattr(cls, "_meta") and hasattr(cls._meta, "pk_attr"):
            return cls._meta.pk_attr
        return "id"

    @property
    def pk(self) -> Any:
        """Get primary key value."""
        pk_field = self._get_pk_field_name()
        return getattr(self, pk_field, None)

    @pk.setter
    def pk(self, value: Any) -> None:
        """Set primary key value."""
        pk_field = self._get_pk_field_name()
        setattr(self, pk_field, value)

    async def save(
        self,
        using_db: Any = None,
        update_fields: list[str] | None = None,
        force_create: bool = False,
        force_update: bool = False,
    ) -> None:
        """
        Save the model instance.

        Triggers pre_save and post_save signals.
        """
        created = self.pk is None

        # Send pre_save signal
        await pre_save.send(
            sender=self.__class__,
            instance=self,
            raw=False,
            using=using_db,
            update_fields=update_fields,
        )

        # Call parent save
        await super().save(
            using_db=using_db,
            update_fields=update_fields,
            force_create=force_create,
            force_update=force_update,
        )

        # Send post_save signal
        await post_save.send(
            sender=self.__class__,
            instance=self,
            created=created,
            raw=False,
            using=using_db,
            update_fields=update_fields,
        )

    async def delete(self, using_db: Any = None) -> None:
        """
        Delete the model instance.

        Triggers pre_delete and post_delete signals.
        """
        # Send pre_delete signal
        await pre_delete.send(
            sender=self.__class__,
            instance=self,
            using=using_db,
        )

        # Call parent delete
        await super().delete(using_db=using_db)

        # Send post_delete signal
        await post_delete.send(
            sender=self.__class__,
            instance=self,
            using=using_db,
        )

    async def refresh_from_db(self, fields: list[str] | None = None) -> None:
        """Reload the instance from the database."""
        await self.refresh_from_db(fields=fields)

    def to_dict(self, exclude: list[str] | None = None) -> dict[str, Any]:
        """Convert model to dictionary."""
        exclude = exclude or []
        result = {}
        for field_name in self._meta.fields_map:
            if field_name not in exclude:
                value = getattr(self, field_name, None)
                result[field_name] = value
        return result

    def to_pydantic(self) -> BaseModel:
        """Convert model to Pydantic model."""
        from fastdjango.forms.schemas import model_to_pydantic

        schema_class = model_to_pydantic(self.__class__)
        return schema_class.model_validate(self.to_dict())

    @classmethod
    async def get_or_404(cls, **kwargs: Any) -> Model:
        """Get instance or raise Http404."""
        from fastdjango.core.exceptions import Http404

        instance = await cls.get_or_none(**kwargs)
        if instance is None:
            raise Http404(f"{cls.__name__} not found")
        return instance

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(pk={self.pk})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self}>"
