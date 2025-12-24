"""
FastDjango WebSocket support.
Native async WebSocket handling.
"""

from __future__ import annotations

import json
import asyncio
from typing import Any, Callable, TypeVar, Generic
from functools import wraps
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState


T = TypeVar("T")


class WebSocketRouter:
    """
    WebSocket router for organizing WebSocket endpoints.

    Usage:
        ws_router = WebSocketRouter()

        @ws_router.route("/chat/{room_id}")
        async def chat(websocket: WebSocket, room_id: str):
            await websocket.accept()
            async for message in websocket.iter_text():
                await websocket.send_text(f"Room {room_id}: {message}")
    """

    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self._routes: list[tuple[str, Callable]] = []

    def route(self, path: str):
        """Decorator to add a WebSocket route."""
        def decorator(func: Callable) -> Callable:
            full_path = f"{self.prefix}{path}"
            self._routes.append((full_path, func))
            return func
        return decorator

    def get_routes(self) -> list[tuple[str, Callable]]:
        """Get all registered routes."""
        return self._routes


class ConnectionManager:
    """
    Manages WebSocket connections for broadcasting.

    Usage:
        manager = ConnectionManager()

        @router.websocket("/ws/chat/{room}")
        async def chat(websocket: WebSocket, room: str):
            await manager.connect(websocket, room)
            try:
                async for message in websocket.iter_text():
                    await manager.broadcast(message, room)
            except WebSocketDisconnect:
                manager.disconnect(websocket, room)
    """

    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}
        self._user_connections: dict[int, list[WebSocket]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        group: str = "default",
        user_id: int | None = None,
    ) -> None:
        """Accept and track a WebSocket connection."""
        await websocket.accept()

        # Add to group
        if group not in self._connections:
            self._connections[group] = []
        self._connections[group].append(websocket)

        # Track by user
        if user_id is not None:
            if user_id not in self._user_connections:
                self._user_connections[user_id] = []
            self._user_connections[user_id].append(websocket)

    def disconnect(
        self,
        websocket: WebSocket,
        group: str = "default",
        user_id: int | None = None,
    ) -> None:
        """Remove a WebSocket from tracking."""
        if group in self._connections:
            try:
                self._connections[group].remove(websocket)
            except ValueError:
                pass

        if user_id is not None and user_id in self._user_connections:
            try:
                self._user_connections[user_id].remove(websocket)
            except ValueError:
                pass

    async def send_personal(self, message: str | dict, websocket: WebSocket) -> None:
        """Send a message to a specific WebSocket."""
        if websocket.client_state == WebSocketState.CONNECTED:
            if isinstance(message, dict):
                await websocket.send_json(message)
            else:
                await websocket.send_text(message)

    async def send_to_user(self, message: str | dict, user_id: int) -> None:
        """Send a message to all connections of a user."""
        connections = self._user_connections.get(user_id, [])
        for websocket in connections:
            await self.send_personal(message, websocket)

    async def broadcast(
        self,
        message: str | dict,
        group: str = "default",
        exclude: WebSocket | None = None,
    ) -> None:
        """Broadcast a message to all connections in a group."""
        connections = self._connections.get(group, [])
        for websocket in connections:
            if websocket != exclude:
                await self.send_personal(message, websocket)

    async def broadcast_all(self, message: str | dict) -> None:
        """Broadcast a message to all connections in all groups."""
        for group in self._connections:
            await self.broadcast(message, group)

    def get_group_connections(self, group: str) -> list[WebSocket]:
        """Get all connections in a group."""
        return self._connections.get(group, [])

    def get_user_connections(self, user_id: int) -> list[WebSocket]:
        """Get all connections for a user."""
        return self._user_connections.get(user_id, [])

    def count(self, group: str = "default") -> int:
        """Count connections in a group."""
        return len(self._connections.get(group, []))


class WebSocketConsumer:
    """
    Base class for WebSocket consumers (similar to Django Channels).

    Usage:
        class ChatConsumer(WebSocketConsumer):
            async def connect(self):
                self.room = self.scope["path_params"]["room"]
                await self.channel_layer.group_add(self.room, self.channel_name)
                await self.accept()

            async def disconnect(self, code):
                await self.channel_layer.group_discard(self.room, self.channel_name)

            async def receive(self, text_data=None, bytes_data=None):
                data = json.loads(text_data)
                await self.channel_layer.group_send(
                    self.room,
                    {"type": "chat_message", "message": data["message"]}
                )

            async def chat_message(self, event):
                await self.send(text_data=json.dumps({"message": event["message"]}))
    """

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.scope = {
            "type": "websocket",
            "path": str(websocket.url.path),
            "path_params": websocket.path_params,
            "query_string": str(websocket.query_params),
            "headers": dict(websocket.headers),
        }

    async def accept(self, subprotocol: str | None = None) -> None:
        """Accept the WebSocket connection."""
        await self.websocket.accept(subprotocol=subprotocol)

    async def close(self, code: int = 1000) -> None:
        """Close the WebSocket connection."""
        await self.websocket.close(code=code)

    async def send(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
    ) -> None:
        """Send data to the client."""
        if text_data is not None:
            await self.websocket.send_text(text_data)
        elif bytes_data is not None:
            await self.websocket.send_bytes(bytes_data)

    async def connect(self) -> None:
        """Called when WebSocket connects. Override in subclass."""
        await self.accept()

    async def disconnect(self, code: int) -> None:
        """Called when WebSocket disconnects. Override in subclass."""
        pass

    async def receive(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
    ) -> None:
        """Called when data is received. Override in subclass."""
        pass

    async def __call__(self) -> None:
        """Handle the WebSocket lifecycle."""
        try:
            await self.connect()

            while True:
                message = await self.websocket.receive()

                if message["type"] == "websocket.receive":
                    await self.receive(
                        text_data=message.get("text"),
                        bytes_data=message.get("bytes"),
                    )
                elif message["type"] == "websocket.disconnect":
                    break

        except WebSocketDisconnect as e:
            await self.disconnect(e.code)
        except Exception:
            await self.disconnect(1011)


def websocket(path: str):
    """
    Decorator to create a WebSocket endpoint.

    Usage:
        @websocket("/ws/notifications")
        async def notifications(ws: WebSocket):
            await ws.accept()
            while True:
                data = await ws.receive_text()
                await ws.send_text(f"Received: {data}")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(websocket: WebSocket, *args, **kwargs):
            return await func(websocket, *args, **kwargs)

        wrapper._websocket_path = path
        return wrapper

    return decorator


# Global connection manager instance
connection_manager = ConnectionManager()
