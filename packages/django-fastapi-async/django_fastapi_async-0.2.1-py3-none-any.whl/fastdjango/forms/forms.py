"""
FastDjango Form classes.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING
from pydantic import BaseModel, ValidationError, create_model

from fastdjango.forms.fields import FormField
from fastdjango.core.exceptions import ValidationError as DjangoValidationError

if TYPE_CHECKING:
    from fastdjango.db.models import Model


class FormMetaclass(type):
    """Metaclass for Form classes."""

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        # Collect fields from class attributes
        fields: dict[str, FormField] = {}

        for key, value in list(namespace.items()):
            if isinstance(value, FormField):
                fields[key] = value

        namespace["_declared_fields"] = fields

        return super().__new__(mcs, name, bases, namespace)


class Form(metaclass=FormMetaclass):
    """
    Base form class with Django-like API.

    Usage:
        class LoginForm(Form):
            username = CharField(required=True, max_length=150)
            password = PasswordField(required=True)

        # Validate data
        form = LoginForm(data={"username": "john", "password": "secret"})
        if form.is_valid():
            user = await authenticate(**form.cleaned_data)
        else:
            print(form.errors)

        # Render in template
        {{ form.as_p() }}
    """

    _declared_fields: dict[str, FormField]

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        initial: dict[str, Any] | None = None,
        instance: Any = None,
    ):
        self.data = data or {}
        self.initial = initial or {}
        self.instance = instance
        self._errors: dict[str, list[str]] | None = None
        self._cleaned_data: dict[str, Any] | None = None

        # Build fields dict
        self.fields = dict(self._declared_fields)

    @property
    def errors(self) -> dict[str, list[str]]:
        """Get validation errors."""
        if self._errors is None:
            self.is_valid()
        return self._errors or {}

    @property
    def cleaned_data(self) -> dict[str, Any]:
        """Get cleaned/validated data."""
        if self._cleaned_data is None:
            self.is_valid()
        return self._cleaned_data or {}

    def is_valid(self) -> bool:
        """Validate the form data."""
        self._errors = {}
        self._cleaned_data = {}

        # Build Pydantic model dynamically
        field_definitions: dict[str, tuple] = {}
        for name, field in self.fields.items():
            field_definitions[name] = (field.get_type(), field.to_pydantic_field())

        PydanticModel = create_model("FormModel", **field_definitions)

        try:
            model = PydanticModel(**self.data)
            self._cleaned_data = model.model_dump()
            return True
        except ValidationError as e:
            for error in e.errors():
                field_name = str(error["loc"][0]) if error["loc"] else "__all__"
                if field_name not in self._errors:
                    self._errors[field_name] = []
                self._errors[field_name].append(error["msg"])
            return False

    def add_error(self, field: str | None, error: str) -> None:
        """Add an error to a field."""
        if self._errors is None:
            self._errors = {}

        key = field or "__all__"
        if key not in self._errors:
            self._errors[key] = []
        self._errors[key].append(error)

    def clean(self) -> dict[str, Any]:
        """
        Override to add custom validation.

        Raise ValidationError to add errors.
        """
        return self.cleaned_data

    def as_p(self) -> str:
        """Render form as paragraph elements."""
        html = []
        for name, field in self.fields.items():
            value = self.data.get(name) or self.initial.get(name)
            errors = self.errors.get(name, [])

            label = field.label or name.replace("_", " ").title()
            error_html = "".join(f'<span class="error">{e}</span>' for e in errors)
            input_html = field.render(name, value)

            html.append(f"<p><label>{label}</label>{input_html}{error_html}</p>")

        return "\n".join(html)

    def as_table(self) -> str:
        """Render form as table rows."""
        html = []
        for name, field in self.fields.items():
            value = self.data.get(name) or self.initial.get(name)
            errors = self.errors.get(name, [])

            label = field.label or name.replace("_", " ").title()
            error_html = "".join(f'<span class="error">{e}</span>' for e in errors)
            input_html = field.render(name, value)

            html.append(f"<tr><th><label>{label}</label></th><td>{input_html}{error_html}</td></tr>")

        return "\n".join(html)

    def as_div(self) -> str:
        """Render form as div elements."""
        html = []
        for name, field in self.fields.items():
            value = self.data.get(name) or self.initial.get(name)
            errors = self.errors.get(name, [])

            label = field.label or name.replace("_", " ").title()
            error_html = "".join(f'<div class="error">{e}</div>' for e in errors)
            input_html = field.render(name, value)

            html.append(f'<div class="field"><label>{label}</label>{input_html}{error_html}</div>')

        return "\n".join(html)


class ModelForm(Form):
    """
    Form for editing model instances.

    Usage:
        class PostForm(ModelForm):
            class Meta:
                model = Post
                fields = ["title", "content", "published"]
                exclude = ["author"]

        # Create
        form = PostForm(data=request.form)
        if form.is_valid():
            post = await form.save()

        # Update
        post = await Post.objects.get(pk=1)
        form = PostForm(data=request.form, instance=post)
        if form.is_valid():
            post = await form.save()
    """

    class Meta:
        model: type[Model] = None  # type: ignore
        fields: list[str] | str = "__all__"
        exclude: list[str] = []
        widgets: dict[str, str] = {}

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        initial: dict[str, Any] | None = None,
        instance: Model | None = None,
    ):
        # Get model fields
        self._meta = getattr(self.__class__, "Meta", None)
        if self._meta and self._meta.model:
            self._build_fields_from_model()

        # Initialize with instance data
        if instance is not None:
            initial = initial or {}
            for field_name in self.fields:
                if hasattr(instance, field_name):
                    initial.setdefault(field_name, getattr(instance, field_name))

        super().__init__(data=data, initial=initial, instance=instance)

    def _build_fields_from_model(self) -> None:
        """Build form fields from model."""
        from fastdjango.forms.fields import (
            CharField,
            IntegerField,
            BooleanField,
            TextareaField,
            DateTimeField,
            EmailField,
        )

        model = self._meta.model
        model_fields = getattr(model._meta, "fields_map", {})

        fields_to_include = self._meta.fields
        exclude = self._meta.exclude or []

        if fields_to_include == "__all__":
            fields_to_include = list(model_fields.keys())

        for field_name in fields_to_include:
            if field_name in exclude:
                continue
            if field_name in self._declared_fields:
                continue
            if field_name not in model_fields:
                continue

            model_field = model_fields[field_name]
            form_field = self._model_field_to_form_field(model_field)
            if form_field:
                self._declared_fields[field_name] = form_field

    def _model_field_to_form_field(self, model_field: Any) -> FormField | None:
        """Convert model field to form field."""
        from fastdjango.forms.fields import (
            CharField,
            IntegerField,
            FloatField,
            BooleanField,
            TextareaField,
            DateTimeField,
            DateField,
            EmailField,
        )

        field_class_name = model_field.__class__.__name__

        mapping = {
            "CharField": CharField,
            "TextField": TextareaField,
            "IntField": IntegerField,
            "BigIntField": IntegerField,
            "SmallIntField": IntegerField,
            "FloatField": FloatField,
            "BooleanField": BooleanField,
            "DateField": DateField,
            "DatetimeField": DateTimeField,
        }

        form_field_class = mapping.get(field_class_name, CharField)

        kwargs = {
            "required": not getattr(model_field, "null", False),
        }

        if hasattr(model_field, "max_length"):
            kwargs["max_length"] = model_field.max_length

        if hasattr(model_field, "description") and model_field.description:
            kwargs["label"] = model_field.description

        return form_field_class(**kwargs)

    async def save(self, commit: bool = True) -> Model:
        """Save the model instance."""
        if self.instance is None:
            # Create new instance
            self.instance = self._meta.model(**self.cleaned_data)
        else:
            # Update existing instance
            for key, value in self.cleaned_data.items():
                setattr(self.instance, key, value)

        if commit:
            await self.instance.save()

        return self.instance
