"""
FastDjango model fields.
Wrapper around Tortoise fields with Django-like API.
"""

from __future__ import annotations

from typing import Any, TypeVar, Generic, TYPE_CHECKING
from tortoise import fields as tortoise_fields

if TYPE_CHECKING:
    from fastdjango.db.models import Model


T = TypeVar("T")


# Re-export Tortoise fields with Django-like names
class Field(Generic[T]):
    """Base field class."""

    def __init__(
        self,
        *,
        null: bool = False,
        blank: bool = False,
        default: T | None = None,
        primary_key: bool = False,
        unique: bool = False,
        index: bool = False,
        db_column: str | None = None,
        db_index: bool = False,
        validators: list | None = None,
        verbose_name: str | None = None,
        help_text: str = "",
        editable: bool = True,
        **kwargs: Any,
    ):
        self.null = null
        self.blank = blank
        self.default = default
        self.primary_key = primary_key
        self.unique = unique
        self.index = index or db_index
        self.db_column = db_column
        self.validators = validators or []
        self.verbose_name = verbose_name
        self.help_text = help_text
        self.editable = editable
        self.extra_kwargs = kwargs


# Integer fields
class IntegerField(tortoise_fields.IntField):
    """Integer field."""

    def __init__(
        self,
        *,
        null: bool = False,
        default: int | None = None,
        primary_key: bool = False,
        unique: bool = False,
        index: bool = False,
        verbose_name: str | None = None,
        help_text: str = "",
        **kwargs: Any,
    ):
        super().__init__(
            null=null,
            default=default,
            pk=primary_key,
            unique=unique,
            index=index,
            description=verbose_name,
            **kwargs,
        )


class BigIntegerField(tortoise_fields.BigIntField):
    """Big integer field (64-bit)."""

    def __init__(
        self,
        *,
        null: bool = False,
        default: int | None = None,
        unique: bool = False,
        index: bool = False,
        verbose_name: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            null=null,
            default=default,
            unique=unique,
            index=index,
            description=verbose_name,
            **kwargs,
        )


class SmallIntegerField(tortoise_fields.SmallIntField):
    """Small integer field (16-bit)."""

    def __init__(
        self,
        *,
        null: bool = False,
        default: int | None = None,
        unique: bool = False,
        index: bool = False,
        verbose_name: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            null=null,
            default=default,
            unique=unique,
            index=index,
            description=verbose_name,
            **kwargs,
        )


class PositiveIntegerField(tortoise_fields.IntField):
    """Positive integer field."""

    def __init__(self, **kwargs: Any):
        # Tortoise doesn't have positive-only constraint, handled at validation
        super().__init__(**kwargs)


class AutoField(tortoise_fields.IntField):
    """Auto-incrementing primary key field."""

    def __init__(self, primary_key: bool = True, **kwargs: Any):
        super().__init__(pk=primary_key, generated=True, **kwargs)


class BigAutoField(tortoise_fields.BigIntField):
    """Big auto-incrementing primary key field."""

    def __init__(self, primary_key: bool = True, **kwargs: Any):
        super().__init__(pk=primary_key, generated=True, **kwargs)


# String fields
class CharField(tortoise_fields.CharField):
    """Character field with max length."""

    def __init__(
        self,
        max_length: int,
        *,
        null: bool = False,
        blank: bool = False,
        default: str | None = None,
        unique: bool = False,
        index: bool = False,
        verbose_name: str | None = None,
        help_text: str = "",
        choices: list[tuple[str, str]] | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            max_length=max_length,
            null=null,
            default=default if default is not None else ("" if blank else None),
            unique=unique,
            index=index,
            description=verbose_name,
            **kwargs,
        )
        self.blank = blank
        self.help_text = help_text
        self.choices = choices


class TextField(tortoise_fields.TextField):
    """Text field for long content."""

    def __init__(
        self,
        *,
        null: bool = False,
        blank: bool = False,
        default: str | None = None,
        verbose_name: str | None = None,
        help_text: str = "",
        **kwargs: Any,
    ):
        super().__init__(
            null=null,
            default=default if default is not None else ("" if blank else None),
            description=verbose_name,
            **kwargs,
        )
        self.blank = blank
        self.help_text = help_text


class SlugField(tortoise_fields.CharField):
    """Slug field for URL-friendly strings."""

    def __init__(
        self,
        max_length: int = 50,
        *,
        null: bool = False,
        blank: bool = False,
        default: str | None = None,
        unique: bool = False,
        index: bool = True,
        verbose_name: str | None = None,
        allow_unicode: bool = False,
        **kwargs: Any,
    ):
        super().__init__(
            max_length=max_length,
            null=null,
            default=default,
            unique=unique,
            index=index,
            description=verbose_name,
            **kwargs,
        )
        self.allow_unicode = allow_unicode


class EmailField(tortoise_fields.CharField):
    """Email field."""

    def __init__(
        self,
        max_length: int = 254,
        *,
        null: bool = False,
        blank: bool = False,
        default: str | None = None,
        unique: bool = False,
        verbose_name: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            max_length=max_length,
            null=null,
            default=default,
            unique=unique,
            description=verbose_name,
            **kwargs,
        )


