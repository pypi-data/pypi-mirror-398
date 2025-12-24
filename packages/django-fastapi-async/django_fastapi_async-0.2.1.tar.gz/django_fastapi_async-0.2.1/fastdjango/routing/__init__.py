"""
FastDjango Routing.
"""

from fastdjango.routing.router import Router, include
from fastdjango.routing.websocket import WebSocketRouter, websocket

__all__ = [
    "Router",
    "include",
    "WebSocketRouter",
    "websocket",
]
