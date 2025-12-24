"""
Text utilities.
"""

import re
import unicodedata
from typing import Any


def slugify(value: str, allow_unicode: bool = False) -> str:
    """
    Convert a string to a URL-friendly slug.

    Args:
        value: String to convert
        allow_unicode: Allow unicode characters

    Returns:
        Slugified string
    """
    value = str(value)

    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )

    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def truncate_chars(value: str, length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum number of characters.

    Args:
        value: String to truncate
        length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(value) <= length:
        return value

    truncated = value[: length - len(suffix)]
    # Try to break at a word boundary
    last_space = truncated.rfind(" ")
    if last_space > length // 2:
        truncated = truncated[:last_space]

    return truncated + suffix


def truncate_words(value: str, num_words: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum number of words.

    Args:
        value: String to truncate
        num_words: Maximum number of words
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    words = value.split()
    if len(words) <= num_words:
        return value

    return " ".join(words[:num_words]) + suffix


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def snake_to_camel(name: str) -> str:
    """Convert snake_case to CamelCase."""
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def format_lazy(format_string: str, *args: Any, **kwargs: Any) -> str:
    """Format a string lazily."""
    return format_string.format(*args, **kwargs)
