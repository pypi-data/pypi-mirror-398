"""Base HTTP metrics server for Kryten microservices.

Provides a reusable HTTP server for exposing health and Prometheus metrics.
Microservices can extend this to add their own custom metrics.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from aiohttp import web


class BaseMetricsServer(ABC):
    """Base HTTP server for health and Prometheus metrics.

    Provides:
    - GET /health - JSON health status
    - GET /metrics - Prometheus format metrics

    Subclasses must implement:
    - _collect_custom_metrics() - Return list of Prometheus metric lines
    - _get_health_details() - Return dict of health details

    Example usage:
        class MyMetricsServer(BaseMetricsServer):
            def __init__(self, app, port=8080):
                super().__init__(
                    service_name="myservice",
                    port=port,
                    client=app.client
                )
                self.app = app

            async def _collect_custom_metrics(self) -> list[str]:
                return [
                    "# HELP myservice_requests Total requests",
                    "# TYPE myservice_requests counter",
                    f"myservice_requests {self.app.request_count}",
                ]

            async def _get_health_details(self) -> dict:
                return {
                    "database": "connected" if self.app.db else "disconnected",
                    "requests_processed": self.app.request_count,
                }
    """

    def __init__(
        self,
        service_name: str,
        port: int = 8080,
        client: Any = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize metrics server.

        Args:
            service_name: Name of the service (used in metric names)
            port: HTTP port to listen on
            client: Optional KrytenClient for connection status
            logger: Optional logger instance
        """
        self.service_name = service_name
        self.port = port
        self.client = client
        self.logger = logger or logging.getLogger(__name__)

        self._web_app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

        self.start_time = time.time()
        self._running = False

    async def start(self) -> None:
        """Start HTTP server."""
        self._web_app = web.Application()
        self._web_app.router.add_get("/health", self._handle_health)
        self._web_app.router.add_get("/metrics", self._handle_metrics)

        self._runner = web.AppRunner(self._web_app)
        await self._runner.setup()

        self._site = web.TCPSite(self._runner, "0.0.0.0", self.port)
        await self._site.start()

        self._running = True
        self.logger.info(f"Metrics server listening on port {self.port}")

    async def stop(self) -> None:
        """Stop HTTP server."""
        self._running = False

        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()

        self.logger.info("Metrics server stopped")

    async def _handle_health(self, request: web.Request) -> web.Response:
        """Handle GET /health request."""
        try:
            health = await self._build_health_response()
            status = 200 if health.get("status") == "healthy" else 503
            return web.json_response(health, status=status)
        except Exception as e:
            self.logger.error(f"Error in health check: {e}", exc_info=True)
            return web.json_response(
                {"status": "error", "error": str(e)},
                status=500
            )

    async def _handle_metrics(self, request: web.Request) -> web.Response:
        """Handle GET /metrics request."""
        try:
            metrics = await self._collect_all_metrics()
            return web.Response(
                text=metrics,
                content_type="text/plain; version=0.0.4"
            )
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}", exc_info=True)
            return web.Response(text="# Error collecting metrics\n", status=500)

    async def _build_health_response(self) -> dict:
        """Build health response JSON."""
        uptime = time.time() - self.start_time

        # Base health info
        health = {
            "service": self.service_name,
            "status": "healthy",
            "uptime_seconds": round(uptime, 2),
            "nats_connected": False,
        }

        # Check NATS connection if client provided
        if self.client:
            try:
                health["nats_connected"] = getattr(self.client, "_running", False)
            except Exception:
                health["nats_connected"] = False

        # Add custom health details
        try:
            custom_details = await self._get_health_details()
            health.update(custom_details)
        except Exception as e:
            health["custom_health_error"] = str(e)

        # Determine overall status
        if not health.get("nats_connected"):
            health["status"] = "degraded"

        return health

    async def _collect_all_metrics(self) -> str:
        """Collect all metrics in Prometheus format."""
        lines = []

        # Standard metrics
        uptime = time.time() - self.start_time
        prefix = self.service_name.replace("-", "_")

        lines.append(f"# HELP {prefix}_uptime_seconds Service uptime in seconds")
        lines.append(f"# TYPE {prefix}_uptime_seconds gauge")
        lines.append(f"{prefix}_uptime_seconds {uptime:.2f}")
        lines.append("")

        lines.append(f"# HELP {prefix}_service_status Service health status (1=healthy, 0=unhealthy)")
        lines.append(f"# TYPE {prefix}_service_status gauge")
        lines.append(f"{prefix}_service_status {1 if self._running else 0}")
        lines.append("")

        # NATS connection status
        if self.client:
            nats_connected = 1 if getattr(self.client, "_running", False) else 0
            lines.append(f"# HELP {prefix}_nats_connected NATS connection status (1=connected, 0=disconnected)")
            lines.append(f"# TYPE {prefix}_nats_connected gauge")
            lines.append(f"{prefix}_nats_connected {nats_connected}")
            lines.append("")

        # Custom metrics from subclass
        try:
            custom_metrics = await self._collect_custom_metrics()
            lines.extend(custom_metrics)
        except Exception as e:
            lines.append(f"# Error collecting custom metrics: {e}")

        return "\n".join(lines)

    @abstractmethod
    async def _collect_custom_metrics(self) -> list[str]:
        """Collect custom metrics for this service.

        Returns:
            List of Prometheus format metric lines.

        Example:
            return [
                "# HELP myservice_items Total items processed",
                "# TYPE myservice_items counter",
                "myservice_items 42",
                "",
            ]
        """
        ...

    @abstractmethod
    async def _get_health_details(self) -> dict:
        """Get custom health details for this service.

        Returns:
            Dict of health details to include in /health response.

        Example:
            return {
                "database": "connected",
                "items_processed": 42,
            }
        """
        ...


class SimpleMetricsServer(BaseMetricsServer):
    """Simple metrics server with callback-based custom metrics.

    For services that don't need to subclass, provides a simpler API:

        server = SimpleMetricsServer(
            service_name="myservice",
            port=8080,
            client=client,
            metrics_callback=my_metrics_func,
            health_callback=my_health_func,
        )

    The callbacks should be async functions:
        async def my_metrics_func() -> list[str]:
            return ["# HELP my_metric ...", "my_metric 42"]

        async def my_health_func() -> dict:
            return {"database": "connected"}
    """

    def __init__(
        self,
        service_name: str,
        port: int = 8080,
        client: Any = None,
        logger: logging.Logger | None = None,
        metrics_callback: Callable[[], list[str]] | None = None,
        health_callback: Callable[[], dict] | None = None,
    ):
        """Initialize simple metrics server.

        Args:
            service_name: Name of the service
            port: HTTP port to listen on
            client: Optional KrytenClient for connection status
            logger: Optional logger instance
            metrics_callback: Async function returning custom metric lines
            health_callback: Async function returning health details dict
        """
        super().__init__(service_name, port, client, logger)
        self._metrics_callback = metrics_callback
        self._health_callback = health_callback

    async def _collect_custom_metrics(self) -> list[str]:
        """Collect custom metrics via callback."""
        if self._metrics_callback:
            result = self._metrics_callback()
            if asyncio.iscoroutine(result):
                return await result
            return result
        return []

    async def _get_health_details(self) -> dict:
        """Get health details via callback."""
        if self._health_callback:
            result = self._health_callback()
            if asyncio.iscoroutine(result):
                return await result
            return result
        return {}


__all__ = [
    "BaseMetricsServer",
    "SimpleMetricsServer",
]
