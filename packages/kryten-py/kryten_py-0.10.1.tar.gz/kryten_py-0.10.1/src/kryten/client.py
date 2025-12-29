"""Core Kryten client implementation."""

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import nats
from nats.aio.client import Client as NATSClient

from kryten import __version__
from kryten.config import KrytenConfig
from kryten.exceptions import (
    KrytenConnectionError,
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
from kryten.models import (
    ChangeMediaEvent,
    ChatMessageEvent,
    PlaylistUpdateEvent,
    RawEvent,
    UserJoinEvent,
    UserLeaveEvent,
)
from kryten.subject_builder import SUBJECT_PREFIX, build_command_subject


class KrytenClient:
    """High-level client for CyTube interaction via NATS.

    Examples:
        Basic usage with context manager:

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
        ...     await client.run()  # Run until stopped
    """

    def __init__(
        self,
        config: dict[str, Any] | KrytenConfig,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize client with configuration.

        Args:
            config: Dictionary or KrytenConfig model with NATS and channel settings
            logger: Optional logger instance (creates default if None)

        Raises:
            KrytenValidationError: If configuration is invalid
        """
        # Parse and validate configuration
        if isinstance(config, dict):
            try:
                self.config = KrytenConfig(**config)
            except Exception as e:
                raise KrytenValidationError(f"Invalid configuration: {e}") from e
        else:
            self.config = config

        # Set up logging
        self.logger = logger or logging.getLogger(__name__)
        self.logger.setLevel(self.config.log_level)

        # NATS connection
        self.__nats: NATSClient | None = None
        self._connected = False
        self._connection_time: float | None = None

        # Event handlers: {event_name: [(handler, channel_filter, domain_filter), ...]}
        self._handlers: dict[
            str, list[tuple[Callable[[Any], Any], str | None, str | None]]
        ] = defaultdict(list)

        # Subscriptions
        self._subscriptions: list[Any] = []

        # Control flow
        self._running = False
        self._stop_requested = False

        # Metrics
        self._events_received = 0
        self._commands_sent = 0
        self._errors = 0
        self._event_latencies: list[float] = []
        self._last_event_time: datetime | None = None
        self._channel_metrics: dict[str, int] = defaultdict(int)

        # Lifecycle events - will be initialized on connect if service config provided
        self._lifecycle: LifecycleEventPublisher | None = None

    async def connect(self) -> None:
        """Establish NATS connection and subscribe to configured channels.

        Raises:
            KrytenConnectionError: If NATS connection fails after retries
            KrytenValidationError: If configuration is invalid
        """
        if self._connected:
            self.logger.warning("Already connected to NATS")
            return

        self.logger.info(
            "Connecting to NATS",
            extra={"servers": self.config.nats.servers},
        )

        try:
            # Create NATS client
            self.__nats = await nats.connect(
                servers=self.config.nats.servers,
                user=self.config.nats.user,
                password=self.config.nats.password,
                token=self.config.nats.token,
                connect_timeout=self.config.nats.connect_timeout,
                reconnect_time_wait=self.config.nats.reconnect_time_wait,
                max_reconnect_attempts=self.config.nats.max_reconnect_attempts,
                ping_interval=self.config.nats.ping_interval,
                error_cb=self._on_error,
                disconnected_cb=self._on_disconnected,
                reconnected_cb=self._on_reconnected,
                closed_cb=self._on_closed,
            )

            self._connected = True
            self._connection_time = time.time()

            # Subscribe to channels
            await self._setup_subscriptions()

            # Start lifecycle publisher if service config provided
            if self.config.service:
                # Auto-detect endpoint config from metrics section if not set in service
                health_port = self.config.service.health_port
                health_path = self.config.service.health_path
                metrics_port = self.config.service.metrics_port
                metrics_path = self.config.service.metrics_path

                # Fallback to metrics config if service endpoints not explicitly set
                if self.config.metrics and health_port is None:
                    health_port = self.config.metrics.port
                    health_path = self.config.metrics.health_path
                if self.config.metrics and metrics_port is None:
                    metrics_port = self.config.metrics.port
                    metrics_path = self.config.metrics.metrics_path

                self._lifecycle = LifecycleEventPublisher(
                    nats_client=self.__nats,
                    service_name=self.config.service.name,
                    version=self.config.service.version,
                    heartbeat_interval=self.config.service.heartbeat_interval,
                    enable_heartbeat=self.config.service.enable_heartbeat,
                    enable_discovery=self.config.service.enable_discovery,
                    logger=self.logger,
                    health_port=health_port,
                    health_path=health_path,
                    metrics_port=metrics_port,
                    metrics_path=metrics_path,
                )
                await self._lifecycle.start()
                await self._lifecycle.publish_startup()

            self.logger.info(
                f"kryten-py v{__version__} connected to NATS",
                extra={"channels": [f"{c.domain}/{c.channel}" for c in self.config.channels]},
            )

        except Exception as e:
            self.logger.error(f"Failed to connect to NATS: {e}", exc_info=True)
            raise KrytenConnectionError(f"NATS connection failed: {e}") from e

    async def disconnect(self, reason: str = "Normal shutdown") -> None:
        """Gracefully close NATS connection and cleanup resources.

        Args:
            reason: Reason for disconnection (included in shutdown event)
        """
        if not self._connected or self.__nats is None:
            self.logger.debug("Not connected, nothing to disconnect")
            return

        self.logger.info("Disconnecting from NATS")

        try:
            # Publish shutdown event first (before closing connection)
            if self._lifecycle:
                await self._lifecycle.publish_shutdown(reason=reason)
                # Stop heartbeat task but don't unsubscribe - drain() handles that
                self._lifecycle._running = False
                if self._lifecycle._heartbeat_task and not self._lifecycle._heartbeat_task.done():
                    self._lifecycle._heartbeat_task.cancel()
                    try:
                        await self._lifecycle._heartbeat_task
                    except asyncio.CancelledError:
                        pass
                self._lifecycle = None

            # Clear subscription references - drain() will handle actual unsubscribe
            self._subscriptions.clear()

            # Use close() instead of drain() to avoid timeout issues
            # drain() can hang if the server is slow or messages are in-flight
            try:
                await asyncio.wait_for(self.__nats.close(), timeout=5.0)
            except asyncio.TimeoutError:
                self.logger.warning("NATS close timed out, forcing disconnect")
                # Force close if clean close times out
                if self.__nats.is_connected:
                    await self.__nats.close()

            self._connected = False
            self.__nats = None
            self._connection_time = None

            self.logger.info("Disconnected from NATS successfully")

        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}", exc_info=True)
            # Ensure we mark as disconnected even on error
            self._connected = False
            self.__nats = None
            self._connection_time = None

    @property
    def lifecycle(self) -> LifecycleEventPublisher | None:
        """Get the lifecycle event publisher (if service config provided).

        Returns:
            LifecycleEventPublisher instance or None if no service config
        """
        return self._lifecycle

    def on_group_restart(self, callback: Callable[[dict[str, Any]], Any]) -> None:
        """Register callback for groupwide restart notices.

        This allows the service to respond to coordinated restart requests
        from other services in the cluster.

        Args:
            callback: Async function to call when restart notice received.
                      Signature: async def callback(data: dict) -> None
                      The data dict contains: initiator, reason, delay_seconds, timestamp

        Raises:
            RuntimeError: If lifecycle publisher not initialized (no service config)

        Examples:
            >>> async def handle_restart(data):
            ...     print(f"Restart requested by {data['initiator']}: {data['reason']}")
            ...     await asyncio.sleep(data['delay_seconds'])
            ...     # Gracefully shutdown
            >>>
            >>> client.on_group_restart(handle_restart)
        """
        if self._lifecycle is None:
            raise RuntimeError(
                "Lifecycle publisher not initialized. "
                "Provide 'service' config to enable lifecycle features."
            )
        self._lifecycle.on_restart_notice(callback)

    async def __aenter__(self) -> "KrytenClient":
        """Async context manager entry (calls connect)."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit (calls disconnect)."""
        await self.disconnect()

    def on(
        self,
        event_name: str,
        channel: str | None = None,
        domain: str | None = None,
    ) -> Callable[[Callable[[Any], Any]], Callable[[Any], Any]]:
        """Decorator to register event handler.

        Args:
            event_name: CyTube event type (e.g., "chatmsg", "adduser")
            channel: Optional specific channel filter (None = all channels)
            domain: Optional specific domain filter (None = all domains)

        Returns:
            Decorator function

        Examples:
            Handle all chat messages:

            >>> @client.on("chatmsg")
            ... async def on_chat(event: ChatMessageEvent):
            ...     print(event.message)

            Handle chat only from specific channel:

            >>> @client.on("chatmsg", channel="lounge")
            ... async def on_lounge_chat(event: ChatMessageEvent):
            ...     print(f"Lounge: {event.message}")
        """

        def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
            self._handlers[event_name.lower()].append((func, channel, domain))
            self.logger.debug(
                f"Registered handler for event '{event_name}'",
                extra={"channel": channel, "domain": domain},
            )
            return func

        return decorator

    async def run(self) -> None:
        """Start event processing loop (runs until stop() called).

        This method blocks and processes events indefinitely. Call stop()
        from another task or signal handler to exit gracefully.
        """
        if self._running:
            self.logger.warning("Client already running")
            return

        if not self._connected:
            raise KrytenConnectionError("Must connect before running")

        self._running = True
        self._stop_requested = False

        self.logger.info("Event processing loop started")

        try:
            # Keep running until stop requested
            while not self._stop_requested:
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            self.logger.info("Event processing cancelled")
            raise

        finally:
            self._running = False
            self.logger.info("Event processing loop stopped")

    async def stop(self) -> None:
        """Request graceful shutdown of event processing loop."""
        if not self._running:
            self.logger.debug("Client not running, stop is no-op")
            return

        self.logger.info("Requesting stop")
        self._stop_requested = True

        # Wait for run loop to finish (with timeout)
        timeout = 5.0
        start_time = time.time()
        while self._running and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)

        if self._running:
            self.logger.warning("Stop did not complete within timeout")

    async def subscribe(
        self,
        subject: str,
        handler: Callable[[Any], Any],
    ) -> Any:
        """Subscribe to an arbitrary NATS subject.

        This allows subscribing to subjects outside the standard CyTube event
        pattern, such as service discovery, lifecycle events, or custom topics.

        Args:
            subject: NATS subject pattern (supports wildcards like `*` and `>`)
            handler: Async callback function to handle messages.
                    Signature: async def handler(msg) -> None
                    The msg object has .data (bytes), .subject (str), etc.

        Returns:
            Subscription object (can be used to unsubscribe later)

        Raises:
            KrytenConnectionError: If not connected to NATS

        Examples:
            Subscribe to lifecycle events:

            >>> async def on_startup(msg):
            ...     data = json.loads(msg.data.decode())
            ...     print(f"Service started: {data['service']}")
            >>>
            >>> sub = await client.subscribe("kryten.lifecycle.*.startup", on_startup)

            Subscribe to service discovery polls:

            >>> async def on_poll(msg):
            ...     # Re-announce this service
            ...     pass
            >>>
            >>> sub = await client.subscribe("kryten.service.discovery.poll", on_poll)
        """
        if self.__nats is None:
            raise KrytenConnectionError("NATS client not initialized - call connect() first")

        self.logger.debug(f"Subscribing to custom subject: {subject}")

        sub = await self.__nats.subscribe(subject, cb=handler)
        self._subscriptions.append(sub)

        self.logger.info(f"Subscribed to: {subject}")
        return sub

    async def unsubscribe(self, subscription: Any) -> None:
        """Unsubscribe from a NATS subscription.

        Args:
            subscription: Subscription object returned from subscribe()
        """
        try:
            await subscription.unsubscribe()
            if subscription in self._subscriptions:
                self._subscriptions.remove(subscription)
            self.logger.debug("Unsubscribed from subscription")
        except Exception as e:
            self.logger.warning(f"Error unsubscribing: {e}")

    async def publish(
        self,
        subject: str,
        data: bytes | str | dict[str, Any],
    ) -> None:
        """Publish a message to an arbitrary NATS subject.

        This allows publishing to subjects outside the standard command pattern,
        such as lifecycle events or custom inter-service communication.

        Args:
            subject: NATS subject to publish to
            data: Message payload - bytes, string, or dict (will be JSON encoded)

        Raises:
            KrytenConnectionError: If not connected to NATS
            PublishError: If publish fails

        Examples:
            Publish lifecycle event:

            >>> await client.publish(
            ...     "kryten.lifecycle.mybot.startup",
            ...     {"service": "mybot", "version": "1.0.0"}
            ... )

            Publish raw bytes:

            >>> await client.publish("kryten.custom.topic", b"raw data")
        """
        if self.__nats is None:
            raise KrytenConnectionError("NATS client not initialized - call connect() first")

        # Convert data to bytes
        if isinstance(data, dict):
            payload = json.dumps(data).encode("utf-8")
        elif isinstance(data, str):
            payload = data.encode("utf-8")
        else:
            payload = data

        # Validate subject pattern
        if subject.startswith("kryten.command."):
            self.logger.warning(
                f"Use 'send_command()' instead of 'publish()' for sending commands: {subject}"
            )
        elif self.config.service and subject.startswith(f"kryten.events."):
            # Check if event is from this service
            expected_prefix = f"kryten.events.{self.config.service.name}."
            if "cytube" in subject:
                self.logger.warning(
                    f"Publishing to legacy 'kryten.events.cytube.*' subject: {subject}. "
                    "This format is deprecated."
                )
            elif not subject.startswith(expected_prefix): 
                self.logger.warning(
                    f"Publishing event to foreign service subject: {subject}. "
                    f"Expected prefix: {expected_prefix}"
                )

        try:
            await self.__nats.publish(subject, payload)
            self.logger.debug(f"Published to {subject}")
        except Exception as e:
            raise PublishError(f"Failed to publish to {subject}: {e}") from e

    # Command Publishing - Chat

    async def send_command(
        self,
        service: str,
        type: str,
        body: Any,
        domain: str = "cytu.be",
        channel: str = "lounge",
    ) -> None:
        """Send a command to a specific service.

        This is a public wrapper around __send_command for external usage (e.g. by kryten-playlist).
        
        Args:
            service: Target service (e.g., 'robot', 'llm', 'playlist')
            type: Command type identifier
            body: Command payload/body (will be passed as 'args')
            domain: Target domain (default: cytu.be)
            channel: Target channel (default: lounge)

        Raises:
            KrytenConnectionError: If not connected
            PublishError: If publishing fails
        """
        await self.__send_command(service, type, body, domain, channel)

    async def __send_command(
        self,
        service: str,
        type: str,
        body: Any,
        domain: str = "cytu.be",
        channel: str = "lounge",
    ) -> None:
        """Send a command to a specific service.

        Args:
            service: Target service (e.g., 'robot', 'llm', 'playlist')
            type: Command type identifier
            body: Command payload/body (will be passed as 'args')
            domain: Target domain (default: cytu.be)
            channel: Target channel (default: lounge)

        Raises:
            KrytenConnectionError: If not connected
            PublishError: If publishing fails
        """
        if not self._connected or self.__nats is None:
            raise KrytenConnectionError("Not connected to NATS")

        subject = build_command_subject(service)

        # Standard Protocol Format:
        # {
        #   "command": "action_name",
        #   "args": { ... },
        #   "meta": { ... }
        # }
        
        # If body is a primitive (str), wrap it if the command expects it.
        # But 'body' is generic. The protocol says 'args' is a dict.
        # If 'body' is passed as a string (e.g. for 'say'), we need to know the key.
        # However, for generic 'send_command', we should probably expect 'body' to be the 'args' dict
        # or handle it upstream. 
        
        # In `send_chat`, I passed `body=message`. Robot expects `args.message`.
        # So I should change `send_chat` to pass `body={"message": message}`.
        
        args = body if isinstance(body, dict) else {"value": body}

        payload = {
            "command": type,
            "args": args,
            "meta": {
                "source": self.config.service.name if self.config.service else "kryten-client",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "domain": domain,
                "channel": channel,
                "request_id": str(uuid.uuid4())
            },
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            await self.__nats.publish(subject, data)
            self._commands_sent += 1
            self.logger.debug(
                f"Sent command to {service}: {type}",
                extra={"subject": subject, "payload_size": len(data)},
            )
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Failed to send command: {e}", exc_info=True)
            raise PublishError(f"Failed to publish command: {e}") from e

    async def send_chat(
        self,
        channel: str,
        message: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Send chat message to channel.

        Args:
            channel: Channel name
            message: Message text
            domain: Optional domain (uses first configured if None)

        Returns:
            Correlation ID for tracking

        Raises:
            KrytenConnectionError: If not connected
            PublishError: If publish fails

        Examples:
            >>> await client.send_chat("lounge", "Hello!")
        """
        # Ensure domain is set
        target_domain = domain or self.config.channels[0].domain
        
        await self.__send_command(
            service="robot",
            type="say",
            body={"message": message},
            domain=target_domain,
            channel=channel
        )
        return "" # send_command returns None now

    async def send_pm(
        self,
        channel: str,
        username: str,
        message: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Send private message to user."""
        target_domain = domain or self.config.channels[0].domain
        
        await self.__send_command(
            service="robot",
            type="pm",
            body={"to": username, "msg": message}, # Handler expects args dict
            domain=target_domain,
            channel=channel
        )
        return ""

    # Command Publishing - Playlist

    async def add_media(
        self,
        channel: str,
        media_type: str,
        media_id: str,
        *,
        position: str = "end",
        temp: bool = True,
        domain: str | None = None,
    ) -> str:
        """Add media to playlist.

        Args:
            channel: Channel name
            media_type: Media type (e.g., "yt", "vm", "dm")
            media_id: Media ID (YouTube video ID, etc.)
            position: "end" or "next"
            temp: Mark as temporary (default: True)
            domain: Optional domain

        Returns:
            Correlation ID
        
        Examples:
            >>> await client.add_media("lounge", "yt", "dQw4w9WgXcQ")
        """
        return await self.__send_command(
            service="robot",
            type="addvideo", # Updated to match RobotCommandHandler
            body={"type": media_type, "id": media_id, "pos": position, "temp": temp},
            domain=domain,
            channel=channel # Added channel
        )

    async def delete_media(
        self,
        channel: str,
        uid: int,
        *,
        domain: str | None = None,
    ) -> str:
        """Delete media from playlist.

        Args:
            channel: Channel name
            uid: Playlist item unique ID
            domain: Optional domain

        Returns:
            Correlation ID
        """
        return await self._send_command(
            channel=channel,
            action="delete",
            data={"uid": uid},
            domain=domain,
        )

    async def move_media(
        self,
        channel: str,
        uid: int,
        position: int,
        *,
        domain: str | None = None,
    ) -> str:
        """Move media to new position in playlist."""
        return await self._send_command(
            channel=channel,
            action="move",
            data={"from": uid, "after": position},
            domain=domain,
        )

    async def jump_to(
        self,
        channel: str,
        uid: int,
        *,
        domain: str | None = None,
    ) -> str:
        """Jump to specific media in playlist."""
        return await self._send_command(
            channel=channel,
            action="jump",
            data={"uid": uid},
            domain=domain,
        )

    async def clear_playlist(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Clear entire playlist."""
        return await self._send_command(
            channel=channel,
            action="clear",
            data={},
            domain=domain,
        )

    async def shuffle_playlist(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Shuffle playlist order."""
        return await self._send_command(
            channel=channel,
            action="shuffle",
            data={},
            domain=domain,
        )

    async def set_temp(
        self,
        channel: str,
        uid: int,
        is_temp: bool = True,
        *,
        domain: str | None = None,
    ) -> str:
        """Set temporary flag on playlist item."""
        return await self._send_command(
            channel=channel,
            action="settemp",
            data={"uid": uid, "temp": is_temp},
            domain=domain,
        )

    # Command Publishing - Playback

    async def pause(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Pause current media."""
        return await self._send_command(
            channel=channel,
            action="pause",
            data={},
            domain=domain,
        )

    async def play(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Resume playback."""
        return await self._send_command(
            channel=channel,
            action="play",
            data={},
            domain=domain,
        )

    async def seek(
        self,
        channel: str,
        time_seconds: float,
        *,
        domain: str | None = None,
    ) -> str:
        """Seek to specific time in current media."""
        return await self._send_command(
            channel=channel,
            action="seek",
            data={"time": time_seconds},
            domain=domain,
        )

    # Command Publishing - Moderation

    async def kick_user(
        self,
        channel: str,
        username: str,
        reason: str | None = None,
        *,
        domain: str | None = None,
    ) -> str:
        """Kick user from channel."""
        data: dict[str, Any] = {"name": username}
        if reason:
            data["reason"] = reason
        return await self._send_command(
            channel=channel,
            action="kick",
            data=data,
            domain=domain,
        )

    async def ban_user(
        self,
        channel: str,
        username: str,
        reason: str | None = None,
        *,
        domain: str | None = None,
    ) -> str:
        """Ban user from channel."""
        data: dict[str, Any] = {"name": username}
        if reason:
            data["reason"] = reason
        return await self._send_command(
            channel=channel,
            action="ban",
            data=data,
            domain=domain,
        )

    async def voteskip(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Vote to skip current media."""
        return await self._send_command(
            channel=channel,
            action="voteskip",
            data={},
            domain=domain,
        )

    async def assign_leader(
        self,
        channel: str,
        username: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Assign or remove leader status.

        Leader has temporary elevated permissions (rank 1.5) for playlist
        and playback control. Pass empty string to remove leader.

        Requires rank 2+ (moderator).

        Args:
            channel: Channel name
            username: Username to give leader, or "" to remove leader
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.assign_leader("lounge", "alice")
            >>> await client.assign_leader("lounge", "")  # Remove leader
        """
        return await self._send_command(
            channel=channel,
            action="assignLeader",
            data={"name": username},
            domain=domain,
        )

    async def mute_user(
        self,
        channel: str,
        username: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Mute user (prevents them from chatting).

        The muted user will be notified and cannot send messages.

        Requires rank 2+ (moderator).

        Args:
            channel: Channel name
            username: Username to mute
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.mute_user("lounge", "spammer")
        """
        return await self._send_command(
            channel=channel,
            action="chat",
            data={"message": f"/mute {username}"},
            domain=domain,
        )

    async def shadow_mute_user(
        self,
        channel: str,
        username: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Shadow mute user (they can chat but only mods see it).

        Shadow muted users don't know they're muted - their messages
        appear normal to them but are only visible to themselves and
        moderators. Useful for handling subtle trolls.

        Requires rank 2+ (moderator).

        Args:
            channel: Channel name
            username: Username to shadow mute
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.shadow_mute_user("lounge", "subtle_troll")
        """
        return await self._send_command(
            channel=channel,
            action="chat",
            data={"message": f"/smute {username}"},
            domain=domain,
        )

    async def unmute_user(
        self,
        channel: str,
        username: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Unmute user (removes both regular and shadow mute).

        Requires rank 2+ (moderator).

        Args:
            channel: Channel name
            username: Username to unmute
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.unmute_user("lounge", "reformed_user")
        """
        return await self._send_command(
            channel=channel,
            action="chat",
            data={"message": f"/unmute {username}"},
            domain=domain,
        )

    async def play_next(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Skip to next video in playlist.

        Unlike voteskip, this immediately skips without voting.

        Requires rank 2+ (moderator) or leader status.

        Args:
            channel: Channel name
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.play_next("lounge")
        """
        return await self._send_command(
            channel=channel,
            action="playNext",
            data={},
            domain=domain,
        )

    # Phase 2: Admin Functions (Rank 3+)

    async def set_motd(
        self,
        channel: str,
        motd: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Set channel message of the day (MOTD).

        Requires rank 3+ (admin).

        Args:
            channel: Channel name
            motd: Message of the day HTML content
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.set_motd("lounge", "<h1>Welcome!</h1>")
        """
        return await self._send_command(
            channel=channel,
            action="setMotd",
            data={"motd": motd},
            domain=domain,
        )

    async def set_channel_css(
        self,
        channel: str,
        css: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Set channel custom CSS.

        Requires rank 3+ (admin).
        CyTube has a 20KB limit on CSS content.

        Args:
            channel: Channel name
            css: CSS content (max ~20KB)
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> css_content = "body { background: #000; }"
            >>> await client.set_channel_css("lounge", css_content)
        """
        return await self._send_command(
            channel=channel,
            action="setChannelCSS",
            data={"css": css},
            domain=domain,
        )

    async def set_channel_js(
        self,
        channel: str,
        js: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Set channel custom JavaScript.

        Requires rank 3+ (admin).
        CyTube has a 20KB limit on JS content.

        Args:
            channel: Channel name
            js: JavaScript content (max ~20KB)
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> js_content = "console.log('Hello');"
            >>> await client.set_channel_js("lounge", js_content)
        """
        return await self._send_command(
            channel=channel,
            action="setChannelJS",
            data={"js": js},
            domain=domain,
        )

    async def set_options(
        self,
        channel: str,
        options: dict[str, Any],
        *,
        domain: str | None = None,
    ) -> str:
        """Update channel options.

        Requires rank 3+ (admin).

        Common options include:
        - allow_voteskip: bool - Enable voteskip
        - voteskip_ratio: float - Ratio needed to skip (0.0-1.0)
        - afk_timeout: int - AFK timeout in seconds
        - pagetitle: str - Channel page title
        - maxlength: int - Max video length in seconds (0 = unlimited)
        - externalcss: str - External CSS URL
        - externaljs: str - External JS URL
        - chat_antiflood: bool - Enable chat antiflood
        - chat_antiflood_params: dict - Antiflood parameters
        - show_public: bool - Show in public channel list
        - enable_link_regex: bool - Enable link filtering
        - password: str - Channel password (empty = no password)

        Args:
            channel: Channel name
            options: Dictionary of option key-value pairs
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> opts = {"allow_voteskip": True, "voteskip_ratio": 0.5}
            >>> await client.set_options("lounge", opts)
        """
        return await self._send_command(
            channel=channel,
            action="setOptions",
            data={"options": options},
            domain=domain,
        )

    async def set_permissions(
        self,
        channel: str,
        permissions: dict[str, int],
        *,
        domain: str | None = None,
    ) -> str:
        """Update channel permissions.

        Requires rank 3+ (admin).

        Permissions map actions to minimum rank required.
        Common permission keys:
        - seeplaylist, playlistadd, playlistnext, playlistmove
        - playlistdelete, playlistjump, playlistshuffle, playlistclear
        - pollctl, pollvote, viewhiddenpoll, voteskip
        - oekaki, shout, kick, ban, mute, settemp
        - filteradd, filteredit, filterdelete
        - emoteupdate, emotedelete
        - exceedmaxlength, addnontemp

        Args:
            channel: Channel name
            permissions: Dictionary mapping permission names to rank levels
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> perms = {"kick": 2, "ban": 3}
            >>> await client.set_permissions("lounge", perms)
        """
        return await self._send_command(
            channel=channel,
            action="setPermissions",
            data={"permissions": permissions},
            domain=domain,
        )

    async def update_emote(
        self,
        channel: str,
        name: str,
        image: str,
        source: str = "imgur",
        *,
        domain: str | None = None,
    ) -> str:
        """Add or update a channel emote.

        Requires rank 3+ (admin).

        Args:
            channel: Channel name
            name: Emote name (without colons, e.g. "Kappa")
            image: Image URL or ID (depends on source)
            source: Image source ("imgur", "url", etc.)
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.update_emote("lounge", "CustomEmote", "abc123", "imgur")
        """
        return await self._send_command(
            channel=channel,
            action="updateEmote",
            data={"name": name, "image": image, "source": source},
            domain=domain,
        )

    async def remove_emote(
        self,
        channel: str,
        name: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Remove a channel emote.

        Requires rank 3+ (admin).

        Args:
            channel: Channel name
            name: Emote name to remove
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.remove_emote("lounge", "CustomEmote")
        """
        return await self._send_command(
            channel=channel,
            action="removeEmote",
            data={"name": name},
            domain=domain,
        )

    async def add_filter(
        self,
        channel: str,
        name: str,
        source: str,
        flags: str,
        replace: str,
        filterlinks: bool = False,
        active: bool = True,
        *,
        domain: str | None = None,
    ) -> str:
        """Add a chat filter.

        Requires rank 3+ (admin).

        Args:
            channel: Channel name
            name: Filter name
            source: Regex pattern to match
            flags: Regex flags (e.g., "gi" for global case-insensitive)
            replace: Replacement text
            filterlinks: Whether to filter links
            active: Whether filter is active
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.add_filter(
            ...     "lounge", "badword", r"\\bbad\\b", "gi", "***"
            ... )
        """
        return await self._send_command(
            channel=channel,
            action="addFilter",
            data={
                "name": name,
                "source": source,
                "flags": flags,
                "replace": replace,
                "filterlinks": filterlinks,
                "active": active,
            },
            domain=domain,
        )

    async def update_filter(
        self,
        channel: str,
        name: str,
        source: str,
        flags: str,
        replace: str,
        filterlinks: bool = False,
        active: bool = True,
        *,
        domain: str | None = None,
    ) -> str:
        """Update an existing chat filter.

        Requires rank 3+ (admin).

        Args:
            channel: Channel name
            name: Filter name
            source: Regex pattern to match
            flags: Regex flags (e.g., "gi" for global case-insensitive)
            replace: Replacement text
            filterlinks: Whether to filter links
            active: Whether filter is active
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.update_filter(
            ...     "lounge", "badword", r"\\bbad\\b", "gi", "###"
            ... )
        """
        return await self._send_command(
            channel=channel,
            action="updateFilter",
            data={
                "name": name,
                "source": source,
                "flags": flags,
                "replace": replace,
                "filterlinks": filterlinks,
                "active": active,
            },
            domain=domain,
        )

    async def remove_filter(
        self,
        channel: str,
        name: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Remove a chat filter.

        Requires rank 3+ (admin).

        Args:
            channel: Channel name
            name: Filter name to remove
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.remove_filter("lounge", "badword")
        """
        return await self._send_command(
            channel=channel,
            action="removeFilter",
            data={"name": name},
            domain=domain,
        )

    # Phase 3: Advanced Admin Functions (Rank 2-4+)

    async def new_poll(
        self,
        channel: str,
        title: str,
        options: list[str],
        obscured: bool = False,
        timeout: int = 0,
        *,
        domain: str | None = None,
    ) -> str:
        """Create a new poll.

        Requires rank 2+ (moderator).

        Args:
            channel: Channel name
            title: Poll question
            options: List of poll options
            obscured: Whether to hide results until poll closes
            timeout: Auto-close timeout in seconds (0 = no timeout)
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.new_poll(
            ...     "lounge", "Favorite color?", ["Red", "Blue", "Green"]
            ... )
        """
        return await self._send_command(
            channel=channel,
            action="newPoll",
            data={
                "title": title,
                "opts": options,
                "obscured": obscured,
                "timeout": timeout,
            },
            domain=domain,
        )

    async def vote(
        self,
        channel: str,
        option: int,
        *,
        domain: str | None = None,
    ) -> str:
        """Vote in the active poll.

        Requires rank 0+ (guest).

        Args:
            channel: Channel name
            option: Option index to vote for (0-based)
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.vote("lounge", 0)  # Vote for first option
        """
        return await self._send_command(
            channel=channel,
            action="vote",
            data={"option": option},
            domain=domain,
        )

    async def close_poll(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Close the active poll.

        Requires rank 2+ (moderator).

        Args:
            channel: Channel name
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.close_poll("lounge")
        """
        return await self._send_command(
            channel=channel,
            action="closePoll",
            data={},
            domain=domain,
        )

    async def set_channel_rank(
        self,
        channel: str,
        username: str,
        rank: int,
        *,
        domain: str | None = None,
    ) -> str:
        """Set a user's permanent channel rank.

        Requires rank 4+ (owner).

        Args:
            channel: Channel name
            username: User to modify
            rank: Rank level (0-4+)
                0: Guest
                1: Registered
                2: Moderator
                3: Admin
                4+: Owner
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.set_channel_rank("lounge", "Alice", 2)  # Make moderator
        """
        return await self._send_command(
            channel=channel,
            action="setChannelRank",
            data={"username": username, "rank": rank},
            domain=domain,
        )

    async def request_channel_ranks(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Request list of users with elevated channel ranks.

        Requires rank 4+ (owner).
        Server will respond with channelRankFail or channelRanks event.

        Args:
            channel: Channel name
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.request_channel_ranks("lounge")
        """
        return await self._send_command(
            channel=channel,
            action="requestChannelRanks",
            data={},
            domain=domain,
        )

    async def request_banlist(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Request channel ban list.

        Requires rank 3+ (admin).
        Server will respond with banlist event.

        Args:
            channel: Channel name
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.request_banlist("lounge")
        """
        return await self._send_command(
            channel=channel,
            action="requestBanlist",
            data={},
            domain=domain,
        )

    async def unban(
        self,
        channel: str,
        ban_id: int,
        *,
        domain: str | None = None,
    ) -> str:
        """Remove a ban.

        Requires rank 3+ (admin).

        Args:
            channel: Channel name
            ban_id: ID of the ban to remove (from banlist event)
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.unban("lounge", 12345)
        """
        return await self._send_command(
            channel=channel,
            action="unban",
            data={"id": ban_id},
            domain=domain,
        )

    async def read_chan_log(
        self,
        channel: str,
        count: int = 100,
        *,
        domain: str | None = None,
    ) -> str:
        """Request channel event log.

        Requires rank 3+ (admin).
        Server will respond with readChanLog event.

        Args:
            channel: Channel name
            count: Number of log entries to retrieve (default 100)
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.read_chan_log("lounge", 50)
        """
        return await self._send_command(
            channel=channel,
            action="readChanLog",
            data={"count": count},
            domain=domain,
        )

    async def search_library(
        self,
        channel: str,
        query: str,
        source: str = "library",
        *,
        domain: str | None = None,
    ) -> str:
        """Search channel library.

        Requires appropriate rank based on channel permissions.
        Server will respond with searchResults event.

        Args:
            channel: Channel name
            query: Search query
            source: Search source ("library" or media provider like "yt", "vm")
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.search_library("lounge", "funny video")
        """
        return await self._send_command(
            channel=channel,
            action="searchMedia",
            data={"query": query, "source": source},
            domain=domain,
        )

    async def delete_from_library(
        self,
        channel: str,
        media_id: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Delete item from channel library.

        Requires rank 2+ (moderator).

        Args:
            channel: Channel name
            media_id: ID of media item to delete
            domain: Optional domain override

        Returns:
            Message ID of the published command

        Example:
            >>> await client.delete_from_library("lounge", "yt:abc123")
        """
        return await self._send_command(
            channel=channel,
            action="uncache",
            data={"id": media_id},
            domain=domain,
        )

    # Convenience Methods with Auto-Rank Checking

    async def _check_rank(
        self,
        channel: str,
        required_rank: int,
        operation: str,
        *,
        domain: str | None = None,
        timeout: float = 2.0,
    ) -> bool:
        """Check if bot has sufficient rank for an operation.

        Args:
            channel: Channel name
            required_rank: Minimum rank required
            operation: Description of operation (for error messages)
            domain: Optional domain override
            timeout: Request timeout

        Returns:
            True if rank is sufficient, False otherwise

        Raises:
            KrytenConnectionError: If not connected
        """
        result = await self.get_user_level(channel, domain=domain, timeout=timeout)

        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            raise KrytenConnectionError(f"Failed to check rank: {error_msg}")

        current_rank = result.get("rank", 0)
        if current_rank < required_rank:
            return False

        return True

    async def safe_assign_leader(
        self,
        channel: str,
        username: str,
        *,
        domain: str | None = None,
        check_rank: bool = True,
        timeout: float = 2.0,
    ) -> dict[str, Any]:
        """Assign leader with automatic rank checking.

        Requires rank 2+ (moderator).

        Args:
            channel: Channel name
            username: User to give/remove leader status
            domain: Optional domain override
            check_rank: Whether to check rank before executing (default: True)
            timeout: Rank check timeout

        Returns:
            Dictionary with:
                - success (bool): Whether operation succeeded
                - message_id (str): Command message ID if successful
                - error (str): Error description if failed
                - rank (int): Current bot rank

        Example:
            >>> result = await client.safe_assign_leader("lounge", "TrustedUser")
            >>> if result["success"]:
            ...     print(f"Leader assigned: {result['message_id']}")
            >>> else:
            ...     print(f"Failed: {result['error']}")
        """
        if check_rank:
            try:
                has_rank = await self._check_rank(
                    channel, 2, "assign leader", domain=domain, timeout=timeout
                )
                if not has_rank:
                    level = await self.get_user_level(channel, domain=domain, timeout=timeout)
                    return {
                        "success": False,
                        "error": f"Insufficient rank: need 2+, have {level.get('rank', 0)}",
                        "rank": level.get("rank", 0),
                    }
            except Exception as e:
                return {"success": False, "error": f"Rank check failed: {e}", "rank": 0}

        try:
            msg_id = await self.assign_leader(channel, username, domain=domain)
            return {"success": True, "message_id": msg_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def safe_set_motd(
        self,
        channel: str,
        motd: str,
        *,
        domain: str | None = None,
        check_rank: bool = True,
        timeout: float = 2.0,
    ) -> dict[str, Any]:
        """Set MOTD with automatic rank checking.

        Requires rank 3+ (admin).

        Args:
            channel: Channel name
            motd: Message of the day HTML content
            domain: Optional domain override
            check_rank: Whether to check rank before executing (default: True)
            timeout: Rank check timeout

        Returns:
            Dictionary with success status, message_id or error

        Example:
            >>> result = await client.safe_set_motd("lounge", "<h1>Welcome!</h1>")
            >>> if not result["success"]:
            ...     print(f"Cannot set MOTD: {result['error']}")
        """
        if check_rank:
            try:
                has_rank = await self._check_rank(
                    channel, 3, "set MOTD", domain=domain, timeout=timeout
                )
                if not has_rank:
                    level = await self.get_user_level(channel, domain=domain, timeout=timeout)
                    return {
                        "success": False,
                        "error": f"Insufficient rank: need 3+, have {level.get('rank', 0)}",
                        "rank": level.get("rank", 0),
                    }
            except Exception as e:
                return {"success": False, "error": f"Rank check failed: {e}", "rank": 0}

        try:
            msg_id = await self.set_motd(channel, motd, domain=domain)
            return {"success": True, "message_id": msg_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def safe_set_channel_rank(
        self,
        channel: str,
        username: str,
        rank: int,
        *,
        domain: str | None = None,
        check_rank: bool = True,
        timeout: float = 2.0,
    ) -> dict[str, Any]:
        """Set channel rank with automatic rank checking.

        Requires rank 4+ (owner).

        Args:
            channel: Channel name
            username: User to modify
            rank: Target rank (0-4+)
            domain: Optional domain override
            check_rank: Whether to check rank before executing (default: True)
            timeout: Rank check timeout

        Returns:
            Dictionary with success status, message_id or error

        Example:
            >>> result = await client.safe_set_channel_rank("lounge", "Alice", 2)
            >>> if result["success"]:
            ...     print("User promoted to moderator")
            >>> else:
            ...     print(f"Failed: {result['error']}")
        """
        if check_rank:
            try:
                has_rank = await self._check_rank(
                    channel, 4, "set channel rank", domain=domain, timeout=timeout
                )
                if not has_rank:
                    level = await self.get_user_level(channel, domain=domain, timeout=timeout)
                    return {
                        "success": False,
                        "error": f"Insufficient rank: need 4+, have {level.get('rank', 0)}",
                        "rank": level.get("rank", 0),
                    }
            except Exception as e:
                return {"success": False, "error": f"Rank check failed: {e}", "rank": 0}

        try:
            msg_id = await self.set_channel_rank(channel, username, rank, domain=domain)
            return {"success": True, "message_id": msg_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def safe_update_emote(
        self,
        channel: str,
        name: str,
        image: str,
        source: str = "imgur",
        *,
        domain: str | None = None,
        check_rank: bool = True,
        timeout: float = 2.0,
    ) -> dict[str, Any]:
        """Update emote with automatic rank checking.

        Requires rank 3+ (admin).

        Args:
            channel: Channel name
            name: Emote name
            image: Image URL or ID
            source: Image source
            domain: Optional domain override
            check_rank: Whether to check rank before executing (default: True)
            timeout: Rank check timeout

        Returns:
            Dictionary with success status, message_id or error

        Example:
            >>> result = await client.safe_update_emote("lounge", "Kappa", "abc123")
            >>> if result["success"]:
            ...     print("Emote added successfully")
        """
        if check_rank:
            try:
                has_rank = await self._check_rank(
                    channel, 3, "update emote", domain=domain, timeout=timeout
                )
                if not has_rank:
                    level = await self.get_user_level(channel, domain=domain, timeout=timeout)
                    return {
                        "success": False,
                        "error": f"Insufficient rank: need 3+, have {level.get('rank', 0)}",
                        "rank": level.get("rank", 0),
                    }
            except Exception as e:
                return {"success": False, "error": f"Rank check failed: {e}", "rank": 0}

        try:
            msg_id = await self.update_emote(channel, name, image, source, domain=domain)
            return {"success": True, "message_id": msg_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def safe_add_filter(
        self,
        channel: str,
        name: str,
        source: str,
        flags: str,
        replace: str,
        filterlinks: bool = False,
        active: bool = True,
        *,
        domain: str | None = None,
        check_rank: bool = True,
        timeout: float = 2.0,
    ) -> dict[str, Any]:
        """Add chat filter with automatic rank checking.

        Requires rank 3+ (admin).

        Args:
            channel: Channel name
            name: Filter name
            source: Regex pattern
            flags: Regex flags
            replace: Replacement text
            filterlinks: Whether to filter links
            active: Whether filter is active
            domain: Optional domain override
            check_rank: Whether to check rank before executing (default: True)
            timeout: Rank check timeout

        Returns:
            Dictionary with success status, message_id or error

        Example:
            >>> result = await client.safe_add_filter(
            ...     "lounge", "profanity", r"\\bbad\\b", "gi", "***"
            ... )
        """
        if check_rank:
            try:
                has_rank = await self._check_rank(
                    channel, 3, "add filter", domain=domain, timeout=timeout
                )
                if not has_rank:
                    level = await self.get_user_level(channel, domain=domain, timeout=timeout)
                    return {
                        "success": False,
                        "error": f"Insufficient rank: need 3+, have {level.get('rank', 0)}",
                        "rank": level.get("rank", 0),
                    }
            except Exception as e:
                return {"success": False, "error": f"Rank check failed: {e}", "rank": 0}

        try:
            msg_id = await self.add_filter(
                channel, name, source, flags, replace, filterlinks, active, domain=domain
            )
            return {"success": True, "message_id": msg_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def safe_set_options(
        self,
        channel: str,
        options: dict[str, Any],
        *,
        domain: str | None = None,
        check_rank: bool = True,
        timeout: float = 2.0,
    ) -> dict[str, Any]:
        """Set channel options with automatic rank checking.

        Requires rank 3+ (admin).

        Args:
            channel: Channel name
            options: Dictionary of option key-value pairs
            domain: Optional domain override
            check_rank: Whether to check rank before executing (default: True)
            timeout: Rank check timeout

        Returns:
            Dictionary with success status, message_id or error

        Example:
            >>> opts = {"allow_voteskip": True, "voteskip_ratio": 0.5}
            >>> result = await client.safe_set_options("lounge", opts)
        """
        if check_rank:
            try:
                has_rank = await self._check_rank(
                    channel, 3, "set options", domain=domain, timeout=timeout
                )
                if not has_rank:
                    level = await self.get_user_level(channel, domain=domain, timeout=timeout)
                    return {
                        "success": False,
                        "error": f"Insufficient rank: need 3+, have {level.get('rank', 0)}",
                        "rank": level.get("rank", 0),
                    }
            except Exception as e:
                return {"success": False, "error": f"Rank check failed: {e}", "rank": 0}

        try:
            msg_id = await self.set_options(channel, options, domain=domain)
            return {"success": True, "message_id": msg_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Status & Health

    def health(self) -> HealthStatus:
        """Get current health status and metrics.

        Returns:
            HealthStatus model with connection state and statistics
        """
        uptime = 0.0
        if self._connection_time:
            uptime = time.time() - self._connection_time

        avg_latency = 0.0
        if self._event_latencies:
            avg_latency = sum(self._event_latencies) / len(self._event_latencies) * 1000

        state = "connected" if self._connected else "disconnected"
        if not self._connected and self._connection_time:
            state = "connecting"

        return HealthStatus(
            connected=self._connected,
            state=state,
            uptime_seconds=uptime,
            channels=[f"{c.domain}/{c.channel}" for c in self.config.channels],
            events_received=self._events_received,
            commands_sent=self._commands_sent,
            errors=self._errors,
            avg_event_latency_ms=avg_latency,
            last_event_time=self._last_event_time,
            handlers_registered=sum(len(handlers) for handlers in self._handlers.values()),
        )

    @property
    def is_connected(self) -> bool:
        """Check if NATS connection is active."""
        return self._connected

    @property
    def channels(self) -> list[ChannelInfo]:
        """Get list of configured channels."""
        return [
            ChannelInfo(
                domain=c.domain,
                channel=c.channel,
                subscribed=self._connected,
                events_received=self._channel_metrics.get(f"{c.domain}/{c.channel}", 0),
            )
            for c in self.config.channels
        ]

    # Private methods

    async def _setup_subscriptions(self) -> None:
        """Set up NATS subscriptions for all configured channels."""
        if self._nats is None:
            raise KrytenConnectionError("NATS client not initialized")

        for channel_config in self.config.channels:
            # Subscribe to all events from this channel using wildcard
            # Format: kryten.events.cytube.{channel}.>
            # Channel is normalized (lowercase, dots removed)
            channel_normalized = channel_config.channel.lower().replace(".", "")
            subject = f"{SUBJECT_PREFIX}.cytube.{channel_normalized}.>"

            self.logger.info(f"Subscribing to: {subject}")

            sub = await self._nats.subscribe(subject, cb=self._on_message)
            self._subscriptions.append(sub)

    async def _on_message(self, msg: Any) -> None:
        """Handle incoming NATS message."""
        start_time = time.time()

        try:
            # Parse message
            data = json.loads(msg.data.decode("utf-8"))
            raw_event = RawEvent(**data)

            self._events_received += 1
            self._last_event_time = datetime.now(timezone.utc)
            self._channel_metrics[f"{raw_event.domain}/{raw_event.channel}"] += 1

            # Find matching handlers
            event_name = raw_event.event_name.lower()
            handlers = self._handlers.get(event_name, [])

            # Debug logging
            self.logger.debug(
                f"Received NATS message: {event_name} from {raw_event.domain}/{raw_event.channel}, "
                f"found {len(handlers)} handlers"
            )

            # Invoke handlers concurrently
            tasks = []
            for handler, channel_filter, domain_filter in handlers:
                self.logger.debug(
                    f"Checking handler {handler.__name__}: channel_filter={channel_filter}, "
                    f"domain_filter={domain_filter}, event.channel={raw_event.channel}, "
                    f"event.domain={raw_event.domain}"
                )
                # Check filters
                if channel_filter and channel_filter != raw_event.channel:
                    self.logger.debug(f"Handler filtered out by channel: {channel_filter} != {raw_event.channel}")
                    continue
                if domain_filter and domain_filter != raw_event.domain:
                    self.logger.debug(f"Handler filtered out by domain: {domain_filter} != {raw_event.domain}")
                    continue

                # Create task for handler
                self.logger.debug(f"Creating task for handler: {handler.__name__}")
                task = asyncio.create_task(self._invoke_handler(handler, raw_event))
                tasks.append(task)

            # Wait for all handlers
            self.logger.debug(f"Waiting for {len(tasks)} handler tasks")
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                # Log any exceptions from gather
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        self.logger.error(f"Handler task {i} raised: {result}", exc_info=result)

            # Track latency
            elapsed = time.time() - start_time
            self._event_latencies.append(elapsed)
            # Keep only last 1000 latencies
            if len(self._event_latencies) > 1000:
                self._event_latencies = self._event_latencies[-1000:]

        except Exception as e:
            self._errors += 1
            self.logger.error(f"Error processing message: {e}", exc_info=True)

    def _convert_to_typed_event(self, raw_event: RawEvent) -> Any:
        """Convert RawEvent to specific typed event based on event_name.

        Args:
            raw_event: Raw event from NATS

        Returns:
            Typed event object (ChatMessageEvent, UserJoinEvent, etc.) or RawEvent if no conversion available

        Note:
            Falls back to returning the RawEvent if conversion fails or event type is unknown.
        """
        event_name = raw_event.event_name.lower()
        payload = raw_event.payload

        # Skip conversion if payload is not a dictionary
        if not isinstance(payload, dict):
            return raw_event

        try:
            if event_name == "chatmsg":
                # Extract user info from nested structure or flat structure
                if "user" in payload and isinstance(payload["user"], dict):
                    username = payload["user"].get("name", "")
                    rank = payload["user"].get("rank", 0)
                else:
                    username = payload.get("username", "")
                    rank = payload.get("rank", 0)

                # Message field can be 'msg' or 'message'
                message = payload.get("msg", payload.get("message", ""))

                # Time is Unix timestamp in milliseconds
                time_ms = payload.get("time", 0)
                timestamp = datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc) if time_ms else raw_event.timestamp

                return ChatMessageEvent(
                    username=username,
                    message=message,
                    timestamp=timestamp,
                    rank=rank,
                    channel=raw_event.channel,
                    domain=raw_event.domain,
                    correlation_id=raw_event.correlation_id,
                )

            elif event_name == "pm":
                # PM events have similar structure to chat messages
                if "user" in payload and isinstance(payload["user"], dict):
                    username = payload["user"].get("name", "")
                    rank = payload["user"].get("rank", 0)
                else:
                    username = payload.get("username", "")
                    rank = payload.get("rank", 0)

                message = payload.get("msg", payload.get("message", ""))
                time_ms = payload.get("time", 0)
                timestamp = datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc) if time_ms else raw_event.timestamp

                return ChatMessageEvent(
                    username=username,
                    message=message,
                    timestamp=timestamp,
                    rank=rank,
                    channel=raw_event.channel,
                    domain=raw_event.domain,
                    correlation_id=raw_event.correlation_id,
                )

            elif event_name == "adduser":
                username = payload.get("name", "")
                rank = payload.get("rank", 0)
                time_ms = payload.get("time", 0)
                timestamp = datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc) if time_ms else raw_event.timestamp

                return UserJoinEvent(
                    username=username,
                    rank=rank,
                    timestamp=timestamp,
                    channel=raw_event.channel,
                    domain=raw_event.domain,
                    correlation_id=raw_event.correlation_id,
                )

            elif event_name == "userleave":
                username = payload.get("name", "")
                time_ms = payload.get("time", 0)
                timestamp = datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc) if time_ms else raw_event.timestamp

                return UserLeaveEvent(
                    username=username,
                    timestamp=timestamp,
                    channel=raw_event.channel,
                    domain=raw_event.domain,
                    correlation_id=raw_event.correlation_id,
                )

            elif event_name == "changemedia":
                media_type = payload.get("type", "")
                media_id = payload.get("id", "")
                title = payload.get("title", "")
                duration = payload.get("seconds", 0)
                uid = payload.get("uid", 0)
                time_ms = payload.get("time", 0)
                timestamp = datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc) if time_ms else raw_event.timestamp

                return ChangeMediaEvent(
                    media_type=media_type,
                    media_id=media_id,
                    title=title,
                    duration=duration,
                    uid=uid,
                    timestamp=timestamp,
                    channel=raw_event.channel,
                    domain=raw_event.domain,
                    correlation_id=raw_event.correlation_id,
                )

            elif event_name == "playlist":
                action = payload.get("action", "")
                uid = payload.get("uid")
                time_ms = payload.get("time", 0)
                timestamp = datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc) if time_ms else raw_event.timestamp

                return PlaylistUpdateEvent(
                    action=action,
                    uid=uid,
                    timestamp=timestamp,
                    channel=raw_event.channel,
                    domain=raw_event.domain,
                    correlation_id=raw_event.correlation_id,
                )

        except Exception as e:
            self.logger.warning(
                f"Failed to convert {event_name} to typed event: {e}. Falling back to RawEvent.",
                exc_info=True,
            )

        # Default: return raw event if conversion fails or event type unknown
        return raw_event

    async def _invoke_handler(
        self, handler: Callable[[Any], Any], event: RawEvent
    ) -> None:
        """Invoke event handler with timeout."""
        try:
            # Convert RawEvent to specific typed event based on event_name
            typed_event = self._convert_to_typed_event(event)
            await asyncio.wait_for(
                handler(typed_event),
                timeout=self.config.handler_timeout,
            )
        except asyncio.TimeoutError:
            self._errors += 1
            self.logger.error(
                f"Handler {handler.__name__} timed out",
                extra={"timeout": self.config.handler_timeout},
            )
        except Exception as e:
            self._errors += 1
            self.logger.error(
                f"Handler {handler.__name__} raised exception: {e}",
                exc_info=True,
            )

    async def _send_command(
        self,
        channel: str,
        action: str,
        data: dict[str, Any],
        domain: str | None = None,
    ) -> str:
        """Send command to NATS.

        Args:
            channel: Channel name
            action: Command action
            data: Command data
            domain: Optional domain

        Returns:
            Correlation ID

        Raises:
            KrytenConnectionError: If not connected
            PublishError: If publish fails
        """
        if not self._connected or self._nats is None:
            raise KrytenConnectionError("Not connected to NATS")

        # Resolve domain (use first configured channel's domain if not specified)
        resolved_domain = domain or self.config.channels[0].domain

        # Generate correlation ID
        correlation_id = str(uuid.uuid4())

        # Build subject with domain
        subject = build_command_subject(resolved_domain, channel, action)

        # Build payload
        payload = {
            "action": action,
            "data": data,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Publish with retry
        for attempt in range(self.config.retry_attempts + 1):
            try:
                await self._nats.publish(subject, json.dumps(payload).encode("utf-8"))

                self._commands_sent += 1

                self.logger.info(
                    f"Published command '{action}' to channel '{channel}'",
                    extra={
                        "subject": subject,
                        "correlation_id": correlation_id,
                    },
                )

                return correlation_id

            except Exception as e:
                if attempt < self.config.retry_attempts:
                    delay = self.config.retry_delay * (2**attempt)
                    self.logger.warning(
                        f"Publish failed (attempt {attempt + 1}/{self.config.retry_attempts + 1}), "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    self._errors += 1
                    self.logger.error(f"Publish failed permanently: {e}", exc_info=True)
                    raise PublishError(f"Failed to publish command: {e}") from e

        # Should not reach here
        raise PublishError("Failed to publish command after retries")

    # NATS callbacks

    async def _on_error(self, e: Exception) -> None:
        """Handle NATS error.
        
        Connection-related errors during reconnection are expected and logged
        at WARNING level. Other errors are logged at ERROR with full traceback.
        """
        self._errors += 1
        
        # Check if this is a connection-related error (expected during reconnection)
        error_str = str(e).lower()
        is_connection_error = any(term in error_str for term in [
            "connection refused",
            "connection reset",
            "connection closed",
            "timed out",
            "timeout",
            "winerror 1225",  # Windows connection refused
            "errno 111",      # Linux connection refused
            "errno 104",      # Linux connection reset
        ])
        
        if is_connection_error:
            # Expected during reconnection attempts - log without traceback
            self.logger.warning(f"NATS connection error (will retry): {e}")
        else:
            # Unexpected error - log with full traceback
            self.logger.error(f"NATS error: {e}", exc_info=True)

    async def _on_disconnected(self) -> None:
        """Handle NATS disconnection."""
        self.logger.warning("Disconnected from NATS")

    async def _on_reconnected(self) -> None:
        """Handle NATS reconnection."""
        self.logger.info("Reconnected to NATS")

    async def _on_closed(self) -> None:
        """Handle NATS connection closed."""
        self.logger.info("NATS connection closed")
        self._connected = False

    # User & Profile Query Methods

    async def get_user(
        self,
        channel: str,
        username: str,
        *,
        domain: str | None = None,
        timeout: float = 2.0,
    ) -> dict[str, Any] | None:
        """Get user data from channel state.

        Queries Kryten-Robot for user information including rank, profile, etc.

        Args:
            channel: Channel name
            username: Username to look up
            domain: Optional domain (uses first configured if None)
            timeout: Request timeout in seconds (default: 2.0)

        Returns:
            User dictionary with name, rank, profile, meta fields, or None if not found

        Example:
            >>> user = await client.get_user("lounge", "Alice")
            >>> if user:
            ...     print(f"Rank: {user['rank']}")
            ...     profile = user.get('profile', {})
            ...     print(f"Avatar: {profile.get('image')}")
        """
        if not self._nats:
            raise KrytenConnectionError("Not connected to NATS")

        # Resolve domain
        if domain is None:
            if not self.config.channels:
                raise KrytenValidationError("No channels configured")
            domain = self.config.channels[0].domain

        # Build unified command request
        subject = "kryten.robot.command"
        request = {
            "service": "robot",
            "command": "state.user",
            "username": username
        }

        try:
            response = await self._nats.request(
                subject=subject,
                payload=json.dumps(request).encode(),
                timeout=timeout
            )

            result = json.loads(response.data.decode("utf-8"))
            if result.get("success"):
                return result.get("data", {}).get("user")
            else:
                self.logger.warning(f"User query failed: {result.get('error')}")
                return None

        except asyncio.TimeoutError:
            self.logger.warning(f"User query timed out for {username} in {domain}/{channel}")
            return None
        except Exception as e:
            self.logger.error(f"Error querying user: {e}", exc_info=True)
            return None

    async def get_user_profile(
        self,
        channel: str,
        username: str,
        *,
        domain: str | None = None,
        timeout: float = 2.0,
    ) -> dict[str, Any] | None:
        """Get user's profile (avatar and bio).

        Args:
            channel: Channel name
            username: Username to look up
            domain: Optional domain (uses first configured if None)
            timeout: Request timeout in seconds (default: 2.0)

        Returns:
            Profile dictionary with 'image' and 'text' keys, or None if not found

        Example:
            >>> profile = await client.get_user_profile("lounge", "Alice")
            >>> if profile:
            ...     print(f"Avatar: {profile.get('image')}")
            ...     print(f"Bio: {profile.get('text')}")
        """
        if not self._nats:
            raise KrytenConnectionError("Not connected to NATS")

        # Resolve domain
        if domain is None:
            if not self.config.channels:
                raise KrytenValidationError("No channels configured")
            domain = self.config.channels[0].domain

        # Build unified command request
        subject = "kryten.robot.command"
        request = {
            "service": "robot",
            "command": "state.user",
            "username": username
        }

        try:
            response = await self._nats.request(
                subject=subject,
                payload=json.dumps(request).encode(),
                timeout=timeout
            )

            result = json.loads(response.data.decode("utf-8"))
            if result.get("success"):
                return result.get("data", {}).get("profile")
            else:
                self.logger.warning(f"Profile query failed: {result.get('error')}")
                return None

        except asyncio.TimeoutError:
            self.logger.warning(f"Profile query timed out for {username} in {domain}/{channel}")
            return None
        except Exception as e:
            self.logger.error(f"Error querying profile: {e}", exc_info=True)
            return None

    async def get_all_profiles(
        self,
        channel: str,
        *,
        domain: str | None = None,
        timeout: float = 2.0,
    ) -> dict[str, dict[str, Any]]:
        """Get all user profiles from channel.

        Args:
            channel: Channel name
            domain: Optional domain (uses first configured if None)
            timeout: Request timeout in seconds (default: 2.0)

        Returns:
            Dictionary mapping username to profile dict

        Example:
            >>> profiles = await client.get_all_profiles("lounge")
            >>> for username, profile in profiles.items():
            ...     print(f"{username}: {profile.get('image')}")
        """
        if not self._nats:
            raise KrytenConnectionError("Not connected to NATS")

        # Resolve domain
        if domain is None:
            if not self.config.channels:
                raise KrytenValidationError("No channels configured")
            domain = self.config.channels[0].domain

        # Build unified command request
        subject = "kryten.robot.command"
        request = {
            "service": "robot",
            "command": "state.profiles"
        }

        try:
            response = await self._nats.request(
                subject=subject,
                payload=json.dumps(request).encode(),
                timeout=timeout
            )

            result = json.loads(response.data.decode("utf-8"))
            if result.get("success"):
                return result.get("data", {}).get("profiles", {})
            else:
                self.logger.warning(f"Profiles query failed: {result.get('error')}")
                return {}

        except asyncio.TimeoutError:
            self.logger.warning(f"Profiles query timed out for {domain}/{channel}")
            return {}
        except Exception as e:
            self.logger.error(f"Error querying profiles: {e}", exc_info=True)
            return {}

    async def get_user_level(
        self,
        channel: str,
        *,
        domain: str | None = None,
        timeout: float = 2.0,
    ) -> dict[str, Any]:
        """Get bot's current user level (rank) from Kryten-Robot.

        Queries Kryten-Robot for the logged-in user's rank/permissions level.
        Useful for checking if the bot has sufficient permissions before
        attempting privileged operations like playlist management.

        Args:
            channel: Channel name
            domain: Optional domain (uses first configured if None)
            timeout: Request timeout in seconds (default: 2.0)

        Returns:
            Dictionary with 'success', 'rank', and 'username' keys.
            On success: {"success": True, "rank": 2, "username": "BotName"}
            On error: {"success": False, "error": "error message"}

        CyTube Rank Levels:
            - 0: Guest
            - 1: Registered User
            - 2: Moderator (playlist access)
            - 3+: Admin/Owner

        Example:
            >>> result = await client.get_user_level("lounge")
            >>> if result.get("success") and result.get("rank", 0) >= 2:
            ...     # Bot has moderator+ access
            ...     await client.add_media("lounge", "yt", "dQw4w9WgXcQ")
        """
        if not self._nats:
            return {"success": False, "error": "Not connected to NATS"}

        # Resolve domain
        if domain is None:
            if not self.config.channels:
                return {"success": False, "error": "No channels configured"}
            domain = self.config.channels[0].domain

        # Build subject for user level query
        subject = f"cytube.user_level.{domain.lower()}.{channel.lower()}"

        try:
            response = await self._nats.request(
                subject=subject,
                payload=json.dumps({}).encode(),
                timeout=timeout
            )

            result = json.loads(response.data.decode("utf-8"))
            return result

        except asyncio.TimeoutError:
            self.logger.warning(f"User level query timed out for {domain}/{channel} (Kryten-Robot may not be running)")
            return {"success": False, "error": "Timeout - Kryten-Robot not responding"}
        except Exception as e:
            self.logger.error(f"Error querying user level: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    # KeyValue Store Methods

    async def get_kv_bucket(self, bucket_name: str):
        """Get or create a NATS JetStream KeyValue bucket.

        Args:
            bucket_name: Name of the KV bucket

        Returns:
            KeyValue bucket instance

        Raises:
            KrytenConnectionError: If not connected to NATS

        Example:
            >>> kv = await client.get_kv_bucket("my-state")
        """
        if not self._nats:
            raise KrytenConnectionError("Not connected to NATS")

        return await get_kv_store(self._nats, bucket_name)

    async def get_or_create_kv_bucket(
        self,
        bucket_name: str,
        description: str | None = None,
        max_value_size: int = 1024 * 1024,
    ):
        """Get or create a NATS JetStream KeyValue bucket.

        Use this for services that own their own buckets. If the bucket
        doesn't exist, it will be created with the specified configuration.

        Args:
            bucket_name: Name of the KV bucket
            description: Description for the bucket (used on creation)
            max_value_size: Maximum value size in bytes (default 1MB)

        Returns:
            KeyValue bucket instance

        Raises:
            KrytenConnectionError: If not connected to NATS

        Example:
            >>> kv = await client.get_or_create_kv_bucket(
            ...     "my_service_data",
            ...     description="My service state"
            ... )
        """
        if not self._nats:
            raise KrytenConnectionError("Not connected to NATS")

        return await get_or_create_kv_store(
            self._nats,
            bucket_name,
            description=description,
            max_value_size=max_value_size,
            logger=self.logger,
        )

    async def kv_get(
        self,
        bucket_name: str,
        key: str,
        default: Any = None,
        parse_json: bool = False
    ) -> Any:
        """Get value from KeyValue store.

        Args:
            bucket_name: Name of the KV bucket
            key: Key to retrieve
            default: Default value if key doesn't exist
            parse_json: Whether to parse the value as JSON

        Returns:
            Value from store or default

        Example:
            >>> users = await client.kv_get("cytube_cytu_be_lounge_userlist", "users", default=[], parse_json=True)
        """
        if not self._nats:
            raise KrytenConnectionError("Not connected to NATS")

        kv = await get_kv_store(self._nats, bucket_name)
        return await kv_get(kv, key, default=default, parse_json=parse_json)

    async def kv_put(
        self,
        bucket_name: str,
        key: str,
        value: Any,
        as_json: bool = False
    ) -> None:
        """Put value into KeyValue store.

        Args:
            bucket_name: Name of the KV bucket
            key: Key to store
            value: Value to store
            as_json: Whether to serialize the value as JSON

        Example:
            >>> await client.kv_put("my-state", "counter", 42)
            >>> await client.kv_put("my-state", "config", {"setting": "value"}, as_json=True)
        """
        if not self._nats:
            raise KrytenConnectionError("Not connected to NATS")

        kv = await get_kv_store(self._nats, bucket_name)
        await kv_put(kv, key, value, as_json=as_json)

    async def kv_delete(self, bucket_name: str, key: str) -> None:
        """Delete key from KeyValue store.

        Args:
            bucket_name: Name of the KV bucket
            key: Key to delete

        Example:
            >>> await client.kv_delete("my-state", "old_key")
        """
        if not self._nats:
            raise KrytenConnectionError("Not connected to NATS")

        kv = await get_kv_store(self._nats, bucket_name)
        await kv_delete(kv, key)

    async def kv_keys(self, bucket_name: str) -> list[str]:
        """Get all keys from KeyValue store.

        Args:
            bucket_name: Name of the KV bucket

        Returns:
            List of keys

        Example:
            >>> all_keys = await client.kv_keys("my-state")
        """
        if not self._nats:
            raise KrytenConnectionError("Not connected to NATS")

        kv = await get_kv_store(self._nats, bucket_name)
        return await kv_keys(kv)

    async def kv_get_all(
        self,
        bucket_name: str,
        parse_json: bool = False
    ) -> dict[str, Any]:
        """Get all key-value pairs from KeyValue store.

        Args:
            bucket_name: Name of the KV bucket
            parse_json: Whether to parse values as JSON

        Returns:
            Dictionary of key-value pairs

        Example:
            >>> all_data = await client.kv_get_all("my-state", parse_json=True)
        """
        if not self._nats:
            raise KrytenConnectionError("Not connected to NATS")

        kv = await get_kv_store(self._nats, bucket_name)
        return await kv_get_all(kv, parse_json=parse_json)

    # Kryten-Robot State KV helpers

    def _state_bucket_prefix(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Return the KV bucket prefix used by Kryten-Robot for channel state.

        NOTE: Current Kryten-Robot implementation uses `kryten_{channel}` (domain is
        not included). This helper centralizes that convention so downstream
        services don't duplicate or guess.
        """
        _ = domain
        return f"kryten_{channel.lower()}"

    async def get_state_playlist_items(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get the current playlist items from Kryten-Robot state KV."""
        bucket = f"{self._state_bucket_prefix(channel, domain=domain)}_playlist"
        items = await self.kv_get(bucket, "items", default=[], parse_json=True)
        return items if isinstance(items, list) else []

    async def get_state_current_media(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> dict[str, Any] | None:
        """Get currently playing media from Kryten-Robot state KV."""
        bucket = f"{self._state_bucket_prefix(channel, domain=domain)}_playlist"
        current = await self.kv_get(bucket, "current", default=None, parse_json=True)
        return current if isinstance(current, dict) else None

    async def get_state_current_uid(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str | None:
        """Get UID of the currently playing item (if any) from state KV."""
        current = await self.get_state_current_media(channel, domain=domain)
        if not current:
            return None
        uid = current.get("uid")
        if uid is None:
            return None
        uid_str = str(uid).strip()
        return uid_str or None

    async def subscribe_request_reply(
        self,
        subject: str,
        handler: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> Any:
        """Subscribe to a NATS subject with request-reply pattern.

        This is for services that need to respond to queries on their own subjects.
        The handler receives the request payload and returns a response payload.

        Args:
            subject: NATS subject to subscribe to (e.g., "kryten.query.userstats.user.stats")
            handler: Async function that receives request dict and returns response dict

        Returns:
            Subscription object

        Raises:
            KrytenConnectionError: If not connected to NATS

        Example:
            >>> async def handle_query(request: dict) -> dict:
            ...     username = request.get("username")
            ...     return {"success": True, "data": {"username": username}}
            >>>
            >>> sub = await client.subscribe_request_reply(
            ...     "kryten.query.userstats.user.stats",
            ...     handle_query
            ... )
        """
        if not self._nats:
            raise KrytenConnectionError("Not connected to NATS")

        async def nats_handler(msg):
            """Wrapper to handle NATS message and send reply."""
            try:
                # Parse request
                request = json.loads(msg.data.decode('utf-8'))

                # Call handler
                response = await handler(request)

                # Send reply
                reply_payload = json.dumps(response).encode('utf-8')
                await self._nats.publish(msg.reply, reply_payload)

            except json.JSONDecodeError as e:
                self.logger.error("Invalid JSON in request: %s", e)
                error_response = json.dumps({"error": "Invalid JSON"}).encode('utf-8')
                if msg.reply:
                    await self._nats.publish(msg.reply, error_response)
            except Exception:  # noqa: BLE001
                self.logger.exception("Error in request handler")
                # Send error response
                error_response = json.dumps({"error": "Internal error"}).encode('utf-8')
                if msg.reply:
                    await self._nats.publish(msg.reply, error_response)

        # Subscribe with our wrapper
        sub = await self._nats.subscribe(subject, cb=nats_handler)
        self._subscriptions.append(sub)
        self.logger.info("Subscribed to request-reply subject: %s", subject)

        return sub

    async def nats_request(
        self,
        subject: str,
        request: dict[str, Any],
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        """Send NATS request and wait for response.

        Args:
            subject: NATS subject to send request to
            request: Request payload as dictionary
            timeout: Timeout in seconds

        Returns:
            Response payload as dictionary

        Raises:
            KrytenConnectionError: If not connected to NATS
            TimeoutError: If no response within timeout

        Example:
            >>> response = await client.nats_request(
            ...     "kryten.userstats.command",
            ...     {"service": "userstats", "command": "user.stats", "username": "alice"},
            ...     timeout=2.0
            ... )
        """
        if not self._nats:
            raise KrytenConnectionError("Not connected to NATS")

        try:
            payload = json.dumps(request).encode('utf-8')
            response = await self._nats.request(subject, payload, timeout=timeout)
            return json.loads(response.data.decode('utf-8'))
        except asyncio.TimeoutError as e:
            raise TimeoutError(f"NATS request timeout on {subject}") from e

    async def get_channels(self, timeout: float = 5.0) -> list[dict[str, Any]]:
        """Discover available channels from connected Kryten-Robot instances.

        Queries kryten.robot.command with system.channels command to get a list
        of channels that robot instances are connected to.

        Args:
            timeout: Timeout in seconds for the request

        Returns:
            List of channel dictionaries, each containing:
                - domain (str): CyTube domain
                - channel (str): Channel name
                - connected (bool): Connection status

        Raises:
            KrytenConnectionError: If not connected to NATS
            TimeoutError: If no response within timeout
            ValueError: If response format is invalid

        Example:
            >>> channels = await client.get_channels()
            >>> for ch in channels:
            ...     print(f"{ch['domain']}/{ch['channel']}")
        """
        request = {
            "service": "robot",
            "command": "system.channels"
        }

        response = await self.nats_request("kryten.robot.command", request, timeout)

        if not response.get("success"):
            error = response.get("error", "Unknown error")
            raise ValueError(f"Failed to get channels: {error}")

        channels = response.get("data", {}).get("channels", [])

        if not isinstance(channels, list):
            raise ValueError("Invalid response format: expected list of channels")

        return channels

    async def get_version(self, timeout: float = 5.0) -> str:
        """Get Kryten-Robot version from connected instance.

        Queries kryten.robot.command with system.version command to get the
        version string of the running robot instance. Useful for checking
        compatibility and enforcing minimum version requirements.

        Args:
            timeout: Timeout in seconds for the request

        Returns:
            Semantic version string (e.g., "0.5.4")

        Raises:
            KrytenConnectionError: If not connected to NATS
            TimeoutError: If no response within timeout
            ValueError: If response format is invalid

        Example:
            >>> version = await client.get_version()
            >>> print(f"Kryten-Robot version: {version}")
            >>>
            >>> # Check minimum version
            >>> from packaging import version as pkg_version
            >>> if pkg_version.parse(version) < pkg_version.parse("0.5.0"):
            ...     raise RuntimeError("Requires Kryten-Robot >= 0.5.0")
        """
        request = {
            "service": "robot",
            "command": "system.version"
        }

        response = await self.nats_request("kryten.robot.command", request, timeout)

        if not response.get("success"):
            error = response.get("error", "Unknown error")
            raise ValueError(f"Failed to get version: {error}")

        version = response.get("data", {}).get("version")

        if not isinstance(version, str):
            raise ValueError("Invalid response format: expected version string")

        return version

    async def get_stats(self, timeout: float = 5.0) -> dict[str, Any]:
        """Get comprehensive runtime statistics from Kryten-Robot.

        Queries kryten.robot.command with system.stats command to retrieve
        detailed runtime metrics including uptime, event rates, command stats,
        connection details, state counts, and memory usage.

        Args:
            timeout: Timeout in seconds for the request

        Returns:
            Dictionary containing runtime statistics with keys:
                - uptime_seconds (float): Seconds since application started
                - events (dict): Event publisher statistics
                    - total_published (int): Total events published
                    - rate_1min (float): Events/second over last minute
                    - rate_5min (float): Events/second over last 5 minutes
                    - last_event_time (str): ISO8601 timestamp of last event
                    - last_event_type (str): Type of last event
                - commands (dict): Command subscriber statistics
                    - total_received (int): Total commands received
                    - succeeded (int): Successfully processed commands
                    - failed (int): Failed commands
                    - rate_1min (float): Commands/second over last minute
                    - rate_5min (float): Commands/second over last 5 minutes
                - connections (dict): Connection details
                    - cytube (dict): CyTube connection info
                    - nats (dict): NATS connection info
                - state (dict): Channel state counts
                    - users (int): Current user count
                    - playlist (int): Playlist item count
                    - emotes (int): Emote count
                - memory (dict): Memory usage (if psutil available)
                    - rss_mb (float): Resident Set Size in MB
                    - vms_mb (float): Virtual Memory Size in MB

        Raises:
            KrytenConnectionError: If not connected to NATS
            TimeoutError: If no response within timeout
            ValueError: If response format is invalid

        Example:
            >>> stats = await client.get_stats()
            >>> print(f"Uptime: {stats['uptime'] / 3600:.1f} hours")
            >>> print(f"Events published: {stats['events']['total_published']}")
            >>> print(f"Event rate: {stats['events']['rate_1min']:.2f}/sec")
            >>> print(f"Memory usage: {stats['memory']['rss_mb']:.1f} MB")
        """
        request = {
            "service": "robot",
            "command": "system.stats"
        }

        response = await self.nats_request("kryten.robot.command", request, timeout)

        if not response.get("success"):
            error = response.get("error", "Unknown error")
            raise ValueError(f"Failed to get stats: {error}")

        stats = response.get("data", {})

        if not isinstance(stats, dict):
            raise ValueError("Invalid response format: expected stats dictionary")

        return stats

    async def get_config(self, timeout: float = 5.0) -> dict[str, Any]:
        """Get current configuration from Kryten-Robot (passwords redacted).

        Queries kryten.robot.command with system.config command to retrieve
        the running configuration with sensitive values (passwords, tokens)
        automatically redacted.

        Args:
            timeout: Timeout in seconds for the request

        Returns:
            Dictionary containing configuration with keys matching KrytenConfig
            structure (cytube, nats, commands, health, state_counting, logging).
            All password and token fields will be replaced with "***REDACTED***".

        Raises:
            KrytenConnectionError: If not connected to NATS
            TimeoutError: If no response within timeout
            ValueError: If response format is invalid

        Example:
            >>> config = await client.get_config()
            >>> print(f"Channel: {config['cytube']['channel']}")
            >>> print(f"Domain: {config['cytube']['domain']}")
            >>> print(f"Log level: {config['log_level']}")
            >>> # Passwords are automatically redacted:
            >>> print(config['nats']['password'])  # "***REDACTED***"
        """
        request = {
            "service": "robot",
            "command": "system.config"
        }

        response = await self.nats_request("kryten.robot.command", request, timeout)

        if not response.get("success"):
            error = response.get("error", "Unknown error")
            raise ValueError(f"Failed to get config: {error}")

        config = response.get("data", {})

        if not isinstance(config, dict):
            raise ValueError("Invalid response format: expected config dictionary")

        return config

    async def get_services(self, timeout: float = 5.0) -> dict[str, Any]:
        """Get list of registered microservices from Kryten-Robot.

        Queries kryten.robot.command with system.services command to retrieve
        information about all microservices that have registered with the robot,
        including their version, hostname, health/metrics endpoints, and heartbeat status.

        Args:
            timeout: Timeout in seconds for the request

        Returns:
            Dictionary containing:
                - services (list): List of service dictionaries with:
                    - name (str): Service name (e.g., "userstats", "moderator")
                    - version (str): Service version
                    - hostname (str): Host running the service
                    - first_seen (str): ISO8601 timestamp when first discovered
                    - last_heartbeat (str): ISO8601 timestamp of most recent heartbeat
                    - seconds_since_heartbeat (float): Seconds since last heartbeat
                    - is_stale (bool): True if no heartbeat in 90+ seconds
                    - health_url (str|None): Full URL for health endpoint
                    - metrics_url (str|None): Full URL for metrics endpoint
                - count (int): Total number of registered services
                - active_count (int): Number of non-stale services

        Raises:
            KrytenConnectionError: If not connected to NATS
            TimeoutError: If no response within timeout
            ValueError: If response format is invalid

        Example:
            >>> services = await client.get_services()
            >>> for svc in services["services"]:
            ...     status = "✓" if not svc["is_stale"] else "✗"
            ...     print(f"{status} {svc['name']} v{svc['version']}")
            ...     if svc["health_url"]:
            ...         print(f"    Health: {svc['health_url']}")
        """
        request = {
            "service": "robot",
            "command": "system.services"
        }

        response = await self.nats_request("kryten.robot.command", request, timeout)

        if not response.get("success"):
            error = response.get("error", "Unknown error")
            raise ValueError(f"Failed to get services: {error}")

        services = response.get("data", {})

        if not isinstance(services, dict):
            raise ValueError("Invalid response format: expected services dictionary")

        return services

    async def ping(self, timeout: float = 2.0) -> dict[str, Any]:
        """Perform lightweight alive check on Kryten-Robot.

        Queries kryten.robot.command with system.ping command for a fast
        health check that confirms the robot is running and responsive.
        Uses shorter default timeout since this should be very fast.

        Args:
            timeout: Timeout in seconds for the request (default 2s)

        Returns:
            Dictionary with keys:
                - pong (bool): Always True
                - timestamp (str): ISO8601 timestamp of response
                - uptime_seconds (float): Seconds since robot started
                - service (str): Service name ("robot")
                - version (str): Kryten-Robot version

        Raises:
            KrytenConnectionError: If not connected to NATS
            TimeoutError: If no response within timeout (robot likely down)
            ValueError: If response format is invalid

        Example:
            >>> try:
            ...     result = await client.ping()
            ...     print(f"Robot is alive at {result['timestamp']}")
            ... except TimeoutError:
            ...     print("Robot is not responding")
        """
        request = {
            "service": "robot",
            "command": "system.ping"
        }

        response = await self.nats_request("kryten.robot.command", request, timeout)

        if not response.get("success"):
            error = response.get("error", "Unknown error")
            raise ValueError(f"Failed to ping: {error}")

        ping_result = response.get("data", {})

        if not isinstance(ping_result, dict):
            raise ValueError("Invalid response format: expected ping result dictionary")

        return ping_result

    async def reload_config(
        self,
        config_path: str | None = None,
        timeout: float = 5.0
    ) -> dict[str, Any]:
        """Reload configuration on Kryten-Robot.

        Queries kryten.robot.command with system.reload command to trigger
        a configuration reload. Only "safe" changes are applied (log_level,
        NATS credentials). Unsafe changes (CyTube domain/channel) require
        a restart.

        Args:
            config_path: Optional path to config file (uses current if None)
            timeout: Timeout in seconds for the request

        Returns:
            Dictionary with keys:
                - success (bool): Whether reload succeeded
                - message (str): Human-readable result message
                - changes (dict): Dict of changes (key: "old -> new")
                - errors (list[str]): Any errors encountered

        Raises:
            KrytenConnectionError: If not connected to NATS
            TimeoutError: If no response within timeout
            ValueError: If response format is invalid or reload failed

        Example:
            >>> # Reload current config
            >>> result = await client.reload_config()
            >>> if result['changes_applied']:
            ...     print(f"Applied changes: {result['changes_applied']}")
            >>> if result['unsafe_changes']:
            ...     print(f"Restart required for: {result['unsafe_changes']}")
            >>>
            >>> # Reload from specific file
            >>> result = await client.reload_config("/path/to/config.json")
        """
        request = {
            "service": "robot",
            "command": "system.reload"
        }

        if config_path:
            request["config_path"] = config_path

        response = await self.nats_request("kryten.robot.command", request, timeout)

        if not response.get("success"):
            error = response.get("error", "Unknown error")
            raise ValueError(f"Failed to reload config: {error}")

        reload_result = response.get("data", {})

        if not isinstance(reload_result, dict):
            raise ValueError("Invalid response format: expected reload result dictionary")

        return reload_result

    async def shutdown(
        self,
        delay_seconds: int = 0,
        reason: str = "Remote shutdown via client",
        timeout: float = 5.0
    ) -> dict[str, Any]:
        """Initiate graceful shutdown of Kryten-Robot.

        Queries kryten.robot.command with system.shutdown command to trigger
        a graceful shutdown after an optional delay. The robot will cleanly
        disconnect from CyTube and NATS, save state, and exit.

        Args:
            delay_seconds: Seconds to wait before shutdown (0-300)
            reason: Human-readable reason for shutdown (for logging)
            timeout: Timeout in seconds for the request

        Returns:
            Dictionary with keys:
                - success (bool): Whether shutdown was initiated
                - message (str): Human-readable confirmation
                - delay_seconds (int): Actual delay applied
                - shutdown_time (str): ISO8601 timestamp when shutdown will occur
                - reason (str): Reason logged

        Raises:
            KrytenConnectionError: If not connected to NATS
            TimeoutError: If no response within timeout
            ValueError: If delay is invalid or shutdown failed

        Example:
            >>> # Immediate shutdown
            >>> result = await client.shutdown(reason="Maintenance")
            >>> print(f"Shutdown initiated: {result['message']}")
            >>>
            >>> # Delayed shutdown (30 seconds)
            >>> result = await client.shutdown(
            ...     delay_seconds=30,
            ...     reason="Scheduled maintenance"
            ... )
            >>> print(f"Shutdown at {result['shutdown_time']}")
        """
        if not isinstance(delay_seconds, int) or delay_seconds < 0 or delay_seconds > 300:
            raise ValueError("delay_seconds must be an integer between 0 and 300")

        request = {
            "service": "robot",
            "command": "system.shutdown",
            "delay_seconds": delay_seconds,
            "reason": reason
        }

        response = await self.nats_request("kryten.robot.command", request, timeout)

        if not response.get("success"):
            error = response.get("error", "Unknown error")
            raise ValueError(f"Failed to shutdown: {error}")

        shutdown_result = response.get("data", {})

        if not isinstance(shutdown_result, dict):
            raise ValueError("Invalid response format: expected shutdown result dictionary")

        return shutdown_result


__all__ = ["KrytenClient"]
