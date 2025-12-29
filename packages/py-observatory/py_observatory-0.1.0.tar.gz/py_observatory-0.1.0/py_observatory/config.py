"""Configuration module for py-observatory."""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class StorageType(str, Enum):
    """Storage backend types."""
    MEMORY = "memory"
    REDIS = "redis"
    FILE = "file"


@dataclass
class RedisConfig:
    """Redis connection configuration."""
    host: str = "127.0.0.1"
    port: int = 6379
    password: Optional[str] = None
    database: int = 0
    ssl: bool = False
    prefix: str = "OBSERVATORY_"

    @classmethod
    def from_env(cls) -> "RedisConfig":
        """Create config from environment variables."""
        return cls(
            host=os.getenv("OBSERVATORY_REDIS_HOST", "127.0.0.1"),
            port=int(os.getenv("OBSERVATORY_REDIS_PORT", "6379")),
            password=os.getenv("OBSERVATORY_REDIS_PASSWORD"),
            database=int(os.getenv("OBSERVATORY_REDIS_DATABASE", "0")),
            ssl=os.getenv("OBSERVATORY_REDIS_SSL", "false").lower() == "true",
            prefix=os.getenv("OBSERVATORY_REDIS_PREFIX", "OBSERVATORY_"),
        )


@dataclass
class FileStorageConfig:
    """File storage configuration."""
    path: str = "/tmp/observatory_metrics.json"

    @classmethod
    def from_env(cls) -> "FileStorageConfig":
        """Create config from environment variables."""
        return cls(
            path=os.getenv("OBSERVATORY_FILE_PATH", "/tmp/observatory_metrics.json"),
        )


@dataclass
class AuthConfig:
    """Basic auth configuration for metrics endpoint."""
    enabled: bool = False
    username: str = "prometheus"
    password: str = ""

    @classmethod
    def from_env(cls) -> "AuthConfig":
        """Create config from environment variables."""
        return cls(
            enabled=os.getenv("OBSERVATORY_AUTH_ENABLED", "false").lower() == "true",
            username=os.getenv("OBSERVATORY_AUTH_USERNAME", "prometheus"),
            password=os.getenv("OBSERVATORY_AUTH_PASSWORD", ""),
        )


@dataclass
class InboundConfig:
    """Inbound HTTP monitoring configuration."""
    enabled: bool = True
    exclude_paths: list[str] = field(default_factory=lambda: [
        "/metrics",
        "/health",
        "/healthz",
        "/ready",
        "/readyz",
        "/docs",
        "/redoc",
        "/openapi.json",
    ])
    methods: list[str] = field(default_factory=lambda: [
        "GET", "POST", "PUT", "PATCH", "DELETE"
    ])
    exclude_headers: list[str] = field(default_factory=lambda: [
        "authorization",
        "cookie",
        "x-api-key",
        "x-auth-token",
    ])

    @classmethod
    def from_env(cls) -> "InboundConfig":
        """Create config from environment variables."""
        exclude_paths_str = os.getenv("OBSERVATORY_INBOUND_EXCLUDE_PATHS", "")
        methods_str = os.getenv("OBSERVATORY_INBOUND_METHODS", "")

        default = cls()
        return cls(
            enabled=os.getenv("OBSERVATORY_INBOUND_ENABLED", "true").lower() == "true",
            exclude_paths=(
                [p.strip() for p in exclude_paths_str.split(",") if p.strip()]
                if exclude_paths_str else default.exclude_paths
            ),
            methods=(
                [m.strip().upper() for m in methods_str.split(",") if m.strip()]
                if methods_str else default.methods
            ),
        )


@dataclass
class OutboundConfig:
    """Outbound HTTP monitoring configuration."""
    enabled: bool = True
    exclude_hosts: list[str] = field(default_factory=lambda: [
        "localhost",
        "127.0.0.1",
    ])

    @classmethod
    def from_env(cls) -> "OutboundConfig":
        """Create config from environment variables."""
        exclude_hosts_str = os.getenv("OBSERVATORY_OUTBOUND_EXCLUDE_HOSTS", "")

        default = cls()
        return cls(
            enabled=os.getenv("OBSERVATORY_OUTBOUND_ENABLED", "true").lower() == "true",
            exclude_hosts=(
                [h.strip() for h in exclude_hosts_str.split(",") if h.strip()]
                if exclude_hosts_str else default.exclude_hosts
            ),
        )


@dataclass
class ExceptionConfig:
    """Exception tracking configuration."""
    enabled: bool = True
    ignore_exceptions: list[str] = field(default_factory=lambda: [
        "starlette.exceptions.HTTPException",
        "fastapi.exceptions.RequestValidationError",
    ])

    @classmethod
    def from_env(cls) -> "ExceptionConfig":
        """Create config from environment variables."""
        ignore_str = os.getenv("OBSERVATORY_EXCEPTION_IGNORE", "")

        default = cls()
        return cls(
            enabled=os.getenv("OBSERVATORY_EXCEPTION_ENABLED", "true").lower() == "true",
            ignore_exceptions=(
                [e.strip() for e in ignore_str.split(",") if e.strip()]
                if ignore_str else default.ignore_exceptions
            ),
        )


@dataclass
class PrometheusConfig:
    """Prometheus-specific configuration."""
    endpoint: str = "/metrics"
    storage: StorageType = StorageType.MEMORY
    buckets: list[float] = field(default_factory=lambda: [
        0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0
    ])
    redis: RedisConfig = field(default_factory=RedisConfig)
    file: FileStorageConfig = field(default_factory=FileStorageConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)

    @classmethod
    def from_env(cls) -> "PrometheusConfig":
        """Create config from environment variables."""
        storage_str = os.getenv("OBSERVATORY_STORAGE", "memory")
        buckets_str = os.getenv("OBSERVATORY_BUCKETS", "")

        default = cls()
        return cls(
            endpoint=os.getenv("OBSERVATORY_ENDPOINT", "/metrics"),
            storage=StorageType(storage_str),
            buckets=(
                [float(b.strip()) for b in buckets_str.split(",") if b.strip()]
                if buckets_str else default.buckets
            ),
            redis=RedisConfig.from_env(),
            file=FileStorageConfig.from_env(),
            auth=AuthConfig.from_env(),
        )


@dataclass
class ObservatoryConfig:
    """Main Observatory configuration."""
    enabled: bool = True
    app_name: str = "fastapi"
    prometheus: PrometheusConfig = field(default_factory=PrometheusConfig)
    inbound: InboundConfig = field(default_factory=InboundConfig)
    outbound: OutboundConfig = field(default_factory=OutboundConfig)
    exceptions: ExceptionConfig = field(default_factory=ExceptionConfig)
    labels: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "ObservatoryConfig":
        """Create config from environment variables."""
        labels_str = os.getenv("OBSERVATORY_LABELS", "")
        labels: dict[str, str] = {}

        if labels_str:
            for pair in labels_str.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    labels[key.strip()] = value.strip()

        if not labels:
            labels = {"environment": os.getenv("APP_ENV", "production")}

        return cls(
            enabled=os.getenv("OBSERVATORY_ENABLED", "true").lower() == "true",
            app_name=os.getenv("OBSERVATORY_APP_NAME", os.getenv("APP_NAME", "fastapi")),
            prometheus=PrometheusConfig.from_env(),
            inbound=InboundConfig.from_env(),
            outbound=OutboundConfig.from_env(),
            exceptions=ExceptionConfig.from_env(),
            labels=labels,
        )
