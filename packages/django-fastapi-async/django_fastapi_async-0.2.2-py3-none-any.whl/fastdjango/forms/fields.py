"""
FastDjango Form Fields.
"""

from __future__ import annotations

from typing import Any, Callable
from pydantic import Field, EmailStr, HttpUrl
from pydantic.fields import FieldInfo


class FormField:
    """Base form field with widget info."""

    widget: str = "text"
    field_type: type = str

    def __init__(
        self,
        *,
        required: bool = True,
        default: Any = ...,
        label: str | None = None,
        help_text: str = "",
        widget: str | None = None,
        validators: list[Callable] | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        choices: list[tuple[str, str]] | None = None,
        **kwargs: Any,
    ):
        self.required = required
        self.default = None if not required else default
        self.label = label
        self.help_text = help_text
        self.widget = widget or self.__class__.widget
        self.validators = validators or []
        self.min_length = min_length
        self.max_length = max_length
        self.min_value = min_value
        self.max_value = max_value
        self.choices = choices
        self.extra = kwargs

    def to_pydantic_field(self) -> FieldInfo:
        """Convert to Pydantic FieldInfo."""
        kwargs: dict[str, Any] = {
            "description": self.help_text,
            "title": self.label,
        }

        if self.default is not ...:
            kwargs["default"] = self.default
        elif not self.required:
            kwargs["default"] = None

        if self.min_length is not None:
            kwargs["min_length"] = self.min_length
        if self.max_length is not None:
            kwargs["max_length"] = self.max_length
        if self.min_value is not None:
            kwargs["ge"] = self.min_value
        if self.max_value is not None:
            kwargs["le"] = self.max_value

        return Field(**kwargs)

    def get_type(self) -> type:
        """Get the Python type for this field."""
        if not self.required:
            return self.field_type | None
        return self.field_type

    def render(self, name: str, value: Any = None, attrs: dict | None = None) -> str:
        """Render the field as HTML."""
        attrs = attrs or {}
        attrs_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        value_str = f'value="{value}"' if value is not None else ""

        if self.widget == "textarea":
            return f'<textarea name="{name}" {attrs_str}>{value or ""}</textarea>'
        elif self.widget == "select":
            options = "".join(
                f'<option value="{v}" {"selected" if v == value else ""}>{label}</option>'
                for v, label in (self.choices or [])
            )
            return f'<select name="{name}" {attrs_str}>{options}</select>'
        elif self.widget == "checkbox":
            checked = "checked" if value else ""
            return f'<input type="checkbox" name="{name}" {checked} {attrs_str}>'
        else:
            return f'<input type="{self.widget}" name="{name}" {value_str} {attrs_str}>'


class CharField(FormField):
    """Text input field."""

    widget = "text"
    field_type = str


class TextareaField(FormField):
    """Textarea field."""

    widget = "textarea"
    field_type = str


class PasswordField(FormField):
    """Password input field."""

    widget = "password"
    field_type = str


class HiddenField(FormField):
    """Hidden input field."""

    widget = "hidden"
    field_type = str


class IntegerField(FormField):
    """Integer input field."""

    widget = "number"
    field_type = int


class FloatField(FormField):
    """Float input field."""

    widget = "number"
    field_type = float


class BooleanField(FormField):
    """Boolean checkbox field."""

    widget = "checkbox"
    field_type = bool

    def __init__(self, required: bool = False, **kwargs):
        super().__init__(required=required, **kwargs)


class EmailField(FormField):
    """Email input field."""

    widget = "email"
    field_type = str  # Will use EmailStr in pydantic


class URLField(FormField):
    """URL input field."""

    widget = "url"
    field_type = str


class DateField(FormField):
    """Date input field."""

    widget = "date"
    field_type = str


class DateTimeField(FormField):
    """DateTime input field."""

    widget = "datetime-local"
    field_type = str


class ChoiceField(FormField):
    """Select field with choices."""

    widget = "select"
    field_type = str

    def __init__(self, choices: list[tuple[str, str]], **kwargs):
        super().__init__(choices=choices, **kwargs)


class MultipleChoiceField(FormField):
    """Multiple select field."""

    widget = "select"
    field_type = list

    def __init__(self, choices: list[tuple[str, str]], **kwargs):
        super().__init__(choices=choices, **kwargs)

    def render(self, name: str, value: Any = None, attrs: dict | None = None) -> str:
        attrs = attrs or {}
        attrs["multiple"] = "multiple"
        return super().render(name, value, attrs)


class FileField(FormField):
    """File upload field."""

    widget = "file"
    field_type = bytes


class ImageField(FileField):
    """Image upload field."""

    widget = "file"

    def render(self, name: str, value: Any = None, attrs: dict | None = None) -> str:
        attrs = attrs or {}
        attrs["accept"] = "image/*"
        return super().render(name, value, attrs)
