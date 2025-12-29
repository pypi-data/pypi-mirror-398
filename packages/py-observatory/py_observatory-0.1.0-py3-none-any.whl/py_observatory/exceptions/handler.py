"""Exception handler for py-observatory."""

from typing import TYPE_CHECKING, Any, Optional

from fastapi import FastAPI, Request
from starlette.responses import Response

from ..config import ExceptionConfig

if TYPE_CHECKING:
    from ..exporters.base import ExporterProtocol


class ObservatoryExceptionHandler:
    """Exception handler for tracking exceptions."""

    def __init__(
        self,
        exporter: "ExporterProtocol",
        config: ExceptionConfig,
    ) -> None:
        """Initialize exception handler.

        Args:
            exporter: Metrics exporter.
            config: Exception configuration.
        """
        self._exporter = exporter
        self._config = config

    def should_ignore(self, exception: BaseException) -> bool:
        """Check if exception should be ignored.

        Args:
            exception: The exception to check.

        Returns:
            True if exception should be ignored.
        """
        exception_class = f"{type(exception).__module__}.{type(exception).__name__}"
        exception_name = type(exception).__name__

        for ignore_pattern in self._config.ignore_exceptions:
            if exception_class == ignore_pattern:
                return True
            if exception_name == ignore_pattern:
                return True

        return False

    async def record_exception(
        self,
        exception: BaseException,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record an exception.

        Args:
            exception: The exception to record.
            context: Optional context dict.
        """
        if not self._config.enabled:
            return

        if self.should_ignore(exception):
            return

        await self._exporter.record_exception(exception, context)

    def install(self, app: FastAPI) -> None:
        """Install exception tracking on FastAPI app.

        This wraps the default exception handler to track exceptions
        before they are handled by the application.

        Args:
            app: FastAPI application.
        """
        # Get the original exception handler
        original_handler = app.exception_handlers.get(Exception)

        async def observatory_exception_handler(
            request: Request,
            exc: Exception,
        ) -> Response:
            # Record the exception
            await self.record_exception(
                exc,
                {"path": str(request.url.path), "method": request.method},
            )

            # Call original handler if exists, otherwise re-raise
            if original_handler:
                return await original_handler(request, exc)
            raise exc

        # Install our handler
        app.add_exception_handler(Exception, observatory_exception_handler)
