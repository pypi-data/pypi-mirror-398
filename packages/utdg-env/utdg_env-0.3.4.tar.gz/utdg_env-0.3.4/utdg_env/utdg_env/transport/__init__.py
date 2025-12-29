"""
Transport module for UTDG.

Provides runtime-selectable client/server WebSocket backends.

Running as a module:

    python -m utdg_env.transport check [mode]
"""

from utdg_env.transport.transport_base import (
    Transport,
    TransportError,
    TransportTimeout,
    TransportDisconnected,
)
from utdg_env.transport.transport_hf import HFTransport
from utdg_env.transport.transport_native import NativeTransport
from utdg_env.transport.transport_web import WebTransport
from utdg_env.transport.protocol import (
    Message,
    MessageType,
    ActionPayload,
    ConfigData,
    create_config_message,
)

__all__ = [
    "Transport",
    "TransportError",
    "TransportTimeout",
    "TransportDisconnected",
    "HFTransport",
    "NativeTransport",
    "WebTransport",
    "Message",
    "MessageType",
    "ActionPayload",
    "ConfigData",
    "create_config_message",
]
