"""
Pytest configuration and fixtures.
"""

import asyncio
import pytest
from typing import AsyncGenerator

# Configure asyncio mode
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """Setup test database before each test."""
    from tortoise import Tortoise

    # Initialize with SQLite in memory
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["fastdjango.contrib.auth.models"]},
    )
    await Tortoise.generate_schemas()

    yield

    await Tortoise.close_connections()


@pytest.fixture
def settings():
    """Provide test settings."""
    from fastdjango.conf import settings as app_settings

    # Configure for testing
    app_settings._settings.update({
        "DEBUG": True,
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "DATABASES": {
            "default": {
                "ENGINE": "aiosqlite",
                "NAME": ":memory:",
            }
        },
    })

    return app_settings


@pytest.fixture
async def user():
    """Create a test user."""
    from fastdjango.contrib.auth.models import User

    user = await User.create_user(
        username="testuser",
        email="test@example.com",
        password="testpassword123",
    )
    return user


@pytest.fixture
async def superuser():
    """Create a test superuser."""
    from fastdjango.contrib.auth.models import User

    user = await User.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpassword123",
    )
    return user


@pytest.fixture
def client():
    """Create a test client."""
    from fastapi.testclient import TestClient
    from fastdjango import FastDjango

    app = FastDjango(debug=True)
    return TestClient(app.app)
