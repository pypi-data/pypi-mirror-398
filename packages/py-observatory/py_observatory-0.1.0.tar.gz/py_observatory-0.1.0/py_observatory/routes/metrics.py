"""Metrics endpoint route for py-observatory."""

import secrets
from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from ..config import AuthConfig

if TYPE_CHECKING:
    from ..exporters.base import ExporterProtocol


def create_metrics_router(
    exporter: "ExporterProtocol",
    auth_config: AuthConfig,
    endpoint: str = "/metrics",
) -> APIRouter:
    """Create a FastAPI router for the metrics endpoint.

    Args:
        exporter: Metrics exporter.
        auth_config: Authentication configuration.
        endpoint: Endpoint path (default: /metrics).

    Returns:
        FastAPI router.
    """
    router = APIRouter()
    security = HTTPBasic(auto_error=False)

    async def verify_auth(
        credentials: Optional[HTTPBasicCredentials] = Depends(security),
    ) -> bool:
        """Verify basic auth credentials.

        Args:
            credentials: Optional HTTP basic credentials.

        Returns:
            True if authenticated or auth disabled.
        """
        if not auth_config.enabled:
            return True

        if credentials is None:
            return False

        # Use constant-time comparison to prevent timing attacks
        correct_username = secrets.compare_digest(
            credentials.username.encode("utf8"),
            auth_config.username.encode("utf8"),
        )
        correct_password = secrets.compare_digest(
            credentials.password.encode("utf8"),
            auth_config.password.encode("utf8"),
        )

        return correct_username and correct_password

    @router.get(endpoint)
    async def metrics(
        request: Request,
        authenticated: bool = Depends(verify_auth),
    ) -> Response:
        """Prometheus metrics endpoint.

        Args:
            request: Incoming request.
            authenticated: Whether request is authenticated.

        Returns:
            Prometheus metrics response.
        """
        if not authenticated:
            return Response(
                content="Unauthorized",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Metrics"'},
            )

        output = await exporter.get_output()

        return Response(
            content=output,
            status_code=200,
            media_type="text/plain; charset=utf-8",
        )

    return router
