"""
FastDjango Messages framework.
Flash messages for web applications.
"""

from enum import IntEnum
from typing import Any


class MessageLevel(IntEnum):
    """Message severity levels."""

    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40


# Shortcuts
DEBUG = MessageLevel.DEBUG
INFO = MessageLevel.INFO
SUCCESS = MessageLevel.SUCCESS
WARNING = MessageLevel.WARNING
ERROR = MessageLevel.ERROR


class Message:
    """A single message."""

    def __init__(
        self,
        level: int,
        message: str,
        extra_tags: str = "",
    ):
        self.level = level
        self.message = message
        self.extra_tags = extra_tags

    @property
    def tags(self) -> str:
        """Get CSS-friendly tags."""
        level_tag = {
            DEBUG: "debug",
            INFO: "info",
            SUCCESS: "success",
            WARNING: "warning",
            ERROR: "error",
        }.get(self.level, "info")

        if self.extra_tags:
            return f"{level_tag} {self.extra_tags}"
        return level_tag

    def __str__(self) -> str:
        return self.message


def add_message(request: Any, level: int, message: str, extra_tags: str = "") -> None:
    """Add a message to the request."""
    session = getattr(request.state, "session", None)
    if session is None:
        return

    messages = session.get("_messages", [])
    messages.append({
        "level": level,
        "message": message,
        "extra_tags": extra_tags,
    })
    session["_messages"] = messages


def get_messages(request: Any) -> list[Message]:
    """Get and clear messages from the request."""
    session = getattr(request.state, "session", None)
    if session is None:
        return []

    messages_data = session.pop("_messages", [])
    return [
        Message(
            level=m["level"],
            message=m["message"],
            extra_tags=m.get("extra_tags", ""),
        )
        for m in messages_data
    ]


# Shortcut functions
def debug(request: Any, message: str, extra_tags: str = "") -> None:
    """Add a debug message."""
    add_message(request, DEBUG, message, extra_tags)


def info(request: Any, message: str, extra_tags: str = "") -> None:
    """Add an info message."""
    add_message(request, INFO, message, extra_tags)


def success(request: Any, message: str, extra_tags: str = "") -> None:
    """Add a success message."""
    add_message(request, SUCCESS, message, extra_tags)


def warning(request: Any, message: str, extra_tags: str = "") -> None:
    """Add a warning message."""
    add_message(request, WARNING, message, extra_tags)


def error(request: Any, message: str, extra_tags: str = "") -> None:
    """Add an error message."""
    add_message(request, ERROR, message, extra_tags)


__all__ = [
    "MessageLevel",
    "Message",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "add_message",
    "get_messages",
    "debug",
    "info",
    "success",
    "warning",
    "error",
]
