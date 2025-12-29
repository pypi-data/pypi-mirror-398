"""Kryten-py: Python library for building CyTube microservices via Kryten bridge and NATS.

This library provides a high-level, type-safe API for interacting with CyTube servers
through the Kryten bridge and NATS message bus. It enables rapid development of
microservices like chat bots, automated DJs, moderation tools, and analytics systems.

Example:
    >>> from kryten import KrytenClient, ChatMessageEvent
    >>>
    >>> config = {
    ...     "nats": {"servers": ["nats://localhost:4222"]},
    ...     "channels": [{"domain": "cytu.be", "channel": "lounge"}]
    ... }
    >>>
    >>> async with KrytenClient(config) as client:
    ...     @client.on("chatmsg")
    ...     async def handle_chat(event: ChatMessageEvent):
    ...         print(f"{event.username}: {event.message}")
    ...
    ...     await client.send_chat("lounge", "Hello from bot!")
    ...     await client.run()
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("kryten-py")
except PackageNotFoundError:
    __version__ = "0.0.0"

from kryten.client import KrytenClient
from kryten.config import ChannelConfig, KrytenConfig, MetricsConfig, NatsConfig, ServiceConfig
from kryten.exceptions import (
    HandlerError,
    KrytenConnectionError,
    KrytenError,
    KrytenTimeoutError,
    KrytenValidationError,
    PublishError,
)
from kryten.health import ChannelInfo, HealthStatus
from kryten.kv_store import (
    get_kv_store,
    get_or_create_kv_store,
    kv_delete,
    kv_get,
    kv_get_all,
    kv_keys,
    kv_put,
)
from kryten.lifecycle_events import LifecycleEventPublisher
from kryten.metrics_server import BaseMetricsServer, SimpleMetricsServer
from kryten.mock import MockKrytenClient
from kryten.models import (
    ChangeMediaEvent,
    ChatMessageEvent,
    PlaylistUpdateEvent,
    RawEvent,
    UserJoinEvent,
    UserLeaveEvent,
)

__all__ = [
    # Core client
    "KrytenClient",
    "MockKrytenClient",
    # Configuration
    "KrytenConfig",
    "NatsConfig",
    "ChannelConfig",
    "ServiceConfig",
    "MetricsConfig",
    # Event models
    "RawEvent",
    "ChatMessageEvent",
    "UserJoinEvent",
    "UserLeaveEvent",
    "ChangeMediaEvent",
    "PlaylistUpdateEvent",
    # Health & status
    "HealthStatus",
    "ChannelInfo",
    # Lifecycle events
    "LifecycleEventPublisher",
    # Metrics server
    "BaseMetricsServer",
    "SimpleMetricsServer",
    # KeyValue store helpers
    "get_kv_store",
    "get_or_create_kv_store",
    "kv_get",
    "kv_put",
    "kv_delete",
    "kv_keys",
    "kv_get_all",
    # Exceptions
    "KrytenError",
    "KrytenConnectionError",
    "KrytenValidationError",
    "KrytenTimeoutError",
    "PublishError",
    "HandlerError",
]
