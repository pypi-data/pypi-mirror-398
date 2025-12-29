"""
py-observatory: FastAPI Prometheus monitoring package.

A Python package that provides comprehensive observability for FastAPI
applications, inspired by Laravel Observatory.

Example:
    from fastapi import FastAPI
    from py_observatory import Observatory

    app = FastAPI()
    observatory = Observatory()
    observatory.instrument(app)

    # Outbound request monitoring
    @app.get("/external")
    async def external():
        async with observatory.create_http_client() as client:
            return await client.get("https://api.example.com/data")

    # Custom metrics
    @app.post("/orders")
    async def create_order():
        await observatory.increment("orders_created", {"type": "online"})
        return {"status": "created"}
"""

__version__ = "0.1.0"

from .collectors.cronjob import CronjobCollector, JobInfo, JobStatus
from .config import (
    AuthConfig,
    ExceptionConfig,
    FileStorageConfig,
    InboundConfig,
    ObservatoryConfig,
    OutboundConfig,
    PrometheusConfig,
    RedisConfig,
    StorageType,
)
from .exporters.prometheus import PrometheusExporter
from .http_client.httpx_client import ObservedHTTPXClient
from .middleware.inbound import ObservatoryMiddleware
from .observatory import Observatory

__all__ = [
    # Main class
    "Observatory",
    # Configuration
    "ObservatoryConfig",
    "PrometheusConfig",
    "InboundConfig",
    "OutboundConfig",
    "ExceptionConfig",
    "AuthConfig",
    "RedisConfig",
    "FileStorageConfig",
    "StorageType",
    # Components (for advanced usage)
    "ObservatoryMiddleware",
    "PrometheusExporter",
    "ObservedHTTPXClient",
    # Cronjob monitoring
    "CronjobCollector",
    "JobInfo",
    "JobStatus",
]
