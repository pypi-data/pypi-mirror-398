"""Base exporter protocol for py-observatory."""

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class ExporterProtocol(Protocol):
    """Protocol defining the exporter interface."""

    async def record_inbound(self, data: dict[str, Any]) -> None:
        """Record an inbound HTTP request.

        Args:
            data: Dict containing:
                - method: HTTP method
                - uri: Request URI
                - route: Route pattern
                - status_code: Response status code
                - duration: Request duration in seconds
        """
        ...

    async def record_outbound(self, data: dict[str, Any]) -> None:
        """Record an outbound HTTP request.

        Args:
            data: Dict containing:
                - method: HTTP method
                - host: Target host
                - path: Request path
                - status_code: Response status code
                - duration: Request duration in seconds
                - error: Optional error message
        """
        ...

    async def record_exception(
        self,
        exception: BaseException,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record an exception.

        Args:
            exception: The exception that was raised.
            context: Optional context dict with additional info.
        """
        ...

    async def increment_counter(
        self,
        name: str,
        labels: Optional[dict[str, str]] = None,
        value: float = 1.0,
    ) -> None:
        """Increment a custom counter metric.

        Args:
            name: Metric name.
            labels: Optional dict of label name-value pairs.
            value: Value to increment by (default 1).
        """
        ...

    async def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """Set a custom gauge metric value.

        Args:
            name: Metric name.
            value: Gauge value.
            labels: Optional dict of label name-value pairs.
        """
        ...

    async def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """Observe a custom histogram metric.

        Args:
            name: Metric name.
            value: Observed value.
            labels: Optional dict of label name-value pairs.
        """
        ...

    async def get_output(self) -> str:
        """Get metrics output in Prometheus text format.

        Returns:
            Prometheus exposition format text.
        """
        ...

    async def flush(self) -> None:
        """Flush any buffered data."""
        ...

    async def close(self) -> None:
        """Close connections and clean up resources."""
        ...
