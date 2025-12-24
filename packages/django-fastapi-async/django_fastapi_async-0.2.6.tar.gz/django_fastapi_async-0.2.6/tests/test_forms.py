"""
Tests for forms and schemas.
"""

import pytest


class TestFormFields:
    """Test form field definitions."""

    def test_char_field(self):
        """Test CharField."""
        from fastdjango.forms.fields import CharField

        field = CharField(max_length=100, required=True)
        assert field.max_length == 100
        assert field.required is True
        assert field.widget == "text"

    def test_email_field(self):
        """Test EmailField."""
        from fastdjango.forms.fields import EmailField

        field = EmailField(required=True)
        assert field.widget == "email"

    def test_password_field(self):
        """Test PasswordField."""
        from fastdjango.forms.fields import PasswordField

        field = PasswordField()
        assert field.widget == "password"

    def test_boolean_field(self):
        """Test BooleanField."""
        from fastdjango.forms.fields import BooleanField

        field = BooleanField()
        assert field.widget == "checkbox"
        assert field.required is False  # BooleanField defaults to not required

    def test_choice_field(self):
        """Test ChoiceField."""
        from fastdjango.forms.fields import ChoiceField

        choices = [("a", "Option A"), ("b", "Option B")]
        field = ChoiceField(choices=choices)
        assert field.widget == "select"
        assert field.choices == choices


class TestForm:
    """Test Form class."""

    def test_form_validation_success(self):
        """Test successful form validation."""
        from fastdjango.forms import Form
        from fastdjango.forms.fields import CharField, EmailField

        class TestForm(Form):
            name = CharField(max_length=100)
            email = EmailField()

        form = TestForm(data={"name": "John", "email": "john@example.com"})
        assert form.is_valid()
        assert form.cleaned_data["name"] == "John"
        assert form.cleaned_data["email"] == "john@example.com"

    def test_form_validation_failure(self):
        """Test form validation failure."""
        from fastdjango.forms import Form
        from fastdjango.forms.fields import CharField

        class TestForm(Form):
            name = CharField(required=True)

        form = TestForm(data={})
        assert not form.is_valid()
        assert "name" in form.errors

    def test_form_initial_values(self):
        """Test form with initial values."""
        from fastdjango.forms import Form
        from fastdjango.forms.fields import CharField

        class TestForm(Form):
            name = CharField()

        form = TestForm(initial={"name": "Default"})
        assert form.initial["name"] == "Default"

    def test_form_add_error(self):
        """Test adding errors manually."""
        from fastdjango.forms import Form
        from fastdjango.forms.fields import CharField

        class TestForm(Form):
            name = CharField()

        form = TestForm(data={"name": "Test"})
        form.is_valid()
        form.add_error("name", "Custom error")
        assert "Custom error" in form.errors["name"]


class TestFormRendering:
    """Test form rendering."""

    def test_form_as_p(self):
        """Test rendering form as paragraphs."""
        from fastdjango.forms import Form
        from fastdjango.forms.fields import CharField

        class TestForm(Form):
            name = CharField(label="Your Name")

        form = TestForm()
        html = form.as_p()
        assert "<p>" in html
        assert "Your Name" in html
        assert 'name="name"' in html

    def test_form_as_div(self):
        """Test rendering form as divs."""
        from fastdjango.forms import Form
        from fastdjango.forms.fields import CharField

        class TestForm(Form):
            name = CharField()

        form = TestForm()
        html = form.as_div()
        assert '<div class="field">' in html


class TestSchemaGenerator:
    """Test Pydantic schema generation."""

    def test_schema_generator(self):
        """Test SchemaGenerator."""
        from fastdjango.forms.schemas import SchemaGenerator
        from tortoise import Model as TortoiseModel
        from tortoise import fields

        class SampleModel(TortoiseModel):
            id = fields.IntField(pk=True)
            name = fields.CharField(max_length=100)
            email = fields.CharField(max_length=254)
            created_at = fields.DatetimeField(auto_now_add=True)

            class Meta:
                table = "sample"

        # Note: This would need proper model registration to work fully
        # Just testing the generator creation
        gen = SchemaGenerator(SampleModel)
        assert gen.model == SampleModel
