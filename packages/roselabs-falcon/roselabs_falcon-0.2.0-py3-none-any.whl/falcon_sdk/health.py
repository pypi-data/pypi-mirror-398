"""
Health check endpoint for Falcon SDK.

Provides a standardized health check endpoint that Falcon can ping
to monitor uptime.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

# Track process start time
_start_time = time.time()

DEFAULT_HEALTH_PATH = "/__falcon/health"


@dataclass
class HealthCheckResponse:
    """Health check response structure."""

    status: str  # "ok" or "unhealthy"
    timestamp: str
    uptime_seconds: int
    app_name: str | None = None
    version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result: dict[str, Any] = {
            "status": self.status,
            "timestamp": self.timestamp,
            "uptime_seconds": self.uptime_seconds,
        }
        if self.app_name:
            result["app_name"] = self.app_name
        if self.version:
            result["version"] = self.version
        return result


async def create_health_response(
    app_name: str | None = None,
    version: str | None = None,
    check: Callable[[], bool | Awaitable[bool]] | None = None,
) -> tuple[HealthCheckResponse, int]:
    """
    Create a health check response.

    Args:
        app_name: Application name to include in response
        version: Application version to include
        check: Custom health check function (sync or async)

    Returns:
        Tuple of (response, status_code)
    """
    is_healthy = True

    if check:
        try:
            result = check()
            # Handle async check
            if hasattr(result, "__await__"):
                is_healthy = await result
            else:
                is_healthy = bool(result)
        except Exception:
            is_healthy = False

    response = HealthCheckResponse(
        status="ok" if is_healthy else "unhealthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=int(time.time() - _start_time),
        app_name=app_name,
        version=version,
    )

    status_code = 200 if is_healthy else 503
    return response, status_code
