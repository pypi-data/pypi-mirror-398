"""
Cryptographic utilities.
"""

import secrets
import string
import hmac


def get_random_string(length: int = 32, allowed_chars: str | None = None) -> str:
    """
    Generate a random string of given length.

    Args:
        length: Length of the string to generate
        allowed_chars: Characters to use (default: alphanumeric)

    Returns:
        Random string
    """
    if allowed_chars is None:
        allowed_chars = string.ascii_letters + string.digits

    return "".join(secrets.choice(allowed_chars) for _ in range(length))


def constant_time_compare(val1: str | bytes, val2: str | bytes) -> bool:
    """
    Compare two strings in constant time to prevent timing attacks.

    Args:
        val1: First value
        val2: Second value

    Returns:
        True if values are equal
    """
    if isinstance(val1, str):
        val1 = val1.encode("utf-8")
    if isinstance(val2, str):
        val2 = val2.encode("utf-8")

    return hmac.compare_digest(val1, val2)


def salted_hmac(key_salt: str, value: str, secret: str | None = None) -> bytes:
    """
    Generate a salted HMAC.

    Args:
        key_salt: Salt for the key
        value: Value to hash
        secret: Secret key (uses settings.SECRET_KEY if not provided)

    Returns:
        HMAC digest
    """
    import hashlib

    if secret is None:
        from fastdjango.conf import settings
        secret = settings.SECRET_KEY

    key = hashlib.sha256((key_salt + secret).encode()).digest()
    return hmac.new(key, value.encode(), hashlib.sha256).digest()
