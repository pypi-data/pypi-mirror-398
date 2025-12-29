"""Mock Kryten client for testing without NATS."""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from kryten.config import KrytenConfig
from kryten.health import ChannelInfo, HealthStatus
from kryten.models import (
    ChangeMediaEvent,
    ChatMessageEvent,
    PlaylistUpdateEvent,
    RawEvent,
    UserJoinEvent,
    UserLeaveEvent,
)


class MockKrytenClient:
    """Mock client for testing without real NATS connection.

    Simulates KrytenClient behavior for unit testing, recording published
    commands and allowing simulation of incoming events.

    Examples:
        >>> client = MockKrytenClient(config)
        >>> async with client:
        ...     @client.on("chatmsg")
        ...     async def handle_chat(event):
        ...         print(event.username)
        ...
        ...     await client.send_chat("lounge", "Test message")
        ...     await client.simulate_event("chatmsg", {...})
        ...
        >>> commands = client.get_published_commands()
        >>> assert len(commands) == 1
    """

    def __init__(
        self,
        config: dict[str, Any] | KrytenConfig,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize mock client.

        Args:
            config: Configuration dict or model
            logger: Optional logger
        """
        if isinstance(config, dict):
            self.config = KrytenConfig(**config)
        else:
            self.config = config

        self.logger = logger or logging.getLogger(__name__)

        # Mock state
        self._connected = False
        self._handlers: dict[
            str, list[tuple[Callable[[Any], Any], str | None, str | None]]
        ] = {}
        self._published_commands: list[dict[str, Any]] = []
        self._running = False

        # Metrics
        self._events_received = 0
        self._commands_sent = 0

        # Simple in-memory KV store for tests
        # key: (bucket_name, key)
        self._kv: dict[tuple[str, str], Any] = {}

    async def connect(self) -> None:
        """Mock connect (immediate success)."""
        self._connected = True
        self.logger.info("Mock client connected")

    async def disconnect(self) -> None:
        """Mock disconnect."""
        self._connected = False
        self.logger.info("Mock client disconnected")

    async def __aenter__(self) -> "MockKrytenClient":
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        await self.disconnect()

    def on(
        self,
        event_name: str,
        channel: str | None = None,
        domain: str | None = None,
    ) -> Callable[[Callable[[Any], Any]], Callable[[Any], Any]]:
        """Register event handler."""

        def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
            if event_name not in self._handlers:
                self._handlers[event_name] = []
            self._handlers[event_name].append((func, channel, domain))
            return func

        return decorator

    async def run(self) -> None:
        """Mock run loop (does nothing)."""
        self._running = True
        while self._running:
            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        """Stop run loop."""
        self._running = False

    async def send_command(
        self,
        service: str,
        type: str,
        body: dict[str, Any],
        channel: str | None = None,
        domain: str | None = None,
    ) -> None:
        """Mock generic send command."""
        self._record_command(channel, type, body, domain)

    async def send_chat(
        self,
        channel: str,
        message: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock send chat command."""
        return self._record_command(channel, "chat", {"message": message}, domain)

    async def send_pm(
        self,
        channel: str,
        username: str,
        message: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock send PM command."""
        return self._record_command(channel, "pm", {"to": username, "message": message}, domain)

    async def add_media(
        self,
        channel: str,
        media_type: str,
        media_id: str,
        *,
        position: str = "end",
        domain: str | None = None,
    ) -> str:
        """Mock add media command."""
        return self._record_command(
            channel,
            "queue",
            {"type": media_type, "id": media_id, "pos": position},
            domain,
        )

    async def delete_media(
        self,
        channel: str,
        uid: int,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock delete media command."""
        return self._record_command(channel, "delete", {"uid": uid}, domain)

    async def move_media(
        self,
        channel: str,
        uid: int,
        position: int,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock move media command."""
        return self._record_command(channel, "move", {"from": uid, "after": position}, domain)

    async def jump_to(
        self,
        channel: str,
        uid: int,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock jump command."""
        return self._record_command(channel, "jump", {"uid": uid}, domain)

    async def clear_playlist(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock clear playlist command."""
        return self._record_command(channel, "clear", {}, domain)

    async def shuffle_playlist(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock shuffle command."""
        return self._record_command(channel, "shuffle", {}, domain)

    async def set_temp(
        self,
        channel: str,
        uid: int,
        is_temp: bool = True,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock set temp command."""
        return self._record_command(channel, "settemp", {"uid": uid, "temp": is_temp}, domain)

    async def pause(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock pause command."""
        return self._record_command(channel, "pause", {}, domain)

    async def play(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock play command."""
        return self._record_command(channel, "play", {}, domain)

    async def seek(
        self,
        channel: str,
        time_seconds: float,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock seek command."""
        return self._record_command(channel, "seek", {"time": time_seconds}, domain)

    async def kick_user(
        self,
        channel: str,
        username: str,
        reason: str | None = None,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock kick command."""
        data: dict[str, Any] = {"name": username}
        if reason:
            data["reason"] = reason
        return self._record_command(channel, "kick", data, domain)

    async def ban_user(
        self,
        channel: str,
        username: str,
        reason: str | None = None,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock ban command."""
        data: dict[str, Any] = {"name": username}
        if reason:
            data["reason"] = reason
        return self._record_command(channel, "ban", data, domain)

    async def voteskip(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str:
        """Mock voteskip command."""
        return self._record_command(channel, "voteskip", {}, domain)

    def health(self) -> HealthStatus:
        """Get mock health status."""
        return HealthStatus(
            connected=self._connected,
            state="connected" if self._connected else "disconnected",
            uptime_seconds=0.0,
            channels=[f"{c.domain}/{c.channel}" for c in self.config.channels],
            events_received=self._events_received,
            commands_sent=self._commands_sent,
            errors=0,
            avg_event_latency_ms=0.0,
            last_event_time=None,
            handlers_registered=sum(len(h) for h in self._handlers.values()),
        )

    @property
    def is_connected(self) -> bool:
        """Check if mock client is connected."""
        return self._connected

    # KeyValue Store Methods (mocked)

    async def get_kv_bucket(self, bucket_name: str) -> str:
        _ = bucket_name
        return "mock"

    async def get_or_create_kv_bucket(
        self,
        bucket_name: str,
        description: str | None = None,
        max_value_size: int = 1024 * 1024,
    ) -> str:
        _ = (bucket_name, description, max_value_size)
        return "mock"

    async def kv_get(
        self,
        bucket_name: str,
        key: str,
        default: Any = None,
        parse_json: bool = False,
    ) -> Any:
        _ = parse_json
        return self._kv.get((bucket_name, key), default)

    async def kv_put(
        self,
        bucket_name: str,
        key: str,
        value: Any,
        as_json: bool = False,
    ) -> None:
        _ = as_json
        self._kv[(bucket_name, key)] = value

    async def kv_delete(self, bucket_name: str, key: str) -> None:
        self._kv.pop((bucket_name, key), None)

    async def kv_keys(self, bucket_name: str) -> list[str]:
        return [k for (b, k) in self._kv.keys() if b == bucket_name]

    async def kv_get_all(self, bucket_name: str, parse_json: bool = False) -> dict[str, Any]:
        _ = parse_json
        return {k: v for (b, k), v in self._kv.items() if b == bucket_name}

    # Kryten-Robot State KV helpers (mocked)

    def _state_bucket_prefix(self, channel: str, *, domain: str | None = None) -> str:
        _ = domain
        return f"kryten_{channel.lower()}"

    async def get_state_playlist_items(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> list[dict[str, Any]]:
        bucket = f"{self._state_bucket_prefix(channel, domain=domain)}_playlist"
        items = await self.kv_get(bucket, "items", default=[], parse_json=True)
        return items if isinstance(items, list) else []

    async def get_state_current_media(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> dict[str, Any] | None:
        bucket = f"{self._state_bucket_prefix(channel, domain=domain)}_playlist"
        current = await self.kv_get(bucket, "current", default=None, parse_json=True)
        return current if isinstance(current, dict) else None

    async def get_state_current_uid(
        self,
        channel: str,
        *,
        domain: str | None = None,
    ) -> str | None:
        current = await self.get_state_current_media(channel, domain=domain)
        if not current:
            return None
        uid = current.get("uid")
        if uid is None:
            return None
        uid_str = str(uid).strip()
        return uid_str or None

    @property
    def channels(self) -> list[ChannelInfo]:
        """Get configured channels."""
        return [
            ChannelInfo(
                domain=c.domain,
                channel=c.channel,
                subscribed=self._connected,
                events_received=0,
            )
            for c in self.config.channels
        ]

    async def send_command(
        self,
        service: str,
        type: str,
        body: dict[str, Any],
        channel: str | None = None,
        domain: str | None = None,
    ) -> str:
        """Mock generic command sending."""
        # For mock purposes, we map this to _record_command.
        # Note: _record_command signature is (channel, type, body, domain)
        # It doesn't take 'service'. We can ignore service or encode it in type?
        # Let's verify _record_command signature by looking at usage:
        # self._record_command(channel, "chat", ...)
        
        # We'll just pass it through. If tests inspect published commands, 
        # they will see 'type' and 'body'.
        # If 'service' is important for test assertions, we might need to update _record_command.
        # But for now, let's just make it work.
        return self._record_command(channel, type, body, domain)

    def get_published_commands(self) -> list[dict[str, Any]]:
        """Get list of all published commands for verification.

        Returns:
            List of command dictionaries with subject, data, correlation_id
        """
        return self._published_commands.copy()

    def clear_published_commands(self) -> None:
        """Clear recorded commands."""
        self._published_commands.clear()

    async def simulate_event(
        self,
        event_name: str,
        payload: dict[str, Any],
        *,
        channel: str | None = None,
        domain: str | None = None,
    ) -> None:
        """Simulate receiving an event (for testing).

        Args:
            event_name: Event name
            payload: Event payload
            channel: Optional channel (uses first configured if None)
            domain: Optional domain (uses first configured if None)
        """
        if not self._connected:
            raise RuntimeError("Mock client not connected")

        # Use first configured channel if not specified
        if channel is None:
            channel = self.config.channels[0].channel
        if domain is None:
            domain = self.config.channels[0].domain

        # Create raw event
        raw_event = RawEvent(
            event_name=event_name,
            payload=payload,
            channel=channel,
            domain=domain,
            timestamp=datetime.now(timezone.utc),
        )

        self._events_received += 1

        # Find and invoke handlers
        handlers = self._handlers.get(event_name.lower(), [])
        for handler, channel_filter, domain_filter in handlers:
            if channel_filter and channel_filter != channel:
                continue
            if domain_filter and domain_filter != domain:
                continue

            # Convert to typed event and invoke handler
            typed_event = self._convert_to_typed_event(raw_event)
            await handler(typed_event)

    def _convert_to_typed_event(self, raw_event: RawEvent) -> Any:
        """Convert RawEvent to specific typed event based on event_name.

        Args:
            raw_event: Raw event from simulation

        Returns:
            Typed event object or RawEvent if no conversion available
        """
        event_name = raw_event.event_name.lower()
        payload = raw_event.payload

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

    def _record_command(
        self,
        channel: str,
        action: str,
        data: dict[str, Any],
        domain: str | None,
    ) -> str:
        """Record a published command."""
        import uuid

        correlation_id = str(uuid.uuid4())

        command = {
            "subject": f"cytube.commands.{channel.lower()}.{action.lower()}",
            "action": action,
            "data": data,
            "channel": channel,
            "domain": domain or self.config.channels[0].domain,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._published_commands.append(command)
        self._commands_sent += 1

        self.logger.debug(f"Recorded command: {action} to {channel}")

        return correlation_id


__all__ = ["MockKrytenClient"]
