"""Inbound HTTP request collector for py-observatory."""

from fnmatch import fnmatch
from typing import TYPE_CHECKING

from starlette.requests import Request
from starlette.responses import Response

from ..config import InboundConfig

if TYPE_CHECKING:
    from ..exporters.base import ExporterProtocol


class InboundCollector:
    """Collector for inbound HTTP requests."""

    def __init__(
        self,
        exporter: "ExporterProtocol",
        config: InboundConfig,
    ) -> None:
        """Initialize inbound collector.

        Args:
            exporter: Metrics exporter.
            config: Inbound configuration.
        """
        self._exporter = exporter
        self._config = config

    def should_monitor(self, request: Request) -> bool:
        """Check if request should be monitored.

        Args:
            request: The incoming request.

        Returns:
            True if request should be monitored.
        """
        if not self._config.enabled:
            return False

        # Check HTTP method
        if request.method not in self._config.methods:
            return False

        # Check excluded paths
        path = request.url.path
        for pattern in self._config.exclude_paths:
            # Try exact match first
            if path == pattern or path.lstrip("/") == pattern.lstrip("/"):
                return False
            # Try wildcard match
            if fnmatch(path, pattern) or fnmatch(path.lstrip("/"), pattern):
                return False

        return True

    def get_route_name(self, request: Request) -> str:
        """Extract route name/pattern from request.

        Args:
            request: The incoming request.

        Returns:
            Route pattern or path.
        """
        # Try to get the matched route pattern from FastAPI/Starlette
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "path"):
                return route.path

        # Fall back to actual path
        return request.url.path

    async def record(
        self,
        request: Request,
        response: Response,
        duration: float,
    ) -> None:
        """Record inbound request metrics.

        Args:
            request: The incoming request.
            response: The outgoing response.
            duration: Request duration in seconds.
        """
        data = {
            "method": request.method,
            "uri": request.url.path,
            "route": self.get_route_name(request),
            "status_code": response.status_code,
            "duration": duration,
        }

        await self._exporter.record_inbound(data)
