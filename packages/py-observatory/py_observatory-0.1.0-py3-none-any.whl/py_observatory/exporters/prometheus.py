"""Prometheus exporter for py-observatory."""

import re
from typing import Any, Optional, Union

from ..config import ObservatoryConfig, StorageType
from ..storage.memory import MemoryStorage


class PrometheusExporter:
    """Prometheus metrics exporter."""

    def __init__(self, config: ObservatoryConfig) -> None:
        """Initialize Prometheus exporter.

        Args:
            config: Observatory configuration.
        """
        self._config = config
        self._namespace = self._sanitize_namespace(config.app_name)
        self._storage = self._create_storage()

    def _create_storage(self) -> Union[MemoryStorage, Any]:
        """Create storage adapter based on configuration."""
        storage_type = self._config.prometheus.storage

        if storage_type == StorageType.REDIS:
            from ..storage.redis import RedisStorage
            return RedisStorage(self._config.prometheus.redis)
        elif storage_type == StorageType.FILE:
            from ..storage.file import FileStorage
            return FileStorage(self._config.prometheus.file)
        else:
            return MemoryStorage()

    def _sanitize_namespace(self, name: str) -> str:
        """Sanitize namespace for Prometheus compatibility.

        Args:
            name: Raw namespace name.

        Returns:
            Sanitized namespace.
        """
        # Replace invalid characters with underscore
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        # Ensure doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = "_" + sanitized
        return sanitized or "app"

    def _sanitize_name(self, name: str) -> str:
        """Sanitize metric name for Prometheus compatibility.

        Args:
            name: Raw metric name.

        Returns:
            Sanitized metric name.
        """
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        if sanitized and sanitized[0].isdigit():
            sanitized = "_" + sanitized
        return sanitized or "metric"

    def _sanitize_label(self, value: str) -> str:
        """Sanitize label value (escape special chars, truncate).

        Args:
            value: Raw label value.

        Returns:
            Sanitized label value.
        """
        # Escape backslashes, newlines, and quotes
        value = str(value)
        value = value.replace("\\", "\\\\")
        value = value.replace("\n", "\\n")
        value = value.replace('"', '\\"')
        # Truncate to 128 chars
        return value[:128]

    async def record_inbound(self, data: dict[str, Any]) -> None:
        """Record inbound HTTP request metrics.

        Args:
            data: Request data dict.
        """
        labels = [
            data["method"],
            self._sanitize_label(data.get("route", "unknown")),
            str(data["status_code"]),
        ]

        # Increment counter
        await self._storage.update_counter({
            "name": f"{self._namespace}_http_requests_total",
            "help": "Total number of HTTP requests",
            "type": "counter",
            "labelNames": ["method", "route", "status_code"],
            "labelValues": labels,
            "value": 1,
        })

        # Observe histogram
        await self._storage.update_histogram({
            "name": f"{self._namespace}_http_request_duration_seconds",
            "help": "HTTP request duration in seconds",
            "type": "histogram",
            "labelNames": ["method", "route", "status_code"],
            "labelValues": labels,
            "value": data["duration"],
            "buckets": self._config.prometheus.buckets,
        })

    async def record_outbound(self, data: dict[str, Any]) -> None:
        """Record outbound HTTP request metrics.

        Args:
            data: Request data dict.
        """
        labels = [
            data["method"],
            self._sanitize_label(data.get("host", "unknown")),
            str(data.get("status_code", 0)),
        ]

        # Increment counter
        await self._storage.update_counter({
            "name": f"{self._namespace}_http_outbound_requests_total",
            "help": "Total number of outbound HTTP requests",
            "type": "counter",
            "labelNames": ["method", "host", "status_code"],
            "labelValues": labels,
            "value": 1,
        })

        # Observe histogram
        await self._storage.update_histogram({
            "name": f"{self._namespace}_http_outbound_duration_seconds",
            "help": "Outbound HTTP request duration in seconds",
            "type": "histogram",
            "labelNames": ["method", "host", "status_code"],
            "labelValues": labels,
            "value": data["duration"],
            "buckets": self._config.prometheus.buckets,
        })

    async def record_exception(
        self,
        exception: BaseException,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record exception metrics.

        Args:
            exception: The exception that was raised.
            context: Optional context dict.
        """
        import os

        # Get exception class name
        exception_class = type(exception).__name__

        # Get file from traceback
        file_name = "unknown"
        if exception.__traceback__:
            file_name = os.path.basename(
                exception.__traceback__.tb_frame.f_code.co_filename
            )

        labels = [
            self._sanitize_label(exception_class),
            self._sanitize_label(file_name),
        ]

        await self._storage.update_counter({
            "name": f"{self._namespace}_exceptions_total",
            "help": "Total number of exceptions",
            "type": "counter",
            "labelNames": ["exception_class", "file"],
            "labelValues": labels,
            "value": 1,
        })

    async def increment_counter(
        self,
        name: str,
        labels: Optional[dict[str, str]] = None,
        value: float = 1.0,
    ) -> None:
        """Increment a custom counter metric.

        Args:
            name: Metric name.
            labels: Optional label dict.
            value: Value to increment by.
        """
        labels = labels or {}
        sanitized_name = self._sanitize_name(name)

        await self._storage.update_counter({
            "name": f"{self._namespace}_{sanitized_name}",
            "help": f"Custom counter: {name}",
            "type": "counter",
            "labelNames": list(labels.keys()),
            "labelValues": [self._sanitize_label(v) for v in labels.values()],
            "value": value,
        })

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
            labels: Optional label dict.
        """
        labels = labels or {}
        sanitized_name = self._sanitize_name(name)

        await self._storage.update_gauge({
            "name": f"{self._namespace}_{sanitized_name}",
            "help": f"Custom gauge: {name}",
            "type": "gauge",
            "labelNames": list(labels.keys()),
            "labelValues": [self._sanitize_label(v) for v in labels.values()],
            "value": value,
            "command": "set",
        })

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
            labels: Optional label dict.
        """
        labels = labels or {}
        sanitized_name = self._sanitize_name(name)

        await self._storage.update_histogram({
            "name": f"{self._namespace}_{sanitized_name}",
            "help": f"Custom histogram: {name}",
            "type": "histogram",
            "labelNames": list(labels.keys()),
            "labelValues": [self._sanitize_label(v) for v in labels.values()],
            "value": value,
            "buckets": self._config.prometheus.buckets,
        })

    async def get_output(self) -> str:
        """Get metrics output in Prometheus text format.

        Returns:
            Prometheus exposition format text.
        """
        metrics = await self._storage.collect()
        return self._render_text_format(metrics)

    def _render_text_format(self, metrics: list[dict[str, Any]]) -> str:
        """Render metrics in Prometheus exposition format.

        Args:
            metrics: List of metric dicts.

        Returns:
            Prometheus text format string.
        """
        lines: list[str] = []

        for metric in metrics:
            name = metric["name"]
            metric_type = metric["type"]
            help_text = metric.get("help", "")

            # HELP and TYPE lines
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} {metric_type}")

            # Sample lines
            for sample in metric.get("samples", []):
                sample_name = sample["name"]
                label_names = sample.get("labelNames", [])
                label_values = sample.get("labelValues", [])
                value = sample["value"]

                # Build labels string
                if label_names and label_values:
                    label_pairs = []
                    for n, v in zip(label_names, label_values):
                        escaped_v = self._sanitize_label(str(v))
                        label_pairs.append(f'{n}="{escaped_v}"')
                    labels_str = "{" + ",".join(label_pairs) + "}"
                else:
                    labels_str = ""

                # Format value
                if isinstance(value, float) and value.is_integer():
                    value_str = str(int(value))
                else:
                    value_str = str(value)

                lines.append(f"{sample_name}{labels_str} {value_str}")

            lines.append("")  # Empty line between metrics

        return "\n".join(lines)

    async def flush(self) -> None:
        """Flush any buffered data (no-op for Prometheus)."""
        pass

    async def close(self) -> None:
        """Close storage connections."""
        await self._storage.close()
