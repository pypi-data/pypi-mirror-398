"""Breadcrumbs module for Falcon SDK.

Captures events (HTTP requests, console logs, etc.) leading up to an error
for better debugging context.
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

logger = logging.getLogger("falcon_sdk")

# =============================================================================
# Types
# =============================================================================

BreadcrumbType = Literal["http", "console", "click", "navigation", "custom"]


@dataclass
class Breadcrumb:
    """A breadcrumb event."""

    type: BreadcrumbType
    message: str
    category: str | None = None
    timestamp: str | None = None
    data: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API payload."""
        return {
            "type": self.type,
            "category": self.category,
            "message": self.message,
            "timestamp": self.timestamp,
            "data": self.data,
        }


# =============================================================================
# Breadcrumb Buffer
# =============================================================================

MAX_BREADCRUMBS = 50

# Thread-safe breadcrumb storage
_breadcrumbs: deque[Breadcrumb] = deque(maxlen=MAX_BREADCRUMBS)
_lock = threading.Lock()
_max_breadcrumbs = MAX_BREADCRUMBS


def configure_breadcrumbs(max_breadcrumbs: int = MAX_BREADCRUMBS) -> None:
    """Configure the breadcrumbs buffer size."""
    global _breadcrumbs, _max_breadcrumbs
    with _lock:
        _max_breadcrumbs = max_breadcrumbs
        # Create new deque with new maxlen, preserving existing items
        old_items = list(_breadcrumbs)[-max_breadcrumbs:]
        _breadcrumbs = deque(old_items, maxlen=max_breadcrumbs)


def add_breadcrumb(
    type: BreadcrumbType,
    message: str,
    *,
    category: str | None = None,
    data: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> None:
    """
    Add a breadcrumb to the buffer.

    Args:
        type: Type of breadcrumb (http, console, click, navigation, custom)
        message: Description of the event
        category: Subcategory (e.g., 'fetch', 'xhr', 'log', 'warn')
        data: Additional context data
        timestamp: ISO format timestamp (defaults to now)

    Example:
        >>> add_breadcrumb(
        ...     type="custom",
        ...     message="User clicked checkout button",
        ...     category="ui.click",
        ...     data={"button_id": "checkout-btn"},
        ... )
    """
    breadcrumb = Breadcrumb(
        type=type,
        message=message,
        category=category,
        data=data,
        timestamp=timestamp,
    )

    with _lock:
        _breadcrumbs.append(breadcrumb)


def get_breadcrumbs() -> list[Breadcrumb]:
    """Get all breadcrumbs."""
    with _lock:
        return list(_breadcrumbs)


def clear_breadcrumbs() -> None:
    """Clear all breadcrumbs."""
    with _lock:
        _breadcrumbs.clear()


# =============================================================================
# Logging Integration
# =============================================================================


class BreadcrumbLoggingHandler(logging.Handler):
    """Logging handler that captures log messages as breadcrumbs.

    Example:
        >>> handler = BreadcrumbLoggingHandler()
        >>> logging.getLogger().addHandler(handler)
    """

    LEVEL_MAP = {
        logging.DEBUG: "debug",
        logging.INFO: "info",
        logging.WARNING: "warn",
        logging.ERROR: "error",
        logging.CRITICAL: "error",
    }

    def emit(self, record: logging.LogRecord) -> None:
        # Skip Falcon SDK's own logs
        if record.name.startswith("falcon_sdk"):
            return

        category = self.LEVEL_MAP.get(record.levelno, "log")

        add_breadcrumb(
            type="console",
            category=category,
            message=record.getMessage(),
            data={
                "logger": record.name,
                "level": record.levelname,
                "pathname": record.pathname,
                "lineno": record.lineno,
            }
            if record.pathname
            else None,
        )


# =============================================================================
# HTTP Request Instrumentation (httpx/requests)
# =============================================================================

_httpx_instrumented = False
_requests_instrumented = False


def instrument_httpx() -> None:
    """Instrument httpx to capture HTTP requests as breadcrumbs."""
    global _httpx_instrumented
    if _httpx_instrumented:
        return

    try:
        import httpx

        original_send = httpx.Client.send
        original_async_send = httpx.AsyncClient.send

        def wrapped_send(self: httpx.Client, request: httpx.Request, **kwargs: Any) -> httpx.Response:
            import time

            start_time = time.time()
            try:
                response = original_send(self, request, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="httpx",
                    message=f"{request.method} {request.url}",
                    data={
                        "method": str(request.method),
                        "url": str(request.url),
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )
                return response
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="httpx",
                    message=f"{request.method} {request.url} (failed)",
                    data={
                        "method": str(request.method),
                        "url": str(request.url),
                        "error": str(e),
                        "duration_ms": duration_ms,
                    },
                )
                raise

        async def wrapped_async_send(
            self: httpx.AsyncClient, request: httpx.Request, **kwargs: Any
        ) -> httpx.Response:
            import time

            start_time = time.time()
            try:
                response = await original_async_send(self, request, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="httpx",
                    message=f"{request.method} {request.url}",
                    data={
                        "method": str(request.method),
                        "url": str(request.url),
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )
                return response
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="httpx",
                    message=f"{request.method} {request.url} (failed)",
                    data={
                        "method": str(request.method),
                        "url": str(request.url),
                        "error": str(e),
                        "duration_ms": duration_ms,
                    },
                )
                raise

        httpx.Client.send = wrapped_send  # type: ignore
        httpx.AsyncClient.send = wrapped_async_send  # type: ignore

        _httpx_instrumented = True
        logger.debug("httpx instrumented for breadcrumbs")

    except ImportError:
        pass  # httpx not installed


def instrument_requests() -> None:
    """Instrument requests library to capture HTTP requests as breadcrumbs."""
    global _requests_instrumented
    if _requests_instrumented:
        return

    try:
        import requests

        original_request = requests.Session.request

        def wrapped_request(
            self: requests.Session, method: str, url: str, **kwargs: Any
        ) -> requests.Response:
            import time

            start_time = time.time()
            try:
                response = original_request(self, method, url, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="requests",
                    message=f"{method.upper()} {url}",
                    data={
                        "method": method.upper(),
                        "url": url,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )
                return response
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="requests",
                    message=f"{method.upper()} {url} (failed)",
                    data={
                        "method": method.upper(),
                        "url": url,
                        "error": str(e),
                        "duration_ms": duration_ms,
                    },
                )
                raise

        requests.Session.request = wrapped_request  # type: ignore

        _requests_instrumented = True
        logger.debug("requests instrumented for breadcrumbs")

    except ImportError:
        pass  # requests not installed


def install_breadcrumb_integrations(
    *,
    http: bool = True,
    logging_handler: bool = True,
    logging_level: int = logging.INFO,
) -> None:
    """
    Install automatic breadcrumb capture integrations.

    Args:
        http: Instrument HTTP libraries (httpx, requests)
        logging_handler: Add a handler to the root logger
        logging_level: Minimum log level to capture
    """
    if http:
        instrument_httpx()
        instrument_requests()

    if logging_handler:
        handler = BreadcrumbLoggingHandler()
        handler.setLevel(logging_level)
        logging.getLogger().addHandler(handler)
        logger.debug(f"Installed breadcrumb logging handler (level={logging_level})")
