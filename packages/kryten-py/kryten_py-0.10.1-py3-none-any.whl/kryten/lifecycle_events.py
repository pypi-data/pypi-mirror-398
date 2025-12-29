"""Lifecycle Event Publisher for Kryten Services.

This module provides lifecycle event publishing for Kryten services, including:
- Service startup/shutdown events
- Connection/disconnection events
- Groupwide restart coordination
- Periodic heartbeats
- Service discovery responses

These events allow other Kryten services to monitor system health and coordinate
restarts across the service group.
"""

import asyncio
import json
import logging
import socket
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from nats.aio.client import Client as NATSClient


class LifecycleEventPublisher:
    """Publisher for service lifecycle events.

    Publishes events for service startup, shutdown, connection changes,
    periodic heartbeats, and handles service discovery.

    Subject patterns:
        - kryten.lifecycle.{service}.startup
        - kryten.lifecycle.{service}.shutdown
        - kryten.lifecycle.{service}.heartbeat
        - kryten.lifecycle.{service}.connected
        - kryten.lifecycle.{service}.disconnected
        - kryten.lifecycle.group.restart (broadcast to all services)
        - kryten.service.discovery.poll (listen for discovery requests)

    Attributes:
        service_name: Name of this service (e.g., "robot", "userstats")
        nats_client: NATS client for publishing events.
        logger: Logger instance.

    Examples:
        >>> lifecycle = LifecycleEventPublisher("myservice", nats_client, logger)
        >>> await lifecycle.start()
        >>> await lifecycle.publish_startup()
        >>> # ... service runs with automatic heartbeats ...
        >>> await lifecycle.publish_shutdown()
        >>> await lifecycle.stop()
    """

    def __init__(
        self,
        service_name: str,
        nats_client: NATSClient,
        logger: logging.Logger,
        version: str = "unknown",
        heartbeat_interval: int = 30,
        enable_heartbeat: bool = True,
        enable_discovery: bool = True,
        health_port: int | None = None,
        health_path: str = "/health",
        metrics_port: int | None = None,
        metrics_path: str = "/metrics",
    ) -> None:
        """Initialize lifecycle event publisher.

        Args:
            service_name: Name of this service (robot, userstats, etc.).
            nats_client: NATS client for event publishing.
            logger: Logger for structured output.
            version: Service version string.
            heartbeat_interval: Seconds between heartbeat publishes.
            enable_heartbeat: Whether to publish periodic heartbeats.
            enable_discovery: Whether to respond to discovery polls.
            health_port: Port for health endpoint (e.g., 8080).
            health_path: Path for health endpoint (default: /health).
            metrics_port: Port for metrics endpoint (defaults to health_port).
            metrics_path: Path for metrics endpoint (default: /metrics).
        """
        self._service_name = service_name
        self._nats = nats_client
        self._logger = logger
        self._version = version
        self._heartbeat_interval = heartbeat_interval
        self._enable_heartbeat = enable_heartbeat
        self._enable_discovery = enable_discovery

        self._running = False
        self._subscription: Any = None
        self._discovery_subscription: Any = None
        self._heartbeat_task: asyncio.Task | None = None
        self._restart_callback: Callable[[dict[str, Any]], Any] | None = None

        # Service metadata
        self._hostname = socket.gethostname()
        self._start_time: datetime | None = None
        self._heartbeat_count = 0

        # Custom metadata for heartbeats/discovery
        self._custom_metadata: dict[str, Any] = {}

        # Auto-configure endpoints if provided
        if health_port is not None or metrics_port is not None:
            self.set_endpoints(
                health_port=health_port,
                health_path=health_path,
                metrics_port=metrics_port,
                metrics_path=metrics_path,
            )

    @property
    def is_running(self) -> bool:
        """Check if lifecycle publisher is running."""
        return self._running

    def set_metadata(self, key: str, value: Any) -> None:
        """Set custom metadata to include in heartbeats and discovery responses.

        Args:
            key: Metadata key
            value: Metadata value (must be JSON-serializable)
        """
        self._custom_metadata[key] = value

    def update_metadata(self, data: dict[str, Any]) -> None:
        """Update multiple custom metadata values.

        Args:
            data: Dictionary of metadata to merge
        """
        self._custom_metadata.update(data)

    async def start(self) -> None:
        """Start lifecycle event publisher, heartbeats, and discovery handler."""
        if self._running:
            self._logger.warning("Lifecycle event publisher already running")
            return

        self._running = True
        self._start_time = datetime.now(timezone.utc)

        # Subscribe to groupwide restart notices
        try:
            self._subscription = await self._nats.subscribe(
                "kryten.lifecycle.group.restart",
                cb=self._handle_restart_notice
            )
            self._logger.info("Subscribed to groupwide restart notices")
        except Exception as e:
            self._logger.error("Failed to subscribe to restart notices: %s", e, exc_info=True)

        # Subscribe to service discovery polls
        if self._enable_discovery:
            try:
                self._discovery_subscription = await self._nats.subscribe(
                    "kryten.service.discovery.poll",
                    cb=self._handle_discovery_poll
                )
                self._logger.info("Subscribed to service discovery polls")
            except Exception as e:
                self._logger.error("Failed to subscribe to discovery polls: %s", e, exc_info=True)

        # Start heartbeat task
        if self._enable_heartbeat:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self._logger.info("Started heartbeat task (interval: %ds)", self._heartbeat_interval)

    async def stop(self) -> None:
        """Stop lifecycle event publisher and heartbeat task."""
        if not self._running:
            return

        self._running = False

        # Stop heartbeat task
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._logger.debug("Heartbeat task stopped")

        # Unsubscribe from restart notices
        if self._subscription:
            try:
                await self._subscription.unsubscribe()
            except Exception as e:
                self._logger.warning("Error unsubscribing from restart notices: %s", e)

        # Unsubscribe from discovery polls
        if self._discovery_subscription:
            try:
                await self._discovery_subscription.unsubscribe()
            except Exception as e:
                self._logger.warning("Error unsubscribing from discovery polls: %s", e)

        self._subscription = None
        self._discovery_subscription = None
        self._heartbeat_task = None

    async def _heartbeat_loop(self) -> None:
        """Background task that publishes periodic heartbeats."""
        while self._running:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                if self._running:
                    await self.publish_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("Error in heartbeat loop: %s", e, exc_info=True)
                await asyncio.sleep(5)  # Brief delay before retrying

    async def _handle_discovery_poll(self, msg: Any) -> None:  # noqa: ARG002
        """Handle service discovery poll by re-publishing startup event."""
        try:
            self._logger.debug("Received discovery poll, re-announcing service")
            await self.publish_startup()
        except Exception as e:
            self._logger.error("Error handling discovery poll: %s", e, exc_info=True)

    def on_restart_notice(self, callback: Callable[[dict[str, Any]], Any]) -> None:
        """Register callback for groupwide restart notices.

        Args:
            callback: Async function to call when restart notice received.
                      Signature: async def callback(data: dict) -> None
        """
        self._restart_callback = callback

    async def _handle_restart_notice(self, msg: Any) -> None:
        """Handle incoming groupwide restart notice."""
        try:
            data = json.loads(msg.data.decode('utf-8'))

            # Extract restart parameters
            initiator = data.get('initiator', 'unknown')
            reason = data.get('reason', 'No reason provided')
            delay_seconds = data.get('delay_seconds', 5)

            self._logger.warning(
                "Groupwide restart notice received from %s: %s (restarting in %ss)",
                initiator, reason, delay_seconds
            )

            # Call registered callback if any
            if self._restart_callback:
                try:
                    await self._restart_callback(data)
                except Exception as e:
                    self._logger.error("Error in restart callback: %s", e, exc_info=True)

        except json.JSONDecodeError as e:
            self._logger.error("Invalid restart notice JSON: %s", e)
        except Exception as e:
            self._logger.error("Error handling restart notice: %s", e, exc_info=True)

    def _build_base_payload(self) -> dict[str, Any]:
        """Build base event payload with common metadata."""
        uptime = None
        if self._start_time:
            uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

        payload = {
            "service": self._service_name,
            "version": self._version,
            "hostname": self._hostname,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime,
        }
        
        # Include custom metadata (health/metrics endpoints, etc.)
        if self._custom_metadata:
            payload["metadata"] = self._custom_metadata.copy()
        
        return payload

    def set_endpoints(
        self,
        health_port: int | None = None,
        metrics_port: int | None = None,
        health_path: str = "/health",
        metrics_path: str = "/metrics",
    ) -> None:
        """Set health and metrics endpoint information for service discovery.
        
        This information is included in startup and heartbeat events, allowing
        other services to discover how to reach this service's endpoints.
        
        Args:
            health_port: Port for health endpoint (e.g., 8080)
            metrics_port: Port for metrics endpoint (e.g., 9090)
            health_path: Path for health endpoint (default: /health)
            metrics_path: Path for metrics endpoint (default: /metrics)
        
        Examples:
            >>> lifecycle.set_endpoints(health_port=8080, metrics_port=9090)
            >>> lifecycle.set_endpoints(health_port=28282)  # Same port for both
        """
        endpoints = {}
        if health_port is not None:
            endpoints["health"] = {
                "port": health_port,
                "path": health_path,
            }
        if metrics_port is not None:
            endpoints["metrics"] = {
                "port": metrics_port,
                "path": metrics_path,
            }
        if endpoints:
            self._custom_metadata["endpoints"] = endpoints

    async def publish_startup(self, **extra_data: Any) -> None:
        """Publish service startup event.

        Args:
            **extra_data: Additional key-value pairs to include in event.
        """
        subject = f"kryten.lifecycle.{self._service_name}.startup"
        payload = self._build_base_payload()
        payload.update(extra_data)

        try:
            data_bytes = json.dumps(payload).encode('utf-8')
            await self._nats.publish(subject, data_bytes)
            self._logger.info("Published startup event to %s", subject)
        except Exception as e:
            self._logger.error("Failed to publish startup event: %s", e, exc_info=True)

    async def publish_shutdown(self, reason: str = "Normal shutdown", **extra_data: Any) -> None:
        """Publish service shutdown event.

        Args:
            reason: Reason for shutdown.
            **extra_data: Additional key-value pairs to include in event.
        """
        subject = f"kryten.lifecycle.{self._service_name}.shutdown"
        payload = self._build_base_payload()
        payload["reason"] = reason
        payload.update(extra_data)

        try:
            data_bytes = json.dumps(payload).encode('utf-8')
            await self._nats.publish(subject, data_bytes)
            self._logger.info("Published shutdown event to %s", subject)
        except Exception as e:
            self._logger.error("Failed to publish shutdown event: %s", e, exc_info=True)

    async def publish_heartbeat(self, **extra_data: Any) -> None:
        """Publish service heartbeat event.

        Heartbeats are published periodically to indicate the service is alive.
        They include uptime information and can be used for health monitoring.

        Args:
            **extra_data: Additional key-value pairs to include in event.
        """
        subject = f"kryten.lifecycle.{self._service_name}.heartbeat"
        payload = self._build_base_payload()
        payload.update(extra_data)

        try:
            data_bytes = json.dumps(payload).encode('utf-8')
            await self._nats.publish(subject, data_bytes)
            self._logger.debug("Published heartbeat to %s", subject)
        except Exception as e:
            self._logger.error("Failed to publish heartbeat: %s", e, exc_info=True)

    async def publish_connected(self, target: str, **extra_data: Any) -> None:
        """Publish connection established event.

        Args:
            target: Connection target (e.g., "CyTube", "NATS", "Database").
            **extra_data: Additional key-value pairs to include in event.
        """
        subject = f"kryten.lifecycle.{self._service_name}.connected"
        payload = self._build_base_payload()
        payload["target"] = target
        payload.update(extra_data)

        try:
            data_bytes = json.dumps(payload).encode('utf-8')
            await self._nats.publish(subject, data_bytes)
            self._logger.debug("Published connected event to %s", subject)
        except Exception as e:
            self._logger.error("Failed to publish connected event: %s", e, exc_info=True)

    async def publish_disconnected(self, target: str, reason: str = "Unknown", **extra_data: Any) -> None:
        """Publish connection lost event.

        Args:
            target: Connection target (e.g., "CyTube", "NATS").
            reason: Reason for disconnection.
            **extra_data: Additional key-value pairs to include in event.
        """
        subject = f"kryten.lifecycle.{self._service_name}.disconnected"
        payload = self._build_base_payload()
        payload["target"] = target
        payload["reason"] = reason
        payload.update(extra_data)

        try:
            data_bytes = json.dumps(payload).encode('utf-8')
            await self._nats.publish(subject, data_bytes)
            self._logger.warning("Published disconnected event to %s", subject)
        except Exception as e:
            self._logger.error("Failed to publish disconnected event: %s", e, exc_info=True)

    async def publish_group_restart(
        self,
        reason: str,
        delay_seconds: int = 5,
        initiator: str | None = None,
        **extra_data: Any
    ) -> None:
        """Publish groupwide restart notice to all Kryten services.

        Args:
            reason: Reason for restart (e.g., "Configuration update").
            delay_seconds: Seconds to wait before restarting.
            initiator: Service/user initiating restart.
            **extra_data: Additional key-value pairs to include in event.
        """
        subject = "kryten.lifecycle.group.restart"
        payload = {
            "initiator": initiator or self._service_name,
            "reason": reason,
            "delay_seconds": delay_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        payload.update(extra_data)

        try:
            data_bytes = json.dumps(payload).encode('utf-8')
            await self._nats.publish(subject, data_bytes)
            self._logger.warning(
                "Published groupwide restart notice: %s (delay: %ss)",
                reason, delay_seconds
            )
        except Exception as e:
            self._logger.error("Failed to publish restart notice: %s", e, exc_info=True)


__all__ = ["LifecycleEventPublisher"]
