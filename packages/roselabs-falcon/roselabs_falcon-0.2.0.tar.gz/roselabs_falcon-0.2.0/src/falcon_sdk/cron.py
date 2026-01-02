"""
Cron job monitoring for Falcon SDK.

Monitor your scheduled jobs by sending heartbeats after each run.
Get alerted when jobs miss their expected schedule.

Example:
    >>> from falcon_sdk.cron import cron_heartbeat, cron_job
    >>>
    >>> # Simple heartbeat after job completion
    >>> cron_heartbeat("daily-backup")
    >>>
    >>> # Context manager for automatic timing
    >>> with cron_job("hourly-sync") as job:
    ...     sync_data()
    ...     job.set_metadata({"records_synced": 1500})
    >>>
    >>> # Decorator for automatic timing and error handling
    >>> @cron_job("nightly-cleanup")
    ... def cleanup_old_data():
    ...     # Your job logic here
    ...     pass
"""

from __future__ import annotations

import functools
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

import httpx

logger = logging.getLogger("falcon_sdk.cron")

# Type variable for decorator return type
F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class CronJobContext:
    """Context object for cron job execution."""

    slug: str
    started_at: float = field(default_factory=time.time)
    status: str = "ok"
    metadata: dict[str, Any] = field(default_factory=dict)
    environment: str | None = None
    _api_key: str | None = None
    _api_url: str = "https://api.falcon.roselabs.io"

    def set_metadata(self, data: dict[str, Any]) -> None:
        """Set metadata for this job run."""
        self.metadata.update(data)

    def set_environment(self, environment: str) -> None:
        """Set the environment for this job run."""
        self.environment = environment

    def mark_error(self) -> None:
        """Mark this job run as having an error."""
        self.status = "error"

    @property
    def duration_ms(self) -> int:
        """Get the duration of this job run in milliseconds."""
        return int((time.time() - self.started_at) * 1000)


class CronHeartbeatError(Exception):
    """Raised when a cron heartbeat fails to send."""

    pass


def _get_config() -> tuple[str | None, str]:
    """Get API key and URL from environment or SDK instance."""
    # Try to get from default SDK instance first
    try:
        from . import get_instance

        instance = get_instance()
        if instance:
            return instance.config.api_key, instance.config.api_url
    except Exception:
        pass

    # Fall back to environment variables
    api_key = os.environ.get("FALCON_API_KEY")
    api_url = os.environ.get("FALCON_API_URL", "https://api.falcon.roselabs.io")
    return api_key, api_url


def cron_heartbeat(
    slug: str,
    *,
    status: str = "ok",
    duration_ms: int | None = None,
    metadata: dict[str, Any] | None = None,
    environment: str | None = None,
    api_key: str | None = None,
    api_url: str | None = None,
) -> dict[str, Any]:
    """
    Send a heartbeat for a cron job monitor.

    Args:
        slug: The unique slug for the cron monitor (from Falcon dashboard)
        status: Status of the job run ("ok" or "error")
        duration_ms: Duration of the job in milliseconds (optional)
        metadata: Additional context/metadata from the job (optional)
        environment: Environment where the job ran (optional)
        api_key: Falcon API key (optional, uses env var or SDK instance)
        api_url: Falcon API URL (optional, uses env var or SDK instance)

    Returns:
        Response data from the heartbeat API

    Raises:
        CronHeartbeatError: If the heartbeat fails to send

    Example:
        >>> # Simple heartbeat
        >>> cron_heartbeat("daily-backup")
        >>>
        >>> # Heartbeat with details
        >>> cron_heartbeat(
        ...     "hourly-sync",
        ...     status="ok",
        ...     duration_ms=1234,
        ...     metadata={"records_synced": 500},
        ...     environment="production",
        ... )
    """
    # Get configuration
    key, url = _get_config()
    api_key = api_key or key
    api_url = api_url or url

    if not api_key:
        raise CronHeartbeatError(
            "No API key found. Set FALCON_API_KEY environment variable "
            "or initialize the Falcon SDK with falcon_sdk.init()"
        )

    payload: dict[str, Any] = {"status": status}
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
    if metadata:
        payload["metadata"] = metadata
    if environment:
        payload["environment"] = environment

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(
                f"{api_url}/v1/heartbeat/{slug}",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": api_key,
                },
            )

            if response.status_code == 404:
                raise CronHeartbeatError(
                    f"No cron monitor found with slug '{slug}'. "
                    "Create the monitor in your Falcon dashboard first."
                )

            if not response.is_success:
                raise CronHeartbeatError(
                    f"Heartbeat failed with status {response.status_code}: {response.text}"
                )

            return response.json()

    except httpx.RequestError as e:
        raise CronHeartbeatError(f"Failed to send heartbeat: {e}") from e


