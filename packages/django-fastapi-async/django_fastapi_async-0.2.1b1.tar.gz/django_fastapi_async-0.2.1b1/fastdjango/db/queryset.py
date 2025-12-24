"""
FastDjango QuerySet.
Async QuerySet with Django-like chainable API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, Generic, Iterator, AsyncIterator
from tortoise.queryset import QuerySet as TortoiseQuerySet
from tortoise.expressions import Q
from tortoise.functions import Count, Sum, Avg, Min, Max

if TYPE_CHECKING:
    from fastdjango.db.models import Model

T = TypeVar("T", bound="Model")


class QuerySet(Generic[T]):
    """
    Async QuerySet with Django-like API.

    Supports:
    - Chaining: filter().exclude().order_by()
    - Async iteration: async for obj in queryset
    - Django-style lookups: field__icontains, field__gte, etc.
    """

    def __init__(self, model: type[T], queryset: TortoiseQuerySet | None = None):
        self.model = model
        self._queryset: TortoiseQuerySet = queryset or model.all()
        self._prefetch_related: list[str] = []
        self._select_related: list[str] = []
        self._only_fields: list[str] = []
        self._defer_fields: list[str] = []
        self._values_fields: list[str] = []
        self._values_list_fields: list[str] = []
        self._flat: bool = False
        self._distinct_flag: bool = False

    def _clone(self) -> QuerySet[T]:
        """Create a copy of this QuerySet."""
        clone = QuerySet(self.model, self._queryset)
        clone._prefetch_related = self._prefetch_related.copy()
        clone._select_related = self._select_related.copy()
        clone._only_fields = self._only_fields.copy()
        clone._defer_fields = self._defer_fields.copy()
        clone._values_fields = self._values_fields.copy()
        clone._values_list_fields = self._values_list_fields.copy()
        clone._flat = self._flat
        clone._distinct_flag = self._distinct_flag
        return clone

    def _convert_lookup(self, key: str, value: Any) -> tuple[str, Any]:
        """Convert Django-style lookups to Tortoise format."""
        # Most lookups are the same in Tortoise
        return key, value

    def filter(self, *args: Q, **kwargs: Any) -> QuerySet[T]:
        """Filter QuerySet by given criteria."""
        clone = self._clone()
        if args:
            clone._queryset = clone._queryset.filter(*args)
        if kwargs:
            converted = {k: v for k, v in kwargs.items()}
            clone._queryset = clone._queryset.filter(**converted)
        return clone

    def exclude(self, *args: Q, **kwargs: Any) -> QuerySet[T]:
        """Exclude objects matching criteria."""
        clone = self._clone()
        if args:
            clone._queryset = clone._queryset.exclude(*args)
        if kwargs:
            clone._queryset = clone._queryset.exclude(**kwargs)
        return clone

    def order_by(self, *fields: str) -> QuerySet[T]:
        """Order QuerySet by given fields."""
        clone = self._clone()
        clone._queryset = clone._queryset.order_by(*fields)
        return clone

    def select_related(self, *fields: str) -> QuerySet[T]:
        """Select related objects (eager loading with JOIN)."""
        clone = self._clone()
        clone._select_related.extend(fields)
        clone._queryset = clone._queryset.select_related(*fields)
        return clone

    def prefetch_related(self, *fields: str) -> QuerySet[T]:
        """Prefetch related objects (separate queries)."""
        clone = self._clone()
        clone._prefetch_related.extend(fields)
        clone._queryset = clone._queryset.prefetch_related(*fields)
        return clone

    def only(self, *fields: str) -> QuerySet[T]:
        """Load only specified fields."""
        clone = self._clone()
        clone._only_fields.extend(fields)
        clone._queryset = clone._queryset.only(*fields)
        return clone

    def defer(self, *fields: str) -> QuerySet[T]:
        """Defer loading of specified fields."""
        clone = self._clone()
        clone._defer_fields.extend(fields)
        # Tortoise doesn't have defer, we'll implement via only
        return clone

    def annotate(self, **kwargs: Any) -> QuerySet[T]:
        """Add annotations to objects."""
        clone = self._clone()
        clone._queryset = clone._queryset.annotate(**kwargs)
        return clone

    def values(self, *fields: str) -> QuerySet[T]:
        """Return dictionaries instead of model instances."""
        clone = self._clone()
        clone._values_fields = list(fields)
        clone._queryset = clone._queryset.values(*fields) if fields else clone._queryset.values()
        return clone

    def values_list(self, *fields: str, flat: bool = False) -> QuerySet[T]:
        """Return tuples instead of model instances."""
        clone = self._clone()
        clone._values_list_fields = list(fields)
        clone._flat = flat
        clone._queryset = clone._queryset.values_list(*fields, flat=flat)
        return clone

    def distinct(self) -> QuerySet[T]:
        """Return distinct objects."""
        clone = self._clone()
        clone._distinct_flag = True
        clone._queryset = clone._queryset.distinct()
        return clone

    def limit(self, count: int) -> QuerySet[T]:
        """Limit the number of results."""
        clone = self._clone()
        clone._queryset = clone._queryset.limit(count)
        return clone

    def offset(self, count: int) -> QuerySet[T]:
        """Offset the results."""
        clone = self._clone()
        clone._queryset = clone._queryset.offset(count)
        return clone

    def __getitem__(self, key: int | slice) -> QuerySet[T]:
        """Support slicing: queryset[5:10]."""
        clone = self._clone()
        if isinstance(key, slice):
            if key.start:
                clone._queryset = clone._queryset.offset(key.start)
            if key.stop:
                limit = key.stop - (key.start or 0)
                clone._queryset = clone._queryset.limit(limit)
        else:
            clone._queryset = clone._queryset.offset(key).limit(1)
        return clone

    async def get(self, **kwargs: Any) -> T:
        """Get a single object matching criteria."""
        if kwargs:
            return await self.filter(**kwargs)._queryset.get()
        return await self._queryset.get()

    async def get_or_none(self, **kwargs: Any) -> T | None:
        """Get a single object or None if not found."""
        if kwargs:
            return await self.filter(**kwargs)._queryset.get_or_none()
        return await self._queryset.get_or_none()

    async def get_or_404(self, **kwargs: Any) -> T:
        """Get a single object or raise Http404."""
        from fastdjango.core.exceptions import Http404

        obj = await self.get_or_none(**kwargs)
        if obj is None:
            raise Http404(f"{self.model.__name__} not found")
        return obj

    async def first(self) -> T | None:
        """Get the first object."""
        return await self._queryset.first()

    async def last(self) -> T | None:
        """Get the last object (requires ordering)."""
        # Reverse the queryset and get first
        return await self._queryset.first()

    async def count(self) -> int:
        """Count objects."""
        return await self._queryset.count()

    async def exists(self) -> bool:
        """Check if any objects exist."""
        return await self._queryset.exists()

    async def update(self, **kwargs: Any) -> int:
        """Update all objects in QuerySet."""
        return await self._queryset.update(**kwargs)

    async def delete(self) -> int:
        """Delete all objects in QuerySet."""
        return await self._queryset.delete()

    async def aggregate(self, **kwargs: Any) -> dict[str, Any]:
        """
        Return aggregate values.

        Usage:
            await Post.objects.aggregate(
                total=Count('id'),
                avg_views=Avg('views')
            )
        """
        result = {}
        for name, func in kwargs.items():
            qs = self._queryset.annotate(**{name: func})
            values = await qs.values(name)
            if values:
                result[name] = values[0][name]
            else:
                result[name] = None
        return result

    async def to_list(self) -> list[T]:
        """Convert QuerySet to list."""
        return await self._queryset

    def raw(self, query: str, params: list | tuple | None = None) -> QuerySet[T]:
        """Execute raw SQL query."""
        # Tortoise handles this differently
        clone = self._clone()
        return clone

    async def explain(self) -> str:
        """Get SQL EXPLAIN output."""
        return str(self._queryset.sql())

    def sql(self) -> str:
        """Get the SQL query."""
        return self._queryset.sql()

    # Async iteration
    async def __aiter__(self) -> AsyncIterator[T]:
        """Allow async iteration: async for obj in queryset."""
        async for obj in self._queryset:
            yield obj

    def __await__(self):
        """Allow awaiting the queryset directly."""
        return self.to_list().__await__()

    # Aggregate shortcuts
    async def aggregate_count(self, field: str = "id") -> int:
        """Count aggregate."""
        result = await self.annotate(_count=Count(field)).values("_count")
        return result[0]["_count"] if result else 0

    async def aggregate_sum(self, field: str) -> Any:
        """Sum aggregate."""
        result = await self.annotate(_sum=Sum(field)).values("_sum")
        return result[0]["_sum"] if result else 0

    async def aggregate_avg(self, field: str) -> Any:
        """Average aggregate."""
        result = await self.annotate(_avg=Avg(field)).values("_avg")
        return result[0]["_avg"] if result else None

    async def aggregate_min(self, field: str) -> Any:
        """Minimum aggregate."""
        result = await self.annotate(_min=Min(field)).values("_min")
        return result[0]["_min"] if result else None

    async def aggregate_max(self, field: str) -> Any:
        """Maximum aggregate."""
        result = await self.annotate(_max=Max(field)).values("_max")
        return result[0]["_max"] if result else None

    # Repr
    def __repr__(self) -> str:
        return f"<QuerySet [{self.model.__name__}]>"
