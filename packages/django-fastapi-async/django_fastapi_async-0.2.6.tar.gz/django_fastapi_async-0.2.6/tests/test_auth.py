"""
Tests for authentication.
"""

import pytest


class TestPasswordHashers:
    """Test password hashing."""

    def test_make_password(self):
        """Test password hashing."""
        from fastdjango.contrib.auth.hashers import make_password, check_password

        hashed = make_password("testpassword")
        assert hashed != "testpassword"
        assert check_password("testpassword", hashed)

    def test_check_password_invalid(self):
        """Test checking invalid password."""
        from fastdjango.contrib.auth.hashers import make_password, check_password

        hashed = make_password("testpassword")
        assert not check_password("wrongpassword", hashed)

    def test_empty_password(self):
        """Test empty password handling."""
        from fastdjango.contrib.auth.hashers import make_password

        with pytest.raises(ValueError):
            make_password("")

    def test_unusable_password(self):
        """Test unusable password."""
        from fastdjango.contrib.auth.hashers import check_password, is_password_usable

        assert not is_password_usable("!")
        assert not check_password("any", "!")


class TestUserModel:
    """Test User model."""

    @pytest.mark.asyncio
    async def test_create_user(self, setup_database):
        """Test creating a user."""
        from fastdjango.contrib.auth.models import User

        user = await User.create_user(
            username="newuser",
            email="new@example.com",
            password="password123",
        )

        assert user.pk is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    @pytest.mark.asyncio
    async def test_create_superuser(self, setup_database):
        """Test creating a superuser."""
        from fastdjango.contrib.auth.models import User

        user = await User.create_superuser(
            username="superadmin",
            email="super@example.com",
            password="password123",
        )

        assert user.is_staff is True
        assert user.is_superuser is True

    @pytest.mark.asyncio
    async def test_check_password(self, user):
        """Test password checking."""
        assert await user.check_password("testpassword123")
        assert not await user.check_password("wrongpassword")

    @pytest.mark.asyncio
    async def test_set_password(self, user):
        """Test setting password."""
        await user.set_password("newpassword")
        assert await user.check_password("newpassword")

    def test_get_full_name(self, user):
        """Test getting full name."""
        user.first_name = "Test"
        user.last_name = "User"
        assert user.get_full_name() == "Test User"

    def test_is_authenticated(self, user):
        """Test is_authenticated property."""
        assert user.is_authenticated is True

    def test_is_anonymous(self, user):
        """Test is_anonymous property."""
        assert user.is_anonymous is False


class TestAnonymousUser:
    """Test AnonymousUser."""

    def test_anonymous_user_properties(self):
        """Test AnonymousUser properties."""
        from fastdjango.contrib.auth.models import AnonymousUser

        anon = AnonymousUser()

        assert anon.pk is None
        assert anon.is_authenticated is False
        assert anon.is_anonymous is True
        assert anon.is_active is False
        assert anon.is_staff is False

    @pytest.mark.asyncio
    async def test_anonymous_user_permissions(self):
        """Test AnonymousUser has no permissions."""
        from fastdjango.contrib.auth.models import AnonymousUser

        anon = AnonymousUser()

        assert not await anon.has_perm("any.permission")
        assert not await anon.has_perms(["perm1", "perm2"])


class TestAuthentication:
    """Test authentication functions."""

    @pytest.mark.asyncio
    async def test_authenticate_success(self, user):
        """Test successful authentication."""
        from fastdjango.contrib.auth.backends import authenticate

        authenticated = await authenticate(
            username="testuser",
            password="testpassword123",
        )

        assert authenticated is not None
        assert authenticated.pk == user.pk

    @pytest.mark.asyncio
    async def test_authenticate_failure(self, user):
        """Test failed authentication."""
        from fastdjango.contrib.auth.backends import authenticate

        authenticated = await authenticate(
            username="testuser",
            password="wrongpassword",
        )

        assert authenticated is None

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, user):
        """Test authentication with inactive user."""
        from fastdjango.contrib.auth.backends import authenticate

        user.is_active = False
        await user.save()

        authenticated = await authenticate(
            username="testuser",
            password="testpassword123",
        )

        assert authenticated is None
