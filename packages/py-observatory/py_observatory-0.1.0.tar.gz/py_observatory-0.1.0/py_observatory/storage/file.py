"""File-based storage adapter for py-observatory."""

import asyncio
import contextlib
import json
import os
from pathlib import Path
from typing import Any

from ..config import FileStorageConfig

try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False
    aiofiles = None  # type: ignore


class FileStorage:
    """File-based storage adapter for Prometheus metrics."""

    def __init__(self, config: FileStorageConfig) -> None:
        """Initialize file storage.

        Args:
            config: File storage configuration.

        Raises:
            ImportError: If aiofiles package is not installed.
        """
        if not AIOFILES_AVAILABLE:
            raise ImportError(
                "aiofiles package is required for file storage. "
                "Install with: pip install py-observatory[file]"
            )

        self._config = config
        self._path = Path(config.path)
        self._lock = asyncio.Lock()
        self._data: dict[str, Any] = {
            "counters": {},
            "gauges": {},
            "histograms": {},
        }
        self._dirty = False
        self._loaded = False

    async def _ensure_directory(self) -> None:
        """Ensure parent directory exists."""
        self._path.parent.mkdir(parents=True, exist_ok=True)

    async def _load(self) -> None:
        """Load data from file if not already loaded."""
        if self._loaded:
            return

        if self._path.exists():
            async with aiofiles.open(self._path, "r") as f:
                content = await f.read()
                if content:
                    with contextlib.suppress(json.JSONDecodeError):
                        self._data = json.loads(content)

        self._loaded = True

    async def _save(self) -> None:
        """Save data to file if dirty."""
        if not self._dirty:
            return

        await self._ensure_directory()
        async with aiofiles.open(self._path, "w") as f:
            await f.write(json.dumps(self._data, indent=2))

        self._dirty = False

    async def update_counter(self, data: dict[str, Any]) -> None:
        """Update a counter metric."""
        async with self._lock:
            await self._load()

            key = f"{data['name']}:{json.dumps(data['labelValues'])}"

            if key not in self._data["counters"]:
                self._data["counters"][key] = {
                    "meta": {
                        "name": data["name"],
                        "help": data["help"],
                        "type": data["type"],
                        "labelNames": data["labelNames"],
                    },
                    "labelValues": data["labelValues"],
                    "value": 0,
                }

            self._data["counters"][key]["value"] += data["value"]
            self._dirty = True
            await self._save()

    async def update_gauge(self, data: dict[str, Any]) -> None:
        """Update a gauge metric."""
        async with self._lock:
            await self._load()

            key = f"{data['name']}:{json.dumps(data['labelValues'])}"

            if key not in self._data["gauges"]:
                self._data["gauges"][key] = {
                    "meta": {
                        "name": data["name"],
                        "help": data["help"],
                        "type": data["type"],
                        "labelNames": data["labelNames"],
                    },
                    "labelValues": data["labelValues"],
                    "value": 0,
                }

            command = data.get("command", "set")
            if command == "set":
                self._data["gauges"][key]["value"] = data["value"]
            else:
                self._data["gauges"][key]["value"] += data["value"]

            self._dirty = True
            await self._save()

    async def update_histogram(self, data: dict[str, Any]) -> None:
        """Update a histogram metric."""
        async with self._lock:
            await self._load()

            key = f"{data['name']}:{json.dumps(data['labelValues'])}"

            if key not in self._data["histograms"]:
                self._data["histograms"][key] = {
                    "meta": {
                        "name": data["name"],
                        "help": data["help"],
                        "type": data["type"],
                        "labelNames": data["labelNames"],
                        "buckets": data["buckets"],
                    },
                    "labelValues": data["labelValues"],
                    "buckets": {str(b): 0 for b in data["buckets"]},
                    "sum": 0,
                    "count": 0,
                }
                self._data["histograms"][key]["buckets"]["+Inf"] = 0

            hist = self._data["histograms"][key]

            # Find bucket to increment
            bucket_to_increase = "+Inf"
            for bucket in data["buckets"]:
                if data["value"] <= bucket:
                    bucket_to_increase = str(bucket)
                    break

            hist["buckets"][bucket_to_increase] += 1
            hist["sum"] += data["value"]
            hist["count"] += 1

            self._dirty = True
            await self._save()

    async def collect(self) -> list[dict[str, Any]]:
        """Collect all metrics from file."""
        async with self._lock:
            await self._load()
            metrics = []

            # Group counters by name
            counter_groups: dict[str, dict[str, Any]] = {}
            for _key, counter in self._data["counters"].items():
                name = counter["meta"]["name"]
                if name not in counter_groups:
                    counter_groups[name] = {
                        "meta": counter["meta"],
                        "samples": [],
                    }
                counter_groups[name]["samples"].append({
                    "name": name,
                    "labelNames": counter["meta"]["labelNames"],
                    "labelValues": counter["labelValues"],
                    "value": counter["value"],
                })

            for _name, data in sorted(counter_groups.items()):
                metrics.append({
                    "name": data["meta"]["name"],
                    "help": data["meta"]["help"],
                    "type": "counter",
                    "labelNames": data["meta"]["labelNames"],
                    "samples": data["samples"],
                })

            # Group gauges by name
            gauge_groups: dict[str, dict[str, Any]] = {}
            for _key, gauge in self._data["gauges"].items():
                name = gauge["meta"]["name"]
                if name not in gauge_groups:
                    gauge_groups[name] = {
                        "meta": gauge["meta"],
                        "samples": [],
                    }
                gauge_groups[name]["samples"].append({
                    "name": name,
                    "labelNames": gauge["meta"]["labelNames"],
                    "labelValues": gauge["labelValues"],
                    "value": gauge["value"],
                })

            for _name, data in sorted(gauge_groups.items()):
                metrics.append({
                    "name": data["meta"]["name"],
                    "help": data["meta"]["help"],
                    "type": "gauge",
                    "labelNames": data["meta"]["labelNames"],
                    "samples": data["samples"],
                })

            # Collect histograms
            histogram_groups: dict[str, dict[str, Any]] = {}
            for _key, hist in self._data["histograms"].items():
                name = hist["meta"]["name"]
                if name not in histogram_groups:
                    histogram_groups[name] = {
                        "meta": hist["meta"],
                        "samples_data": [],
                    }
                histogram_groups[name]["samples_data"].append(hist)

            for _name, data in sorted(histogram_groups.items()):
                metric = self._collect_histogram(data)
                metrics.append(metric)

            return metrics

    def _collect_histogram(self, data: dict[str, Any]) -> dict[str, Any]:
        """Collect and compute histogram buckets."""
        meta = data["meta"]
        buckets = list(meta["buckets"]) + ["+Inf"]

        metric = {
            "name": meta["name"],
            "help": meta["help"],
            "type": "histogram",
            "labelNames": meta["labelNames"],
            "buckets": buckets,
            "samples": [],
        }

        for hist in data["samples_data"]:
            label_values = hist["labelValues"]

            # Compute cumulative bucket counts
            cumulative = 0
            for bucket in buckets:
                bucket_str = str(bucket)
                cumulative += hist["buckets"].get(bucket_str, 0)

                metric["samples"].append({
                    "name": f"{meta['name']}_bucket",
                    "labelNames": meta["labelNames"] + ["le"],
                    "labelValues": label_values + [bucket_str],
                    "value": cumulative,
                })

            metric["samples"].append({
                "name": f"{meta['name']}_count",
                "labelNames": meta["labelNames"],
                "labelValues": label_values,
                "value": hist["count"],
            })

            metric["samples"].append({
                "name": f"{meta['name']}_sum",
                "labelNames": meta["labelNames"],
                "labelValues": label_values,
                "value": hist["sum"],
            })

        return metric

    async def wipe(self) -> None:
        """Clear all metrics."""
        async with self._lock:
            self._data = {"counters": {}, "gauges": {}, "histograms": {}}
            self._loaded = True

            if self._path.exists():
                os.remove(self._path)

    async def close(self) -> None:
        """Close storage and save pending data."""
        async with self._lock:
            await self._save()
