"""
FastDjango Forms.
Pydantic-based forms with Django-like API.
"""

from fastdjango.forms.forms import Form, ModelForm
from fastdjango.forms.fields import (
    CharField,
    IntegerField,
    FloatField,
    BooleanField,
    EmailField,
    URLField,
    DateField,
    DateTimeField,
    ChoiceField,
    MultipleChoiceField,
    FileField,
    ImageField,
    PasswordField,
    HiddenField,
    TextareaField,
)
from fastdjango.forms.schemas import model_to_pydantic

__all__ = [
    "Form",
    "ModelForm",
    # Fields
    "CharField",
    "IntegerField",
    "FloatField",
    "BooleanField",
    "EmailField",
    "URLField",
    "DateField",
    "DateTimeField",
    "ChoiceField",
    "MultipleChoiceField",
    "FileField",
    "ImageField",
    "PasswordField",
    "HiddenField",
    "TextareaField",
    # Utilities
    "model_to_pydantic",
]
