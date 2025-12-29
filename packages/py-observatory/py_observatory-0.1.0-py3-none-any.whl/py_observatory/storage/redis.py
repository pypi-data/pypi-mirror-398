"""Redis storage adapter for py-observatory."""

import json
from collections import defaultdict
from typing import Any, Optional

from ..config import RedisConfig

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None  # type: ignore


class RedisStorage:
    """Async Redis storage adapter for Prometheus metrics."""

    METRIC_KEYS_SUFFIX = "_METRIC_KEYS"

    def __init__(self, config: RedisConfig) -> None:
        """Initialize Redis storage.

        Args:
            config: Redis connection configuration.

        Raises:
            ImportError: If redis package is not installed.
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis package is required for Redis storage. "
                "Install with: pip install py-observatory[redis]"
            )

        self._config = config
        self._prefix = config.prefix
        self._client: Optional[aioredis.Redis] = None  # type: ignore

    async def _get_client(self) -> "aioredis.Redis":  # type: ignore
        """Get or create Redis client."""
        if self._client is None:
            self._client = aioredis.Redis(
                host=self._config.host,
                port=self._config.port,
                password=self._config.password,
                db=self._config.database,
                ssl=self._config.ssl,
                decode_responses=True,
            )
        return self._client

    def _metric_key(self, data: dict[str, Any]) -> str:
        """Generate Redis key for a metric."""
        return f"{self._prefix}{data['type']}:{data['name']}"

    def _keys_set_key(self, metric_type: str) -> str:
        """Generate key for the set of metric keys."""
        return f"{self._prefix}{metric_type}{self.METRIC_KEYS_SUFFIX}"

    async def update_counter(self, data: dict[str, Any]) -> None:
        """Update a counter metric in Redis."""
        client = await self._get_client()
        metric_key = self._metric_key(data)
        keys_set = self._keys_set_key("counter")

        meta_data = {
            "name": data["name"],
            "help": data["help"],
            "type": data["type"],
            "labelNames": data["labelNames"],
        }

        label_key = json.dumps(data["labelValues"])

        async with client.pipeline(transaction=True) as pipe:
            await pipe.hincrbyfloat(metric_key, label_key, data["value"])
            await pipe.hset(metric_key, "__meta", json.dumps(meta_data))
            await pipe.sadd(keys_set, metric_key)
            await pipe.execute()

    async def update_gauge(self, data: dict[str, Any]) -> None:
        """Update a gauge metric in Redis."""
        client = await self._get_client()
        metric_key = self._metric_key(data)
        keys_set = self._keys_set_key("gauge")

        meta_data = {
            "name": data["name"],
            "help": data["help"],
            "type": data["type"],
            "labelNames": data["labelNames"],
        }

        label_key = json.dumps(data["labelValues"])
        command = data.get("command", "set")

        async with client.pipeline(transaction=True) as pipe:
            if command == "set":
                await pipe.hset(metric_key, label_key, data["value"])
            else:
                await pipe.hincrbyfloat(metric_key, label_key, data["value"])
            await pipe.hset(metric_key, "__meta", json.dumps(meta_data))
            await pipe.sadd(keys_set, metric_key)
            await pipe.execute()

    async def update_histogram(self, data: dict[str, Any]) -> None:
        """Update a histogram metric in Redis."""
        client = await self._get_client()
        metric_key = self._metric_key(data)
        keys_set = self._keys_set_key("histogram")

        meta_data = {
            "name": data["name"],
            "help": data["help"],
            "type": data["type"],
            "labelNames": data["labelNames"],
            "buckets": data["buckets"],
        }

        # Find bucket to increment
        bucket_to_increase = "+Inf"
        for bucket in data["buckets"]:
            if data["value"] <= bucket:
                bucket_to_increase = str(bucket)
                break

        sum_key = json.dumps({"b": "sum", "labelValues": data["labelValues"]})
        bucket_key = json.dumps({"b": bucket_to_increase, "labelValues": data["labelValues"]})
        count_key = json.dumps({"b": "count", "labelValues": data["labelValues"]})

        async with client.pipeline(transaction=True) as pipe:
            await pipe.hincrbyfloat(metric_key, sum_key, data["value"])
            await pipe.hincrby(metric_key, bucket_key, 1)
            await pipe.hincrby(metric_key, count_key, 1)
            await pipe.hset(metric_key, "__meta", json.dumps(meta_data))
            await pipe.sadd(keys_set, metric_key)
            await pipe.execute()

    async def collect(self) -> list[dict[str, Any]]:
        """Collect all metrics from Redis."""
        client = await self._get_client()
        metrics = []

        # Collect counters
        counter_keys = await client.smembers(self._keys_set_key("counter"))
        for key in sorted(counter_keys):
            raw = await client.hgetall(key)
            if "__meta" not in raw:
                continue

            meta = json.loads(raw.pop("__meta"))
            samples = []

            for k, v in raw.items():
                samples.append({
                    "name": meta["name"],
                    "labelNames": meta["labelNames"],
                    "labelValues": json.loads(k),
                    "value": float(v),
                })

            metrics.append({
                "name": meta["name"],
                "help": meta["help"],
                "type": "counter",
                "labelNames": meta["labelNames"],
                "samples": samples,
            })

        # Collect gauges
        gauge_keys = await client.smembers(self._keys_set_key("gauge"))
        for key in sorted(gauge_keys):
            raw = await client.hgetall(key)
            if "__meta" not in raw:
                continue

            meta = json.loads(raw.pop("__meta"))
            samples = []

            for k, v in raw.items():
                samples.append({
                    "name": meta["name"],
                    "labelNames": meta["labelNames"],
                    "labelValues": json.loads(k),
                    "value": float(v),
                })

            metrics.append({
                "name": meta["name"],
                "help": meta["help"],
                "type": "gauge",
                "labelNames": meta["labelNames"],
                "samples": samples,
            })

        # Collect histograms
        histogram_keys = await client.smembers(self._keys_set_key("histogram"))
        for key in sorted(histogram_keys):
            raw = await client.hgetall(key)
            if "__meta" not in raw:
                continue

            meta = json.loads(raw.pop("__meta"))
            metric = self._collect_histogram(meta, raw)
            metrics.append(metric)

        return metrics

    def _collect_histogram(
        self, meta: dict[str, Any], raw: dict[str, str]
    ) -> dict[str, Any]:
        """Collect and compute histogram buckets from Redis data."""
        buckets = list(meta["buckets"]) + ["+Inf"]

        metric = {
            "name": meta["name"],
            "help": meta["help"],
            "type": "histogram",
            "labelNames": meta["labelNames"],
            "buckets": buckets,
            "samples": [],
        }

        # Group by label values
        label_value_data: dict[str, dict[str, float]] = defaultdict(
            lambda: {"sum": 0, "count": 0, "buckets": defaultdict(int)}
        )

        for key, value in raw.items():
            data = json.loads(key)
            label_key = json.dumps(data["labelValues"])
            bucket = data["b"]

            if bucket == "sum":
                label_value_data[label_key]["sum"] = float(value)
            elif bucket == "count":
                label_value_data[label_key]["count"] = int(float(value))
            else:
                label_value_data[label_key]["buckets"][bucket] = int(float(value))

        # Compute cumulative buckets
        for label_key, data in label_value_data.items():
            label_values = json.loads(label_key)

            cumulative = 0
            for bucket in buckets:
                bucket_str = str(bucket)
                cumulative += data["buckets"].get(bucket_str, 0)

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
                "value": data["count"],
            })

            metric["samples"].append({
                "name": f"{meta['name']}_sum",
                "labelNames": meta["labelNames"],
                "labelValues": label_values,
                "value": data["sum"],
            })

        return metric

    async def wipe(self) -> None:
        """Clear all metrics from Redis."""
        client = await self._get_client()
        pattern = f"{self._prefix}*"

        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=pattern)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
