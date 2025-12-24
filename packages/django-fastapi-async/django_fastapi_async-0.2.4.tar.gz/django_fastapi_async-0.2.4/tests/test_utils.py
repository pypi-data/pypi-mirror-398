"""
Tests for utility functions.
"""

import pytest


class TestCrypto:
    """Test cryptographic utilities."""

    def test_get_random_string(self):
        """Test random string generation."""
        from fastdjango.utils.crypto import get_random_string

        s1 = get_random_string(32)
        s2 = get_random_string(32)

        assert len(s1) == 32
        assert len(s2) == 32
        assert s1 != s2  # Should be different

    def test_get_random_string_custom_chars(self):
        """Test random string with custom characters."""
        from fastdjango.utils.crypto import get_random_string

        result = get_random_string(10, allowed_chars="abc")
        assert len(result) == 10
        assert all(c in "abc" for c in result)

    def test_constant_time_compare(self):
        """Test constant time comparison."""
        from fastdjango.utils.crypto import constant_time_compare

        assert constant_time_compare("test", "test")
        assert not constant_time_compare("test", "wrong")
        assert constant_time_compare(b"test", b"test")


class TestText:
    """Test text utilities."""

    def test_slugify(self):
        """Test slugify function."""
        from fastdjango.utils.text import slugify

        assert slugify("Hello World") == "hello-world"
        assert slugify("Test  Multiple   Spaces") == "test-multiple-spaces"
        assert slugify("Special!@#$%Characters") == "specialcharacters"
        assert slugify("UPPERCASE") == "uppercase"

    def test_slugify_unicode(self):
        """Test slugify with unicode."""
        from fastdjango.utils.text import slugify

        assert slugify("Olá Mundo", allow_unicode=True) == "olá-mundo"
        assert slugify("Café") == "caf"  # Without unicode

    def test_truncate_chars(self):
        """Test character truncation."""
        from fastdjango.utils.text import truncate_chars

        assert truncate_chars("Hello", 10) == "Hello"
        assert truncate_chars("Hello World Test", 10) == "Hello..."
        assert truncate_chars("Short", 100) == "Short"

    def test_truncate_words(self):
        """Test word truncation."""
        from fastdjango.utils.text import truncate_words

        assert truncate_words("Hello World Test", 2) == "Hello World..."
        assert truncate_words("Hello", 5) == "Hello"

    def test_camel_to_snake(self):
        """Test CamelCase to snake_case conversion."""
        from fastdjango.utils.text import camel_to_snake

        assert camel_to_snake("CamelCase") == "camel_case"
        assert camel_to_snake("HTTPResponse") == "http_response"
        assert camel_to_snake("simple") == "simple"

    def test_snake_to_camel(self):
        """Test snake_case to CamelCase conversion."""
        from fastdjango.utils.text import snake_to_camel

        assert snake_to_camel("snake_case") == "snakeCase"
        assert snake_to_camel("http_response") == "httpResponse"


class TestMessages:
    """Test message framework."""

    def test_message_levels(self):
        """Test message level constants."""
        from fastdjango.contrib.messages import DEBUG, INFO, SUCCESS, WARNING, ERROR

        assert DEBUG < INFO < SUCCESS < WARNING < ERROR

    def test_message_creation(self):
        """Test Message class."""
        from fastdjango.contrib.messages import Message, INFO

        msg = Message(INFO, "Test message")
        assert str(msg) == "Test message"
        assert msg.level == INFO
        assert msg.tags == "info"

    def test_message_with_extra_tags(self):
        """Test Message with extra tags."""
        from fastdjango.contrib.messages import Message, SUCCESS

        msg = Message(SUCCESS, "Success!", extra_tags="custom")
        assert msg.tags == "success custom"
