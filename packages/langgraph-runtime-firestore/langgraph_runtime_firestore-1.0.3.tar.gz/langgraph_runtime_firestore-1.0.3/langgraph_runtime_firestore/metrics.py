"""Metrics collection for Firestore runtime."""

from __future__ import annotations

import typing
from typing import Any

if typing.TYPE_CHECKING:
    pass


def get_metrics() -> dict[str, Any]:
    """Get current metrics for Firestore runtime.

    Returns:
        Dictionary containing runtime metrics
    """
    return {
        "firestore_operations": 0,
        "firestore_errors": 0,
        "firestore_latency_ms": 0,
        "workers": {"max": 0, "active": 0, "available": 0},
    }


async def collect_metrics() -> dict[str, Any]:
    """Collect metrics asynchronously.

    Returns:
        Dictionary containing collected metrics
    """
    return get_metrics()


__all__ = ["get_metrics", "collect_metrics"]
