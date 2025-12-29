"""Base storage protocol for py-observatory."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StorageProtocol(Protocol):
    """Protocol defining the storage adapter interface."""

    async def update_counter(self, data: dict[str, Any]) -> None:
        """Update a counter metric.

        Args:
            data: Dict containing:
                - name: Metric name
                - help: Help text
                - type: 'counter'
                - labelNames: List of label names
                - labelValues: List of label values
                - value: Value to increment by
        """
        ...

    async def update_gauge(self, data: dict[str, Any]) -> None:
        """Update a gauge metric.

        Args:
            data: Dict containing:
                - name: Metric name
                - help: Help text
                - type: 'gauge'
                - labelNames: List of label names
                - labelValues: List of label values
                - value: New value or increment
                - command: 'set' or 'inc'
        """
        ...

    async def update_histogram(self, data: dict[str, Any]) -> None:
        """Update a histogram metric.

        Args:
            data: Dict containing:
                - name: Metric name
                - help: Help text
                - type: 'histogram'
                - labelNames: List of label names
                - labelValues: List of label values
                - value: Observed value
                - buckets: List of bucket boundaries
        """
        ...

    async def collect(self) -> list[dict[str, Any]]:
        """Collect all metrics for rendering.

        Returns:
            List of metric dicts containing:
                - name: Metric name
                - help: Help text
                - type: Metric type
                - labelNames: List of label names
                - samples: List of sample dicts
        """
        ...

    async def wipe(self) -> None:
        """Clear all stored metrics."""
        ...

    async def close(self) -> None:
        """Close any connections and clean up resources."""
        ...