class URLField(tortoise_fields.CharField):
    """URL field."""

    def __init__(
        self,
        max_length: int = 200,
        *,
        null: bool = False,
        blank: bool = False,
        default: str | None = None,
        verbose_name: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            max_length=max_length,
            null=null,
            default=default,
            description=verbose_name,
            **kwargs,
        )


class UUIDField(tortoise_fields.UUIDField):
    """UUID field."""

    def __init__(
        self,
        *,
        null: bool = False,
        default: Any = None,
        primary_key: bool = False,
        unique: bool = False,
        verbose_name: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            null=null,
            default=default,
            pk=primary_key,
            unique=unique,
            description=verbose_name,
            **kwargs,
        )


# Boolean field
class BooleanField(tortoise_fields.BooleanField):
    """Boolean field."""

    def __init__(
        self,
        *,
        null: bool = False,
        default: bool | None = None,
        verbose_name: str | None = None,
        help_text: str = "",
        **kwargs: Any,
    ):
        super().__init__(
            null=null,
            default=default,
            description=verbose_name,
            **kwargs,
        )
        self.help_text = help_text


# Date/Time fields
class DateField(tortoise_fields.DateField):
    """Date field."""

    def __init__(
        self,
        *,
        null: bool = False,
        default: Any = None,
        auto_now: bool = False,
        auto_now_add: bool = False,
        verbose_name: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            null=null,
            default=default,
            auto_now=auto_now,
            auto_now_add=auto_now_add,
            description=verbose_name,
            **kwargs,
        )


class DateTimeField(tortoise_fields.DatetimeField):
    """DateTime field."""

    def __init__(
        self,
        *,
        null: bool = False,
        default: Any = None,
        auto_now: bool = False,
        auto_now_add: bool = False,
        verbose_name: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            null=null,
            default=default,
            auto_now=auto_now,
            auto_now_add=auto_now_add,
            description=verbose_name,
            **kwargs,
        )


class TimeField(tortoise_fields.TimeField):
    """Time field."""

    def __init__(
        self,
        *,
        null: bool = False,
        default: Any = None,
        auto_now: bool = False,
        auto_now_add: bool = False,
        verbose_name: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            null=null,
            default=default,
            description=verbose_name,
            **kwargs,
        )


# Numeric fields
class DecimalField(tortoise_fields.DecimalField):
    """Decimal field."""

    def __init__(
        self,
        max_digits: int,
        decimal_places: int,
        *,
        null: bool = False,
        default: Any = None,
        verbose_name: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            max_digits=max_digits,
            decimal_places=decimal_places,
            null=null,
            default=default,
            description=verbose_name,
            **kwargs,
        )


class FloatField(tortoise_fields.FloatField):
    """Float field."""

    def __init__(
        self,
        *,
        null: bool = False,
        default: float | None = None,
        verbose_name: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            null=null,
            default=default,
            description=verbose_name,
            **kwargs,
        )


# Binary field
class BinaryField(tortoise_fields.BinaryField):
    """Binary field."""

    def __init__(
        self,
        *,
        null: bool = False,
        default: bytes | None = None,
        verbose_name: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            null=null,
            default=default,
            description=verbose_name,
            **kwargs,
        )


# JSON field
class JSONField(tortoise_fields.JSONField):
    """JSON field."""

    def __init__(
        self,
        *,
        null: bool = False,
        default: Any = None,
        verbose_name: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            null=null,
            default=default,
            description=verbose_name,
            **kwargs,
        )


# Relationship fields (these are functions in Tortoise, not classes)
def ForeignKey(
    to: str,
    *,
    related_name: str | None = None,
    on_delete: str = "CASCADE",
    null: bool = False,
    verbose_name: str | None = None,
    **kwargs: Any,
):
    """Foreign key relationship."""
    return tortoise_fields.ForeignKeyField(
        model_name=to,
        related_name=related_name,
        on_delete=on_delete,
        null=null,
        description=verbose_name,
        **kwargs,
    )


def OneToOneField(
    to: str,
    *,
    related_name: str | None = None,
    on_delete: str = "CASCADE",
    null: bool = False,
    verbose_name: str | None = None,
    **kwargs: Any,
):
    """One-to-one relationship."""
    return tortoise_fields.OneToOneField(
        model_name=to,
        related_name=related_name,
        on_delete=on_delete,
        null=null,
        description=verbose_name,
        **kwargs,
    )


def ManyToManyField(
    to: str,
    *,
    related_name: str | None = None,
    through: str | None = None,
    verbose_name: str | None = None,
    **kwargs: Any,
):
    """Many-to-many relationship."""
    return tortoise_fields.ManyToManyField(
        model_name=to,
        related_name=related_name,
        through=through,
        description=verbose_name,
        **kwargs,
    )


# Aliases for Django compatibility
IntField = IntegerField
BigIntField = BigIntegerField
SmallIntField = SmallIntegerField
ForeignKeyField = ForeignKey
OneToOneRel = OneToOneField
ManyToManyRel = ManyToManyField