class cron_job:
    """
    Context manager and decorator for monitoring cron job execution.

    Automatically measures duration and sends heartbeat on completion.
    Reports errors if the job fails.

    As context manager:
        >>> with cron_job("hourly-sync") as job:
        ...     sync_data()
        ...     job.set_metadata({"records": 500})

    As decorator:
        >>> @cron_job("nightly-cleanup")
        ... def cleanup():
        ...     clean_old_records()
    """

    def __init__(
        self,
        slug: str,
        *,
        environment: str | None = None,
        api_key: str | None = None,
        api_url: str | None = None,
        reraise_errors: bool = True,
    ):
        """
        Initialize cron job monitor.

        Args:
            slug: The unique slug for the cron monitor
            environment: Environment where the job runs
            api_key: Falcon API key (optional)
            api_url: Falcon API URL (optional)
            reraise_errors: Whether to re-raise exceptions after reporting
        """
        self.slug = slug
        self.environment = environment
        self.api_key = api_key
        self.api_url = api_url
        self.reraise_errors = reraise_errors
        self._context: CronJobContext | None = None

    def __enter__(self) -> CronJobContext:
        """Enter the context manager."""
        self._context = CronJobContext(
            slug=self.slug,
            environment=self.environment,
        )
        return self._context

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> bool:
        """Exit the context manager and send heartbeat."""
        if self._context is None:
            return False

        # Mark as error if exception occurred
        if exc_type is not None:
            self._context.status = "error"
            # Add exception info to metadata
            if exc_val:
                self._context.metadata["error"] = str(exc_val)
                self._context.metadata["error_type"] = exc_type.__name__

        try:
            cron_heartbeat(
                self._context.slug,
                status=self._context.status,
                duration_ms=self._context.duration_ms,
                metadata=self._context.metadata if self._context.metadata else None,
                environment=self._context.environment,
                api_key=self.api_key,
                api_url=self.api_url,
            )
        except CronHeartbeatError as e:
            logger.warning(f"Failed to send cron heartbeat: {e}")

        # Return False to not suppress exceptions (unless reraise_errors is False)
        return not self.reraise_errors if exc_type else False

    def __call__(self, func: F) -> F:
        """Use as a decorator."""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self as job:
                result = func(*args, **kwargs)
                return result

        return wrapper  # type: ignore


# Async versions for asyncio support


async def cron_heartbeat_async(
    slug: str,
    *,
    status: str = "ok",
    duration_ms: int | None = None,
    metadata: dict[str, Any] | None = None,
    environment: str | None = None,
    api_key: str | None = None,
    api_url: str | None = None,
) -> dict[str, Any]:
    """
    Send a heartbeat for a cron job monitor (async version).

    See cron_heartbeat() for full documentation.
    """
    key, url = _get_config()
    api_key = api_key or key
    api_url = api_url or url

    if not api_key:
        raise CronHeartbeatError(
            "No API key found. Set FALCON_API_KEY environment variable "
            "or initialize the Falcon SDK with falcon_sdk.init()"
        )

    payload: dict[str, Any] = {"status": status}
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
    if metadata:
        payload["metadata"] = metadata
    if environment:
        payload["environment"] = environment

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{api_url}/v1/heartbeat/{slug}",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": api_key,
                },
            )

            if response.status_code == 404:
                raise CronHeartbeatError(
                    f"No cron monitor found with slug '{slug}'. "
                    "Create the monitor in your Falcon dashboard first."
                )

            if not response.is_success:
                raise CronHeartbeatError(
                    f"Heartbeat failed with status {response.status_code}: {response.text}"
                )

            return response.json()

    except httpx.RequestError as e:
        raise CronHeartbeatError(f"Failed to send heartbeat: {e}") from e
