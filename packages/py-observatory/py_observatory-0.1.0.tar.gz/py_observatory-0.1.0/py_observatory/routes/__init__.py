"""Routes for py-observatory."""

from .metrics import create_metrics_router

__all__ = [
    "create_metrics_router",
]
