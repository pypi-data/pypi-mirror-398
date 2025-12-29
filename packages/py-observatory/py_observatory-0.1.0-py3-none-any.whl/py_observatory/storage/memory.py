"""In-memory storage adapter for py-observatory."""

import asyncio
import base64
import json
from typing import Any


class MemoryStorage:
    """Thread-safe in-memory storage adapter for Prometheus metrics."""

    def __init__(self) -> None:
        """Initialize memory storage."""
        self._lock = asyncio.Lock()
        self._counters: dict[str, dict[str, Any]] = {}
        self._gauges: dict[str, dict[str, Any]] = {}
        self._histograms: dict[str, dict[str, Any]] = {}

    def _encode_labels(self, values: list[str]) -> str:
        """Encode label values to a unique key."""
        return base64.b64encode(json.dumps(values).encode()).decode()

    def _decode_labels(self, encoded: str) -> list[str]:
        """Decode label values from key."""
        return json.loads(base64.b64decode(encoded.encode()).decode())

    def _meta_key(self, data: dict[str, Any]) -> str:
        """Generate metadata key for a metric."""
        return f"{data['type']}:{data['name']}"

    def _value_key(self, data: dict[str, Any]) -> str:
        """Generate value key for a metric sample."""
        encoded = self._encode_labels(data["labelValues"])
        return f"{data['name']}:{encoded}"

    async def update_counter(self, data: dict[str, Any]) -> None:
        """Update a counter metric."""
        async with self._lock:
            meta_key = self._meta_key(data)
            value_key = self._value_key(data)

            if meta_key not in self._counters:
                self._counters[meta_key] = {
                    "meta": {
                        "name": data["name"],
                        "help": data["help"],
                        "type": data["type"],
                        "labelNames": data["labelNames"],
                    },
                    "samples": {},
                }

            samples = self._counters[meta_key]["samples"]
            if value_key not in samples:
                samples[value_key] = {
                    "labelValues": data["labelValues"],
                    "value": 0,
                }

            samples[value_key]["value"] += data["value"]

    async def update_gauge(self, data: dict[str, Any]) -> None:
        """Update a gauge metric."""
        async with self._lock:
            meta_key = self._meta_key(data)
            value_key = self._value_key(data)

            if meta_key not in self._gauges:
                self._gauges[meta_key] = {
                    "meta": {
                        "name": data["name"],
                        "help": data["help"],
                        "type": data["type"],
                        "labelNames": data["labelNames"],
                    },
                    "samples": {},
                }

            samples = self._gauges[meta_key]["samples"]
            command = data.get("command", "set")

            if value_key not in samples:
                samples[value_key] = {
                    "labelValues": data["labelValues"],
                    "value": 0,
                }

            if command == "set":
                samples[value_key]["value"] = data["value"]
            else:  # increment
                samples[value_key]["value"] += data["value"]

    async def update_histogram(self, data: dict[str, Any]) -> None:
        """Update a histogram metric."""
        async with self._lock:
            meta_key = self._meta_key(data)
            value_key = self._value_key(data)

            if meta_key not in self._histograms:
                self._histograms[meta_key] = {
                    "meta": {
                        "name": data["name"],
                        "help": data["help"],
                        "type": data["type"],
                        "labelNames": data["labelNames"],
                        "buckets": data["buckets"],
                    },
                    "samples": {},
                }

            samples = self._histograms[meta_key]["samples"]

            if value_key not in samples:
                samples[value_key] = {
                    "labelValues": data["labelValues"],
                    "buckets": {str(b): 0 for b in data["buckets"]},
                    "sum": 0,
                    "count": 0,
                }
                samples[value_key]["buckets"]["+Inf"] = 0

            sample = samples[value_key]

            # Find the bucket to increment
            bucket_to_increase = "+Inf"
            for bucket in data["buckets"]:
                if data["value"] <= bucket:
                    bucket_to_increase = str(bucket)
                    break

            sample["buckets"][bucket_to_increase] += 1
            sample["sum"] += data["value"]
            sample["count"] += 1

    async def collect(self) -> list[dict[str, Any]]:
        """Collect all metrics for rendering."""
        async with self._lock:
            metrics = []

            # Collect counters
            for meta_key in sorted(self._counters.keys()):
                counter = self._counters[meta_key]
                meta = counter["meta"]

                metric = {
                    "name": meta["name"],
                    "help": meta["help"],
                    "type": "counter",
                    "labelNames": meta["labelNames"],
                    "samples": [],
                }

                for sample_data in counter["samples"].values():
                    metric["samples"].append({
                        "name": meta["name"],
                        "labelNames": meta["labelNames"],
                        "labelValues": sample_data["labelValues"],
                        "value": sample_data["value"],
                    })

                metrics.append(metric)

            # Collect gauges
            for meta_key in sorted(self._gauges.keys()):
                gauge = self._gauges[meta_key]
                meta = gauge["meta"]

                metric = {
                    "name": meta["name"],
                    "help": meta["help"],
                    "type": "gauge",
                    "labelNames": meta["labelNames"],
                    "samples": [],
                }

                for sample_data in gauge["samples"].values():
                    metric["samples"].append({
                        "name": meta["name"],
                        "labelNames": meta["labelNames"],
                        "labelValues": sample_data["labelValues"],
                        "value": sample_data["value"],
                    })

                metrics.append(metric)

            # Collect histograms
            for meta_key in sorted(self._histograms.keys()):
                histogram = self._histograms[meta_key]
                metric = self._collect_histogram(histogram)
                metrics.append(metric)

            return metrics

    def _collect_histogram(self, histogram: dict[str, Any]) -> dict[str, Any]:
        """Collect and compute histogram buckets with cumulative counts."""
        meta = histogram["meta"]
        buckets = list(meta["buckets"]) + ["+Inf"]

        metric = {
            "name": meta["name"],
            "help": meta["help"],
            "type": "histogram",
            "labelNames": meta["labelNames"],
            "buckets": buckets,
            "samples": [],
        }

        for sample_data in histogram["samples"].values():
            label_values = sample_data["labelValues"]

            # Compute cumulative bucket counts
            cumulative = 0
            for bucket in buckets:
                bucket_str = str(bucket)
                cumulative += sample_data["buckets"].get(bucket_str, 0)

                metric["samples"].append({
                    "name": f"{meta['name']}_bucket",
                    "labelNames": meta["labelNames"] + ["le"],
                    "labelValues": label_values + [bucket_str],
                    "value": cumulative,
                })

            # Add count
            metric["samples"].append({
                "name": f"{meta['name']}_count",
                "labelNames": meta["labelNames"],
                "labelValues": label_values,
                "value": sample_data["count"],
            })

            # Add sum
            metric["samples"].append({
                "name": f"{meta['name']}_sum",
                "labelNames": meta["labelNames"],
                "labelValues": label_values,
                "value": sample_data["sum"],
            })

        return metric

    async def wipe(self) -> None:
        """Clear all stored metrics."""
        async with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()

    async def close(self) -> None:
        """Close storage (no-op for memory storage)."""
        pass
