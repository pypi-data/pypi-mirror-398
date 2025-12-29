"""Main Observatory facade class for py-observatory."""

from typing import Any, Callable, Optional

from fastapi import FastAPI

from .collectors.cronjob import CronjobCollector, JobInfo
from .collectors.inbound import InboundCollector
from .collectors.outbound import OutboundCollector
from .config import ObservatoryConfig
from .exceptions.handler import ObservatoryExceptionHandler
from .exporters.prometheus import PrometheusExporter
from .http_client.httpx_client import ObservedHTTPXClient
from .middleware.inbound import ObservatoryMiddleware
from .routes.metrics import create_metrics_router


class Observatory:
    """Main Observatory facade class.

    This class provides a simple interface to instrument a FastAPI application
    with Prometheus metrics. It handles:
    - Inbound HTTP request monitoring
    - Outbound HTTP request monitoring
    - Exception tracking
    - Cronjob/scheduled task monitoring
    - Custom metrics
    """

    def __init__(self, config: Optional[ObservatoryConfig] = None) -> None:
        """Initialize Observatory.

        Args:
            config: Optional configuration. If not provided, loads from
                    environment variables.
        """
        self._config = config or ObservatoryConfig.from_env()
        self._exporter = PrometheusExporter(self._config)
        self._inbound_collector = InboundCollector(
            self._exporter,
            self._config.inbound,
        )
        self._outbound_collector = OutboundCollector(
            self._exporter,
            self._config.outbound,
        )
        self._cronjob_collector = CronjobCollector(
            self._exporter,
            enabled=self._config.enabled,
        )
        self._exception_handler = ObservatoryExceptionHandler(
            self._exporter,
            self._config.exceptions,
        )

    @property
    def config(self) -> ObservatoryConfig:
        """Get the configuration.

        Returns:
            Observatory configuration.
        """
        return self._config

    @property
    def exporter(self) -> PrometheusExporter:
        """Get the exporter.

        Returns:
            Prometheus exporter.
        """
        return self._exporter

    def instrument(self, app: FastAPI) -> "Observatory":
        """Instrument a FastAPI application with Observatory monitoring.

        This method adds:
        - Middleware for inbound request tracking
        - /metrics endpoint for Prometheus scraping
        - Exception handler for tracking exceptions

        Args:
            app: FastAPI application to instrument.

        Returns:
            Self for method chaining.
        """
        if not self._config.enabled:
            return self

        # Add inbound request middleware
        if self._config.inbound.enabled:
            app.add_middleware(
                ObservatoryMiddleware,
                collector=self._inbound_collector,
            )

        # Add metrics endpoint
        metrics_router = create_metrics_router(
            exporter=self._exporter,
            auth_config=self._config.prometheus.auth,
            endpoint=self._config.prometheus.endpoint,
        )
        app.include_router(metrics_router)

        # Install exception handler
        if self._config.exceptions.enabled:
            self._exception_handler.install(app)

        return self

    def create_http_client(self, **kwargs: Any) -> ObservedHTTPXClient:
        """Create an instrumented HTTP client.

        Args:
            **kwargs: Arguments to pass to httpx.AsyncClient.

        Returns:
            Instrumented HTTP client.

        Example:
            async with observatory.create_http_client() as client:
                response = await client.get("https://api.example.com/data")
        """
        return ObservedHTTPXClient(self._outbound_collector, **kwargs)

    async def increment(
        self,
        name: str,
        labels: Optional[dict[str, str]] = None,
        value: float = 1.0,
    ) -> None:
        """Increment a custom counter metric.

        Args:
            name: Metric name.
            labels: Optional label dict.
            value: Value to increment by (default 1).

        Example:
            await observatory.increment("orders_created", {"type": "online"})
        """
        await self._exporter.increment_counter(name, labels, value)

    async def gauge(
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

        Example:
            await observatory.gauge("active_users", 42, {"region": "us-east"})
        """
        await self._exporter.set_gauge(name, value, labels)

    async def histogram(
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

        Example:
            await observatory.histogram("processing_time", 0.5, {"job": "import"})
        """
        await self._exporter.observe_histogram(name, value, labels)

    # ========== Cronjob Monitoring Methods ==========

    @property
    def cronjob(self) -> CronjobCollector:
        """Get the cronjob collector.

        Returns:
            CronjobCollector instance.

        Example:
            # Use as decorator
            @observatory.cronjob.monitor(schedule="*/5 * * * *")
            async def my_job():
                await do_work()

            # Use as context manager
            async with observatory.cronjob.track("my_job", "0 * * * *"):
                await do_work()
        """
        return self._cronjob_collector

    def monitor_job(
        self,
        job_name: Optional[str] = None,
        schedule: str = "",
    ) -> Callable:
        """Decorator for monitoring cronjob/scheduled task functions.

        Args:
            job_name: Name of the job (defaults to function name).
            schedule: Cron expression or schedule description.

        Returns:
            Decorator function.

        Example:
            @observatory.monitor_job(schedule="0 * * * *")
            async def hourly_cleanup():
                await cleanup_old_data()

            @observatory.monitor_job("daily_report", "0 0 * * *")
            def generate_daily_report():
                generate_report()
        """
        return self._cronjob_collector.monitor(job_name, schedule)

    async def track_job(self, job_name: str, schedule: str = ""):
        """Async context manager for tracking job execution.

        Args:
            job_name: Name of the job.
            schedule: Cron expression or schedule description.

        Returns:
            Async context manager.

        Example:
            async with observatory.track_job("data_sync", "*/10 * * * *"):
                await sync_data()
        """
        return self._cronjob_collector.track(job_name, schedule)

    def get_jobs(self) -> list[JobInfo]:
        """Get all registered cronjobs.

        Returns:
            List of JobInfo objects.
        """
        return self._cronjob_collector.get_all_jobs()

    def enabled(self) -> bool:
        """Check if Observatory is enabled.

        Returns:
            True if enabled.
        """
        return self._config.enabled

    async def close(self) -> None:
        """Close Observatory and clean up resources.

        Should be called when shutting down the application.
        """
        await self._exporter.close()
