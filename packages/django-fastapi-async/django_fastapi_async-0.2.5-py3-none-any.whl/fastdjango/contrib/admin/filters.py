"""
FastDjango Admin Filters.
Filter classes for admin list views.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, date
from typing import Any, TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from fastapi import Request


class ListFilter(ABC):
    """
    Base class for admin list filters.

    Usage:
        class StatusFilter(ListFilter):
            title = "Status"
            parameter_name = "status"

            def lookups(self, request, model_admin):
                return [
                    ("published", "Published"),
                    ("draft", "Draft"),
                ]

            def queryset(self, request, queryset):
                if self.value() == "published":
                    return queryset.filter(status="published")
                elif self.value() == "draft":
                    return queryset.filter(status="draft")
                return queryset
    """

    title: str = ""
    parameter_name: str = ""

    def __init__(self, request: Request, params: dict, model: type, model_admin: Any):
        self.request = request
        self.params = params
        self.model = model
        self.model_admin = model_admin
        self._value = params.get(self.parameter_name)

    def value(self) -> str | None:
        """Return the filter value from query params."""
        return self._value

    @abstractmethod
    def lookups(self, request: Request, model_admin: Any) -> list[tuple[str, str]]:
        """
        Return a list of tuples (value, display_name) for filter options.
        """
        pass

    @abstractmethod
    def queryset(self, request: Request, queryset: Any) -> Any:
        """
        Filter the queryset based on self.value().
        """
        pass

    def choices(self) -> list[dict[str, Any]]:
        """Return choices for template rendering."""
        yield {
            "selected": self.value() is None,
            "query_string": self._get_query_string(remove=[self.parameter_name]),
            "display": "All",
        }
        for lookup, title in self.lookups(self.request, self.model_admin):
            yield {
                "selected": str(lookup) == self.value(),
                "query_string": self._get_query_string({self.parameter_name: lookup}),
                "display": title,
            }

    def _get_query_string(
        self, new_params: dict | None = None, remove: list | None = None
    ) -> str:
        """Build query string with updated params."""
        params = self.params.copy()
        if new_params:
            params.update(new_params)
        if remove:
            for key in remove:
                params.pop(key, None)
        return "&".join(f"{k}={v}" for k, v in params.items())


class SimpleListFilter(ListFilter):
    """Simple list filter that doesn't require model field."""
    pass


class FieldListFilter(ListFilter):
    """Filter based on a model field."""

    field_name: str = ""

    def __init__(self, field: Any, request: Request, params: dict, model: type, model_admin: Any):
        self.field = field
        self.field_name = field.model_field_name
        super().__init__(request, params, model, model_admin)
        self.parameter_name = self.field_name


class BooleanFieldListFilter(FieldListFilter):
    """Filter for boolean fields."""

    def lookups(self, request: Request, model_admin: Any) -> list[tuple[str, str]]:
        return [
            ("1", "Yes"),
            ("0", "No"),
        ]

    def queryset(self, request: Request, queryset: Any) -> Any:
        if self.value() == "1":
            return queryset.filter(**{self.field_name: True})
        elif self.value() == "0":
            return queryset.filter(**{self.field_name: False})
        return queryset


class ChoicesFieldListFilter(FieldListFilter):
    """Filter for fields with choices."""

    def lookups(self, request: Request, model_admin: Any) -> list[tuple[str, str]]:
        choices = getattr(self.field, "choices", None) or []
        return [(str(k), str(v)) for k, v in choices]

    def queryset(self, request: Request, queryset: Any) -> Any:
        if self.value():
            return queryset.filter(**{self.field_name: self.value()})
        return queryset


class DateFieldListFilter(FieldListFilter):
    """Filter for date/datetime fields."""

    def lookups(self, request: Request, model_admin: Any) -> list[tuple[str, str]]:
        return [
            ("today", "Today"),
            ("past_7_days", "Past 7 days"),
            ("this_month", "This month"),
            ("this_year", "This year"),
        ]

    def queryset(self, request: Request, queryset: Any) -> Any:
        today = date.today()
        value = self.value()

        if value == "today":
            return queryset.filter(**{
                f"{self.field_name}__gte": today,
                f"{self.field_name}__lt": today + timedelta(days=1),
            })
        elif value == "past_7_days":
            return queryset.filter(**{
                f"{self.field_name}__gte": today - timedelta(days=7),
            })
        elif value == "this_month":
            return queryset.filter(**{
                f"{self.field_name}__year": today.year,
                f"{self.field_name}__month": today.month,
            })
        elif value == "this_year":
            return queryset.filter(**{
                f"{self.field_name}__year": today.year,
            })
        return queryset


class AllValuesFieldListFilter(FieldListFilter):
    """Filter showing all distinct values for a field."""

    def lookups(self, request: Request, model_admin: Any) -> list[tuple[str, str]]:
        # This would need async handling in real implementation
        return []

    def queryset(self, request: Request, queryset: Any) -> Any:
        if self.value():
            return queryset.filter(**{self.field_name: self.value()})
        return queryset


class RelatedFieldListFilter(FieldListFilter):
    """Filter for ForeignKey/related fields."""

    def lookups(self, request: Request, model_admin: Any) -> list[tuple[str, str]]:
        # Would need to fetch related objects
        return []

    def queryset(self, request: Request, queryset: Any) -> Any:
        if self.value():
            return queryset.filter(**{f"{self.field_name}_id": self.value()})
        return queryset


class EmptyFieldListFilter(FieldListFilter):
    """Filter for empty/non-empty values."""

    def lookups(self, request: Request, model_admin: Any) -> list[tuple[str, str]]:
        return [
            ("1", "Empty"),
            ("0", "Not empty"),
        ]

    def queryset(self, request: Request, queryset: Any) -> Any:
        if self.value() == "1":
            return queryset.filter(**{f"{self.field_name}__isnull": True})
        elif self.value() == "0":
            return queryset.filter(**{f"{self.field_name}__isnull": False})
        return queryset


# Filter registry
FILTER_FOR_FIELD_TYPES = {
    "BooleanField": BooleanFieldListFilter,
    "DateField": DateFieldListFilter,
    "DatetimeField": DateFieldListFilter,
    "CharField": AllValuesFieldListFilter,
    "ForeignKeyField": RelatedFieldListFilter,
}


def get_filter_for_field(field: Any) -> type[FieldListFilter] | None:
    """Get appropriate filter class for a field type."""
    field_type = field.__class__.__name__
    return FILTER_FOR_FIELD_TYPES.get(field_type)


__all__ = [
    "ListFilter",
    "SimpleListFilter",
    "FieldListFilter",
    "BooleanFieldListFilter",
    "ChoicesFieldListFilter",
    "DateFieldListFilter",
    "AllValuesFieldListFilter",
    "RelatedFieldListFilter",
    "EmptyFieldListFilter",
    "get_filter_for_field",
]
