"""
Tests for database/ORM functionality.
"""

import pytest
from tortoise import fields as tortoise_fields
from fastdjango.db.models import Model
from fastdjango.db import fields


class TestModel(Model):
    """Test model for ORM tests."""

    id = tortoise_fields.IntField(pk=True)
    name = tortoise_fields.CharField(max_length=100)
    description = tortoise_fields.TextField(null=True)
    is_active = tortoise_fields.BooleanField(default=True)

    class Meta:
        table = "test_model"


class TestFields:
    """Test field definitions."""

    def test_char_field(self):
        """Test CharField creation."""
        field = fields.CharField(max_length=100)
        assert field.max_length == 100

    def test_integer_field(self):
        """Test IntegerField creation."""
        field = fields.IntegerField(default=0)
        assert field.default == 0

    def test_boolean_field(self):
        """Test BooleanField creation."""
        field = fields.BooleanField(default=True)
        assert field.default is True

    def test_text_field(self):
        """Test TextField creation."""
        field = fields.TextField(blank=True)
        assert field.null is False

    def test_datetime_field(self):
        """Test DateTimeField creation."""
        field = fields.DateTimeField(auto_now_add=True)
        assert field.auto_now_add is True


class TestManager:
    """Test Manager functionality."""

    @pytest.mark.asyncio
    async def test_all(self, setup_database):
        """Test Manager.all()."""
        from tortoise import Tortoise

        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": [__name__]},
        )
        await Tortoise.generate_schemas()

        await TestModel.create(name="Test 1")
        await TestModel.create(name="Test 2")

        all_items = await TestModel.all()
        assert len(all_items) == 2

        await Tortoise.close_connections()

    @pytest.mark.asyncio
    async def test_filter(self, setup_database):
        """Test Manager.filter()."""
        from tortoise import Tortoise

        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": [__name__]},
        )
        await Tortoise.generate_schemas()

        await TestModel.create(name="Active", is_active=True)
        await TestModel.create(name="Inactive", is_active=False)

        active = await TestModel.filter(is_active=True)
        assert len(active) == 1
        assert active[0].name == "Active"

        await Tortoise.close_connections()


class TestQuerySet:
    """Test QuerySet functionality."""

    @pytest.mark.asyncio
    async def test_queryset_chain(self, setup_database):
        """Test QuerySet chaining."""
        from tortoise import Tortoise

        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": [__name__]},
        )
        await Tortoise.generate_schemas()

        await TestModel.create(name="A", is_active=True)
        await TestModel.create(name="B", is_active=True)
        await TestModel.create(name="C", is_active=False)

        result = await TestModel.filter(is_active=True).order_by("name")
        assert len(result) == 2
        assert result[0].name == "A"
        assert result[1].name == "B"

        await Tortoise.close_connections()

    @pytest.mark.asyncio
    async def test_queryset_count(self, setup_database):
        """Test QuerySet.count()."""
        from tortoise import Tortoise

        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": [__name__]},
        )
        await Tortoise.generate_schemas()

        await TestModel.create(name="Test 1")
        await TestModel.create(name="Test 2")

        count = await TestModel.all().count()
        assert count == 2

        await Tortoise.close_connections()

    @pytest.mark.asyncio
    async def test_queryset_exists(self, setup_database):
        """Test QuerySet.exists()."""
        from tortoise import Tortoise

        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": [__name__]},
        )
        await Tortoise.generate_schemas()

        assert not await TestModel.all().exists()

        await TestModel.create(name="Test")
        assert await TestModel.all().exists()

        await Tortoise.close_connections()
