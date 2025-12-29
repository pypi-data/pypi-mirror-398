"""FastAPI middleware for inbound request monitoring."""

import time
from collections.abc import Awaitable
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from ..collectors.inbound import InboundCollector


class ObservatoryMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for inbound HTTP request monitoring."""

    def __init__(self, app: ASGIApp, collector: InboundCollector) -> None:
        """Initialize middleware.

        Args:
            app: ASGI application.
            collector: Inbound request collector.
        """
        super().__init__(app)
        self._collector = collector

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request and record metrics.

        Args:
            request: Incoming request.
            call_next: Next middleware/handler.

        Returns:
            Response from the application.
        """
        # Check if we should monitor this request
        if not self._collector.should_monitor(request):
            return await call_next(request)

        # Start timing
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.perf_counter() - start_time

        # Record metrics
        await self._collector.record(request, response, duration)

        return response
