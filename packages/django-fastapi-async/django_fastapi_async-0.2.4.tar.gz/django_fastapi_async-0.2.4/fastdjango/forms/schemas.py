"""
FastDjango Schema generation.
Convert models to Pydantic schemas automatically.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING
from pydantic import BaseModel, create_model

if TYPE_CHECKING:
    from fastdjango.db.models import Model


def model_to_pydantic(
    model: type[Model],
    *,
    name: str | None = None,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    optional: list[str] | None = None,
) -> type[BaseModel]:
    """
    Generate a Pydantic model from a FastDjango model.

    Usage:
        # Basic usage
        PostSchema = model_to_pydantic(Post)

        # With options
        PostCreate = model_to_pydantic(
            Post,
            name="PostCreate",
            exclude=["id", "created_at"],
            optional=["published"],
        )
    """
    name = name or f"{model.__name__}Schema"
    include = include or []
    exclude = exclude or []
    optional = optional or []

    field_definitions: dict[str, tuple] = {}
    model_fields = getattr(model._meta, "fields_map", {})

    for field_name, field in model_fields.items():
        # Filter fields
        if include and field_name not in include:
            continue
        if field_name in exclude:
            continue

        # Get Python type
        python_type = _get_python_type(field)
        if python_type is None:
            continue

        # Make optional if specified
        is_optional = field_name in optional or getattr(field, "null", False)
        if is_optional:
            python_type = python_type | None
            field_definitions[field_name] = (python_type, None)
        else:
            default = getattr(field, "default", ...)
            if default is None:
                default = ...
            field_definitions[field_name] = (python_type, default)

    return create_model(name, **field_definitions)


def _get_python_type(field: Any) -> type | None:
    """Map a model field to a Python type."""
    field_class_name = field.__class__.__name__

    type_mapping = {
        "IntField": int,
        "BigIntField": int,
        "SmallIntField": int,
        "CharField": str,
        "TextField": str,
        "BooleanField": bool,
        "FloatField": float,
        "DecimalField": float,
        "DateField": str,
        "DatetimeField": str,
        "TimeField": str,
        "JSONField": dict,
        "UUIDField": str,
        "BinaryField": bytes,
    }

    return type_mapping.get(field_class_name)


class SchemaGenerator:
    """
    Generate multiple schemas for a model.

    Usage:
        gen = SchemaGenerator(Post)
        PostSchema = gen.schema()           # All fields, for reading
        PostCreate = gen.create_schema()    # Without id, timestamps
        PostUpdate = gen.update_schema()    # All fields optional
    """

    def __init__(self, model: type[Model]):
        self.model = model

    def schema(self, name: str | None = None) -> type[BaseModel]:
        """Generate read schema with all fields."""
        return model_to_pydantic(self.model, name=name)

    def create_schema(self, name: str | None = None) -> type[BaseModel]:
        """Generate create schema without auto fields."""
        name = name or f"{self.model.__name__}Create"
        return model_to_pydantic(
            self.model,
            name=name,
            exclude=["id", "pk", "created_at", "updated_at"],
        )

    def update_schema(self, name: str | None = None) -> type[BaseModel]:
        """Generate update schema with all fields optional."""
        name = name or f"{self.model.__name__}Update"
        model_fields = getattr(self.model._meta, "fields_map", {})
        optional_fields = [
            f for f in model_fields.keys()
            if f not in ["id", "pk", "created_at", "updated_at"]
        ]
        return model_to_pydantic(
            self.model,
            name=name,
            exclude=["id", "pk", "created_at", "updated_at"],
            optional=optional_fields,
        )

    def list_schema(self, name: str | None = None) -> type[BaseModel]:
        """Generate list schema for pagination."""
        name = name or f"{self.model.__name__}List"
        item_schema = self.schema()

        return create_model(
            name,
            items=(list[item_schema], ...),  # type: ignore
            total=(int, ...),
            page=(int, 1),
            per_page=(int, 25),
        )
