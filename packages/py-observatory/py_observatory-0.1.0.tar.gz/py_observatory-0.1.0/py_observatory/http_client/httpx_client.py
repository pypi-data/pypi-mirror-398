"""Instrumented httpx client wrapper for py-observatory."""

import time
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from ..collectors.outbound import OutboundCollector


class ObservedHTTPXClient:
    """Instrumented httpx client wrapper for outbound request monitoring."""

    def __init__(
        self,
        collector: OutboundCollector,
        client: Optional[httpx.AsyncClient] = None,
        **client_kwargs: Any,
    ) -> None:
        """Initialize observed HTTP client.

        Args:
            collector: Outbound request collector.
            client: Optional existing httpx client to wrap.
            **client_kwargs: Arguments to pass to httpx.AsyncClient.
        """
        self._collector = collector
        self._client = client
        self._client_kwargs = client_kwargs
        self._owns_client = client is None

    async def __aenter__(self) -> "ObservedHTTPXClient":
        """Enter async context manager."""
        if self._client is None:
            self._client = httpx.AsyncClient(**self._client_kwargs)
        if self._owns_client:
            await self._client.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        if self._owns_client and self._client:
            await self._client.__aexit__(*args)

    def _parse_url(self, url: str) -> tuple[str, str]:
        """Parse URL into host and path.

        Args:
            url: URL string.

        Returns:
            Tuple of (host, path).
        """
        parsed = urlparse(url)
        host = parsed.netloc or parsed.hostname or "unknown"
        path = parsed.path or "/"
        return host, path

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with monitoring.

        Args:
            method: HTTP method.
            url: Request URL.
            **kwargs: Additional request arguments.

        Returns:
            HTTP response.

        Raises:
            Any exception from httpx.
        """
        if self._client is None:
            raise RuntimeError("Client not initialized. Use async context manager.")

        host, path = self._parse_url(url)

        start_time = time.perf_counter()
        error: Optional[str] = None
        status_code = 0

        try:
            response = await self._client.request(method, url, **kwargs)
            status_code = response.status_code
            return response
        except Exception as e:
            error = str(e)
            raise
        finally:
            duration = time.perf_counter() - start_time

            if self._collector.should_monitor(host):
                await self._collector.record(
                    method=method,
                    host=host,
                    path=path,
                    status_code=status_code,
                    duration=duration,
                    error=error,
                )

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a GET request.

        Args:
            url: Request URL.
            **kwargs: Additional request arguments.

        Returns:
            HTTP response.
        """
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a POST request.

        Args:
            url: Request URL.
            **kwargs: Additional request arguments.

        Returns:
            HTTP response.
        """
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a PUT request.

        Args:
            url: Request URL.
            **kwargs: Additional request arguments.

        Returns:
            HTTP response.
        """
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a PATCH request.

        Args:
            url: Request URL.
            **kwargs: Additional request arguments.

        Returns:
            HTTP response.
        """
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a DELETE request.

        Args:
            url: Request URL.
            **kwargs: Additional request arguments.

        Returns:
            HTTP response.
        """
        return await self.request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a HEAD request.

        Args:
            url: Request URL.
            **kwargs: Additional request arguments.

        Returns:
            HTTP response.
        """
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make an OPTIONS request.

        Args:
            url: Request URL.
            **kwargs: Additional request arguments.

        Returns:
            HTTP response.
        """
        return await self.request("OPTIONS", url, **kwargs)
