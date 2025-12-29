"""Cronjob/Scheduled task collector for py-observatory."""

import asyncio
import functools
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Callable,
    Optional,
)

if TYPE_CHECKING:
    from ..exporters.base import ExporterProtocol


class JobStatus(str, Enum):
    """Job execution status."""
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"
    SKIPPED = "skipped"


@dataclass
class JobExecution:
    """Represents a single job execution."""
    job_name: str
    schedule: str
    status: JobStatus
    duration: float
    started_at: datetime
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    error_type: Optional[str] = None


@dataclass
class JobInfo:
    """Information about a registered job."""
    name: str
    schedule: str
    description: str = ""
    last_run: Optional[datetime] = None
    last_status: Optional[JobStatus] = None
    last_duration: Optional[float] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0


class CronjobCollector:
    """Collector for cronjob/scheduled task monitoring."""

    def __init__(
        self,
        exporter: "ExporterProtocol",
        enabled: bool = True,
    ) -> None:
        """Initialize cronjob collector.

        Args:
            exporter: Metrics exporter.
            enabled: Whether cronjob monitoring is enabled.
        """
        self._exporter = exporter
        self._enabled = enabled
        self._jobs: dict[str, JobInfo] = {}
        self._current_executions: dict[str, JobExecution] = {}

    def register_job(
        self,
        name: str,
        schedule: str,
        description: str = "",
    ) -> None:
        """Register a job for monitoring.

        Args:
            name: Job name/identifier.
            schedule: Cron expression or schedule description.
            description: Human-readable description.
        """
        if name not in self._jobs:
            self._jobs[name] = JobInfo(
                name=name,
                schedule=schedule,
                description=description,
            )

    def get_job_info(self, name: str) -> Optional[JobInfo]:
        """Get information about a registered job.

        Args:
            name: Job name.

        Returns:
            JobInfo or None if not found.
        """
        return self._jobs.get(name)

    def get_all_jobs(self) -> list[JobInfo]:
        """Get all registered jobs.

        Returns:
            List of JobInfo.
        """
        return list(self._jobs.values())

    async def record_start(
        self,
        job_name: str,
        schedule: str = "",
    ) -> float:
        """Record job start.

        Args:
            job_name: Name of the job.
            schedule: Cron expression or schedule.

        Returns:
            Start time for duration calculation.
        """
        if not self._enabled:
            return time.perf_counter()

        # Register job if not exists
        if job_name not in self._jobs:
            self.register_job(job_name, schedule)

        start_time = time.perf_counter()
        now = datetime.now()

        self._current_executions[job_name] = JobExecution(
            job_name=job_name,
            schedule=schedule or self._jobs[job_name].schedule,
            status=JobStatus.RUNNING,
            duration=0,
            started_at=now,
        )

        # Update gauge for running jobs
        await self._exporter.set_gauge(
            "cronjob_running",
            1,
            {"job": job_name},
        )

        return start_time

    async def record_success(
        self,
        job_name: str,
        start_time: float,
    ) -> None:
        """Record successful job completion.

        Args:
            job_name: Name of the job.
            start_time: Start time from record_start.
        """
        if not self._enabled:
            return

        duration = time.perf_counter() - start_time
        now = datetime.now()

        # Update job info
        if job_name in self._jobs:
            job = self._jobs[job_name]
            job.last_run = now
            job.last_status = JobStatus.SUCCESS
            job.last_duration = duration
            job.run_count += 1
            job.success_count += 1

        # Record metrics
        await self._record_metrics(job_name, JobStatus.SUCCESS, duration)

        # Clear running state
        if job_name in self._current_executions:
            del self._current_executions[job_name]

        await self._exporter.set_gauge(
            "cronjob_running",
            0,
            {"job": job_name},
        )

    async def record_failure(
        self,
        job_name: str,
        start_time: float,
        error: Optional[BaseException] = None,
    ) -> None:
        """Record failed job execution.

        Args:
            job_name: Name of the job.
            start_time: Start time from record_start.
            error: The exception that caused the failure.
        """
        if not self._enabled:
            return

        duration = time.perf_counter() - start_time
        now = datetime.now()

        error_type = type(error).__name__ if error else "Unknown"
        str(error) if error else ""

        # Update job info
        if job_name in self._jobs:
            job = self._jobs[job_name]
            job.last_run = now
            job.last_status = JobStatus.FAILED
            job.last_duration = duration
            job.run_count += 1
            job.failure_count += 1

        # Record metrics
        await self._record_metrics(
            job_name,
            JobStatus.FAILED,
            duration,
            error_type=error_type,
        )

        # Clear running state
        if job_name in self._current_executions:
            del self._current_executions[job_name]

        await self._exporter.set_gauge(
            "cronjob_running",
            0,
            {"job": job_name},
        )

    async def record_skip(
        self,
        job_name: str,
        reason: str = "",
    ) -> None:
        """Record skipped job execution.

        Args:
            job_name: Name of the job.
            reason: Reason for skipping.
        """
        if not self._enabled:
            return

        await self._exporter.increment_counter(
            "cronjob_skipped_total",
            {"job": job_name, "reason": reason or "unknown"},
        )

    async def _record_metrics(
        self,
        job_name: str,
        status: JobStatus,
        duration: float,
        error_type: Optional[str] = None,
    ) -> None:
        """Record job execution metrics.

        Args:
            job_name: Name of the job.
            status: Execution status.
            duration: Execution duration in seconds.
            error_type: Type of error if failed.
        """
        # Counter for total executions
        await self._exporter.increment_counter(
            "cronjob_executions_total",
            {"job": job_name, "status": status.value},
        )

        # Histogram for duration
        await self._exporter.observe_histogram(
            "cronjob_duration_seconds",
            duration,
            {"job": job_name, "status": status.value},
        )

        # Gauge for last execution timestamp
        await self._exporter.set_gauge(
            "cronjob_last_execution_timestamp",
            time.time(),
            {"job": job_name},
        )

        # Gauge for last duration
        await self._exporter.set_gauge(
            "cronjob_last_duration_seconds",
            duration,
            {"job": job_name},
        )

        # Gauge for last status (1=success, 0=failed)
        await self._exporter.set_gauge(
            "cronjob_last_success",
            1 if status == JobStatus.SUCCESS else 0,
            {"job": job_name},
        )

        # Counter for failures with error type
        if status == JobStatus.FAILED and error_type:
            await self._exporter.increment_counter(
                "cronjob_failures_total",
                {"job": job_name, "error_type": error_type},
            )

    @asynccontextmanager
    async def track(
        self,
        job_name: str,
        schedule: str = "",
    ):
        """Async context manager for tracking job execution.

        Args:
            job_name: Name of the job.
            schedule: Cron expression or schedule.

        Yields:
            None

        Example:
            async with collector.track("my_job", "0 * * * *"):
                await do_work()
        """
        start_time = await self.record_start(job_name, schedule)
        try:
            yield
            await self.record_success(job_name, start_time)
        except Exception as e:
            await self.record_failure(job_name, start_time, e)
            raise

    def track_sync(
        self,
        job_name: str,
        schedule: str = "",
    ):
        """Sync context manager for tracking job execution.

        Args:
            job_name: Name of the job.
            schedule: Cron expression or schedule.

        Returns:
            Context manager.

        Example:
            with collector.track_sync("my_job", "0 * * * *"):
                do_work()
        """
        return _SyncJobTracker(self, job_name, schedule)

    def monitor(
        self,
        job_name: Optional[str] = None,
        schedule: str = "",
    ):
        """Decorator for monitoring job functions.

        Args:
            job_name: Name of the job (defaults to function name).
            schedule: Cron expression or schedule.

        Returns:
            Decorator function.

        Example:
            @collector.monitor(schedule="0 * * * *")
            async def my_hourly_job():
                await do_work()

            @collector.monitor("cleanup_job", "0 0 * * *")
            def daily_cleanup():
                do_cleanup()
        """
        def decorator(func: Callable) -> Callable:
            name = job_name or func.__name__

            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    async with self.track(name, schedule):
                        return await func(*args, **kwargs)
                return async_wrapper
            else:
                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    with self.track_sync(name, schedule):
                        return func(*args, **kwargs)
                return sync_wrapper

        return decorator


class _SyncJobTracker:
    """Sync context manager for job tracking."""

    def __init__(
        self,
        collector: CronjobCollector,
        job_name: str,
        schedule: str,
    ) -> None:
        self._collector = collector
        self._job_name = job_name
        self._schedule = schedule
        self._start_time: float = 0
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def __enter__(self) -> "_SyncJobTracker":
        # Get or create event loop
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

        # Record start
        self._start_time = self._loop.run_until_complete(
            self._collector.record_start(self._job_name, self._schedule)
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            self._loop.run_until_complete(
                self._collector.record_success(self._job_name, self._start_time)
            )
        else:
            self._loop.run_until_complete(
                self._collector.record_failure(self._job_name, self._start_time, exc_val)
            )
        return False  # Don't suppress exceptions
