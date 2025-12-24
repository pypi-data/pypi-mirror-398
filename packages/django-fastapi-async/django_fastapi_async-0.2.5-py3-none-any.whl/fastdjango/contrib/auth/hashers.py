"""
FastDjango Password Hashers.
"""

from __future__ import annotations

import hashlib
import secrets
import base64
from abc import ABC, abstractmethod
from typing import Any

from passlib.context import CryptContext


# Passlib context for bcrypt (primary) and pbkdf2 (fallback)
pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto",
    bcrypt__rounds=12,
)


class BasePasswordHasher(ABC):
    """Base password hasher interface."""

    algorithm: str

    @abstractmethod
    def encode(self, password: str, salt: str | None = None) -> str:
        """Hash the password."""
        pass

    @abstractmethod
    def verify(self, password: str, encoded: str) -> bool:
        """Verify password against hash."""
        pass

    @abstractmethod
    def safe_summary(self, encoded: str) -> dict[str, str]:
        """Return a summary of the hash (for display)."""
        pass

    def salt(self) -> str:
        """Generate a random salt."""
        return secrets.token_hex(16)

    def must_update(self, encoded: str) -> bool:
        """Check if hash should be updated."""
        return False


class BCryptHasher(BasePasswordHasher):
    """BCrypt password hasher (recommended)."""

    algorithm = "bcrypt"

    def encode(self, password: str, salt: str | None = None) -> str:
        """Hash password with bcrypt."""
        return pwd_context.hash(password)

    def verify(self, password: str, encoded: str) -> bool:
        """Verify password."""
        try:
            return pwd_context.verify(password, encoded)
        except Exception:
            return False

    def safe_summary(self, encoded: str) -> dict[str, str]:
        return {
            "algorithm": self.algorithm,
            "hash": encoded[:20] + "..." if len(encoded) > 20 else encoded,
        }


class PBKDF2Hasher(BasePasswordHasher):
    """PBKDF2 password hasher."""

    algorithm = "pbkdf2_sha256"
    iterations = 600000

    def encode(self, password: str, salt: str | None = None) -> str:
        """Hash password with PBKDF2."""
        if salt is None:
            salt = self.salt()

        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            self.iterations,
        )
        hash_b64 = base64.b64encode(hash_bytes).decode("ascii")
        return f"pbkdf2_sha256${self.iterations}${salt}${hash_b64}"

    def verify(self, password: str, encoded: str) -> bool:
        """Verify password."""
        try:
            algorithm, iterations, salt, hash_b64 = encoded.split("$")
            if algorithm != "pbkdf2_sha256":
                return False

            hash_bytes = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations),
            )
            expected_hash = base64.b64encode(hash_bytes).decode("ascii")
            return secrets.compare_digest(hash_b64, expected_hash)
        except Exception:
            return False

    def safe_summary(self, encoded: str) -> dict[str, str]:
        algorithm, iterations, salt, hash_b64 = encoded.split("$", 3)
        return {
            "algorithm": algorithm,
            "iterations": iterations,
            "salt": salt[:6] + "...",
            "hash": hash_b64[:10] + "...",
        }


class Argon2Hasher(BasePasswordHasher):
    """Argon2 password hasher (if available)."""

    algorithm = "argon2"

    def __init__(self):
        try:
            import argon2

            self._hasher = argon2.PasswordHasher()
        except ImportError:
            self._hasher = None

    def encode(self, password: str, salt: str | None = None) -> str:
        if self._hasher is None:
            raise ImportError("argon2-cffi is required for Argon2Hasher")
        return self._hasher.hash(password)

    def verify(self, password: str, encoded: str) -> bool:
        if self._hasher is None:
            return False
        try:
            return self._hasher.verify(encoded, password)
        except Exception:
            return False

    def safe_summary(self, encoded: str) -> dict[str, str]:
        return {
            "algorithm": self.algorithm,
            "hash": encoded[:30] + "..." if len(encoded) > 30 else encoded,
        }


# Default hashers
HASHERS: list[BasePasswordHasher] = [
    BCryptHasher(),
    PBKDF2Hasher(),
]


def get_hasher(algorithm: str | None = None) -> BasePasswordHasher:
    """Get a password hasher by algorithm name."""
    if algorithm is None:
        return HASHERS[0]

    for hasher in HASHERS:
        if hasher.algorithm == algorithm:
            return hasher

    raise ValueError(f"Unknown password hashing algorithm: {algorithm}")


def identify_hasher(encoded: str) -> BasePasswordHasher:
    """Identify which hasher was used for the encoded password."""
    if encoded.startswith("$2"):
        return get_hasher("bcrypt")
    elif encoded.startswith("pbkdf2_"):
        return get_hasher("pbkdf2_sha256")
    elif encoded.startswith("$argon2"):
        return get_hasher("argon2")
    else:
        # Default to bcrypt for passlib-generated hashes
        return get_hasher("bcrypt")


def make_password(password: str, salt: str | None = None, hasher: str | None = None) -> str:
    """
    Hash a password.

    Args:
        password: The raw password to hash
        salt: Optional salt (auto-generated if not provided)
        hasher: Algorithm to use (default: bcrypt)

    Returns:
        The hashed password string
    """
    if not password:
        raise ValueError("Password cannot be empty")

    hasher_obj = get_hasher(hasher)
    return hasher_obj.encode(password, salt)


def check_password(password: str, encoded: str) -> bool:
    """
    Check if a password matches the encoded hash.

    Args:
        password: The raw password to check
        encoded: The hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    if not password or not encoded:
        return False

    if encoded.startswith("!"):
        # Unusable password
        return False

    hasher = identify_hasher(encoded)
    return hasher.verify(password, encoded)


def is_password_usable(encoded: str | None) -> bool:
    """Check if the encoded password is usable."""
    if encoded is None or encoded.startswith("!"):
        return False
    return True
