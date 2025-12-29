"""Outbound HTTP request collector for py-observatory."""

from fnmatch import fnmatch
from typing import TYPE_CHECKING, Optional

from ..config import OutboundConfig

if TYPE_CHECKING:
    from ..exporters.base import ExporterProtocol


class OutboundCollector:
    """Collector for outbound HTTP requests."""

    def __init__(
        self,
        exporter: "ExporterProtocol",
        config: OutboundConfig,
    ) -> None:
        """Initialize outbound collector.

        Args:
            exporter: Metrics exporter.
            config: Outbound configuration.
        """
        self._exporter = exporter
        self._config = config

    def should_monitor(self, host: str) -> bool:
        """Check if host should be monitored.

        Args:
            host: Target host.

        Returns:
            True if host should be monitored.
        """
        if not self._config.enabled:
            return False

        for exclude_host in self._config.exclude_hosts:
            # Case-insensitive comparison
            if host.lower() == exclude_host.lower():
                return False
            # Wildcard match
            if fnmatch(host.lower(), exclude_host.lower()):
                return False

        return True

    async def record(
        self,
        method: str,
        host: str,
        path: str,
        status_code: int,
        duration: float,
        error: Optional[str] = None,
    ) -> None:
        """Record outbound request metrics.

        Args:
            method: HTTP method.
            host: Target host.
            path: Request path.
            status_code: Response status code (0 if error).
            duration: Request duration in seconds.
            error: Optional error message.
        """
        data = {
            "method": method,
            "host": host,
            "path": path,
            "status_code": status_code if not error else 0,
            "duration": duration,
            "error": error,
        }

        await self._exporter.record_outbound(data)
