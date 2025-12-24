"""
FastDjango Model Manager.
Provides Django-like objects manager interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, Generic

if TYPE_CHECKING:
    from fastdjango.db.models import Model
    from fastdjango.db.queryset import QuerySet

T = TypeVar("T", bound="Model")


class Manager(Generic[T]):
    """
    Manager provides the interface for database query operations.
    Similar to Django's Manager class.

    Usage:
        class MyModel(Model):
            pass

        # Automatically available:
        await MyModel.objects.all()
        await MyModel.objects.filter(name="test")
        await MyModel.objects.get(id=1)
    """

    def __init__(self, model: type[T] | None = None):
        self.model: type[T] | None = model

    def __get__(self, instance: T | None, owner: type[T]) -> Manager[T]:
        """Descriptor to bind manager to model class."""
        if self.model is None:
            self.model = owner
        return self

    def _get_queryset(self) -> QuerySet[T]:
        """Get a new QuerySet for this manager's model."""
        from fastdjango.db.queryset import QuerySet

        if self.model is None:
            raise ValueError("Manager is not bound to a model")
        return QuerySet(self.model)

    def all(self) -> QuerySet[T]:
        """Return all objects."""
        return self._get_queryset()

    def filter(self, *args: Any, **kwargs: Any) -> QuerySet[T]:
        """Filter objects by given criteria."""
        return self._get_queryset().filter(*args, **kwargs)

    def exclude(self, *args: Any, **kwargs: Any) -> QuerySet[T]:
        """Exclude objects by given criteria."""
        return self._get_queryset().exclude(*args, **kwargs)

    def order_by(self, *fields: str) -> QuerySet[T]:
        """Order objects by given fields."""
        return self._get_queryset().order_by(*fields)

    def select_related(self, *fields: str) -> QuerySet[T]:
        """Select related objects (JOIN)."""
        return self._get_queryset().select_related(*fields)

    def prefetch_related(self, *fields: str) -> QuerySet[T]:
        """Prefetch related objects (separate queries)."""
        return self._get_queryset().prefetch_related(*fields)

    def only(self, *fields: str) -> QuerySet[T]:
        """Load only specified fields."""
        return self._get_queryset().only(*fields)

    def defer(self, *fields: str) -> QuerySet[T]:
        """Defer loading of specified fields."""
        return self._get_queryset().defer(*fields)

    def annotate(self, **kwargs: Any) -> QuerySet[T]:
        """Add annotations to objects."""
        return self._get_queryset().annotate(**kwargs)

    def values(self, *fields: str) -> QuerySet[T]:
        """Return dictionaries instead of model instances."""
        return self._get_queryset().values(*fields)

    def values_list(self, *fields: str, flat: bool = False) -> QuerySet[T]:
        """Return tuples instead of model instances."""
        return self._get_queryset().values_list(*fields, flat=flat)

    def distinct(self) -> QuerySet[T]:
        """Return distinct objects."""
        return self._get_queryset().distinct()

    async def get(self, **kwargs: Any) -> T:
        """Get a single object matching criteria."""
        return await self._get_queryset().get(**kwargs)

    async def get_or_none(self, **kwargs: Any) -> T | None:
        """Get a single object or None if not found."""
        return await self._get_queryset().get_or_none(**kwargs)

    async def get_or_404(self, **kwargs: Any) -> T:
        """Get a single object or raise Http404."""
        from fastdjango.core.exceptions import Http404

        obj = await self.get_or_none(**kwargs)
        if obj is None:
            model_name = self.model.__name__ if self.model else "Object"
            raise Http404(f"{model_name} not found")
        return obj

    async def first(self) -> T | None:
        """Get the first object."""
        return await self._get_queryset().first()

    async def last(self) -> T | None:
        """Get the last object."""
        return await self._get_queryset().last()

    async def count(self) -> int:
        """Count objects."""
        return await self._get_queryset().count()

    async def exists(self) -> bool:
        """Check if any objects exist."""
        return await self._get_queryset().exists()

    async def create(self, **kwargs: Any) -> T:
        """Create and save a new object."""
        if self.model is None:
            raise ValueError("Manager is not bound to a model")
        return await self.model.create(**kwargs)

    async def get_or_create(
        self,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[T, bool]:
        """Get an object or create it if it doesn't exist."""
        if self.model is None:
            raise ValueError("Manager is not bound to a model")

        obj = await self.get_or_none(**kwargs)
        if obj is not None:
            return obj, False

        create_kwargs = {**kwargs, **(defaults or {})}
        obj = await self.create(**create_kwargs)
        return obj, True

    async def update_or_create(
        self,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[T, bool]:
        """Update an object or create it if it doesn't exist."""
        obj = await self.get_or_none(**kwargs)

        if obj is not None:
            for key, value in (defaults or {}).items():
                setattr(obj, key, value)
            await obj.save()
            return obj, False

        create_kwargs = {**kwargs, **(defaults or {})}
        obj = await self.create(**create_kwargs)
        return obj, True

    async def bulk_create(self, objs: list[T], batch_size: int | None = None) -> list[T]:
        """Create multiple objects in bulk."""
        if self.model is None:
            raise ValueError("Manager is not bound to a model")
        return await self.model.bulk_create(objs, batch_size=batch_size)

    async def bulk_update(
        self,
        objs: list[T],
        fields: list[str],
        batch_size: int | None = None,
    ) -> int:
        """Update multiple objects in bulk."""
        if self.model is None:
            raise ValueError("Manager is not bound to a model")

        count = 0
        for obj in objs:
            update_data = {field: getattr(obj, field) for field in fields}
            await self.filter(pk=obj.pk).update(**update_data)
            count += 1
        return count

    async def in_bulk(
        self,
        id_list: list[Any] | None = None,
        field_name: str = "pk",
    ) -> dict[Any, T]:
        """Return a dict mapping IDs to objects."""
        if id_list is None:
            return {}

        objs = await self.filter(**{f"{field_name}__in": id_list})
        return {getattr(obj, field_name): obj for obj in objs}

    def raw(self, query: str, params: list | tuple | None = None) -> QuerySet[T]:
        """Execute raw SQL query."""
        return self._get_queryset().raw(query, params)

    def __aiter__(self):
        """Allow async iteration over all objects."""
        return self._get_queryset().__aiter__()
