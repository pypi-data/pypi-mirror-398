"""Tests for py-observatory package."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from py_observatory import Observatory, ObservatoryConfig
from py_observatory.config import PrometheusConfig, StorageType


class TestObservatoryConfig:
    """Test configuration classes."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ObservatoryConfig()
        assert config.enabled is True
        assert config.app_name == "fastapi"

    def test_custom_config(self):
        """Test custom configuration."""
        config = ObservatoryConfig(
            enabled=False,
            app_name="myapp",
        )
        assert config.enabled is False
        assert config.app_name == "myapp"

    def test_prometheus_config(self):
        """Test Prometheus configuration."""
        config = PrometheusConfig(
            endpoint="/custom-metrics",
            storage=StorageType.MEMORY,
        )
        assert config.endpoint == "/custom-metrics"
        assert config.storage == StorageType.MEMORY


class TestObservatory:
    """Test Observatory main class."""

    def test_observatory_init(self):
        """Test Observatory initialization."""
        obs = Observatory()
        assert obs is not None

    def test_observatory_with_config(self):
        """Test Observatory with custom config."""
        config = ObservatoryConfig(app_name="testapp")
        obs = Observatory(config)
        assert obs._config.app_name == "testapp"

    def test_observatory_disabled(self):
        """Test Observatory when disabled."""
        config = ObservatoryConfig(enabled=False)
        obs = Observatory(config)
        assert obs._config.enabled is False


class TestCronjobCollector:
    """Test cronjob monitoring."""

    def test_monitor_job_decorator(self):
        """Test monitor_job decorator creates wrapper."""
        obs = Observatory()

        @obs.monitor_job(schedule="* * * * *")
        async def my_job():
            return "done"

        assert callable(my_job)

    def test_monitor_job_with_name(self):
        """Test monitor_job with custom name."""
        obs = Observatory()

        @obs.monitor_job("custom_name", schedule="0 * * * *")
        async def another_job():
            return "done"

        assert callable(another_job)


class TestStorageTypes:
    """Test storage type enum."""

    def test_storage_types_exist(self):
        """Test all storage types are defined."""
        assert StorageType.MEMORY == "memory"
        assert StorageType.REDIS == "redis"
        assert StorageType.FILE == "file"


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test async operations."""

    async def test_increment_metric(self):
        """Test incrementing a counter metric."""
        obs = Observatory()
        # Should not raise
        await obs.increment("test_counter", {"label": "value"})

    async def test_gauge_metric(self):
        """Test setting a gauge metric."""
        obs = Observatory()
        # Should not raise
        await obs.gauge("test_gauge", 42.0, {"label": "value"})

    async def test_histogram_metric(self):
        """Test observing a histogram metric."""
        obs = Observatory()
        # Should not raise
        await obs.histogram("test_histogram", 0.5, {"label": "value"})

    async def test_track_job_context_manager(self):
        """Test track_job context manager."""
        obs = Observatory()
        ctx = await obs.track_job("test_job", "* * * * *")
        async with ctx:
            pass  # Job execution
