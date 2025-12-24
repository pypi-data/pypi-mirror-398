"""
FastDjango signals - async-first signal dispatcher.
Similar to Django signals but fully async.
"""

from __future__ import annotations

import asyncio
import weakref
from typing import Any, Callable, TypeVar, Generic
from collections.abc import Coroutine


T = TypeVar("T")
Receiver = Callable[..., Coroutine[Any, Any, Any] | Any]


class Signal(Generic[T]):
    """
    Async signal dispatcher.

    Usage:
        # Define signal
        post_save = Signal()

        # Connect receiver
        @post_save.connect
        async def on_post_save(sender, instance, created, **kwargs):
            print(f"Saved: {instance}")

        # Or connect with sender filter
        @post_save.connect(sender=User)
        async def on_user_save(sender, instance, created, **kwargs):
            print(f"User saved: {instance}")

        # Send signal
        await post_save.send(sender=User, instance=user, created=True)
    """

    def __init__(self, providing_args: list[str] | None = None):
        """
        Initialize signal.

        Args:
            providing_args: List of argument names this signal provides.
                           Used for documentation only.
        """
        self.providing_args = providing_args or []
        self._receivers: list[tuple[type | None, weakref.ref[Receiver] | Receiver]] = []
        self._lock = asyncio.Lock()

    def connect(
        self,
        receiver: Receiver | None = None,
        sender: type | None = None,
        weak: bool = True,
    ) -> Receiver | Callable[[Receiver], Receiver]:
        """
        Connect a receiver to this signal.

        Can be used as a decorator:
            @signal.connect
            async def handler(sender, **kwargs):
                pass

            @signal.connect(sender=MyModel)
            async def handler(sender, **kwargs):
                pass
        """
        def _connect(receiver: Receiver) -> Receiver:
            if weak:
                ref = weakref.ref(receiver)
            else:
                ref = receiver
            self._receivers.append((sender, ref))
            return receiver

        if receiver is not None:
            return _connect(receiver)
        return _connect

    def disconnect(
        self,
        receiver: Receiver,
        sender: type | None = None,
    ) -> bool:
        """
        Disconnect a receiver from this signal.

        Returns True if the receiver was connected, False otherwise.
        """
        disconnected = False
        new_receivers = []

        for r_sender, r_receiver in self._receivers:
            if r_sender == sender:
                if isinstance(r_receiver, weakref.ref):
                    if r_receiver() is receiver:
                        disconnected = True
                        continue
                elif r_receiver is receiver:
                    disconnected = True
                    continue
            new_receivers.append((r_sender, r_receiver))

        self._receivers = new_receivers
        return disconnected

    async def send(
        self,
        sender: type,
        **kwargs: Any,
    ) -> list[tuple[Receiver, Any]]:
        """
        Send this signal with the given sender and keyword arguments.

        Returns a list of (receiver, response) tuples.
        """
        responses = []

        for r_sender, r_receiver in self._receivers:
            # Check sender filter
            if r_sender is not None and r_sender is not sender:
                continue

            # Get actual receiver from weakref
            if isinstance(r_receiver, weakref.ref):
                receiver = r_receiver()
                if receiver is None:
                    continue
            else:
                receiver = r_receiver

            try:
                result = receiver(sender=sender, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                responses.append((receiver, result))
            except Exception as e:
                responses.append((receiver, e))

        return responses

    async def send_robust(
        self,
        sender: type,
        **kwargs: Any,
    ) -> list[tuple[Receiver, Any | Exception]]:
        """
        Send signal, catching exceptions from receivers.

        Returns a list of (receiver, response or exception) tuples.
        """
        return await self.send(sender=sender, **kwargs)

    def has_listeners(self, sender: type | None = None) -> bool:
        """Check if this signal has any connected receivers."""
        if sender is None:
            return bool(self._receivers)

        for r_sender, _ in self._receivers:
            if r_sender is None or r_sender is sender:
                return True
        return False


# Built-in signals
pre_save = Signal(providing_args=["instance", "raw", "using", "update_fields"])
post_save = Signal(providing_args=["instance", "created", "raw", "using", "update_fields"])
pre_delete = Signal(providing_args=["instance", "using"])
post_delete = Signal(providing_args=["instance", "using"])
m2m_changed = Signal(providing_args=["action", "instance", "reverse", "model", "pk_set", "using"])

# Request signals
request_started = Signal(providing_args=["environ", "scope"])
request_finished = Signal(providing_args=["environ", "scope"])

# User signals
user_logged_in = Signal(providing_args=["request", "user"])
user_logged_out = Signal(providing_args=["request", "user"])
user_login_failed = Signal(providing_args=["credentials", "request"])
