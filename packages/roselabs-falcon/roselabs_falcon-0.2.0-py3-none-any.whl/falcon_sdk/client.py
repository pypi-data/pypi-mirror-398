"""Falcon SDK client with both sync and async support."""

from __future__ import annotations

import atexit
import logging
import sys
import time
import traceback
from collections import deque
from dataclasses import dataclass, field
from threading import Lock, Thread
from typing import Any, Callable

import httpx

from .breadcrumbs import (
    Breadcrumb,
    BreadcrumbType,
    add_breadcrumb as add_breadcrumb_internal,
    get_breadcrumbs,
    clear_breadcrumbs,
    install_breadcrumb_integrations,
)
from .types import CaptureOptions, ErrorLevel, FalconEvent, UserContext

logger = logging.getLogger("falcon_sdk")


class FalconConfigError(Exception):
    """Raised when Falcon SDK configuration is invalid."""

    pass


@dataclass
class FalconConfig:
    """Configuration for Falcon SDK."""

    api_key: str
    app_name: str
    environment: str | None = None
    release: str | None = None
    api_url: str = "https://api.falcon.roselabs.io"
    enabled: bool = True
    debug: bool = False
    before_send: Callable[[FalconEvent], FalconEvent | None] | None = None
    # Rate limiting - prevent error storms from overwhelming the server
    max_events_per_minute: int = 60  # Max events per minute (0 = unlimited)
    max_events_per_second: int = 10  # Burst limit per second (0 = unlimited)

    def validate(self) -> None:
        """
        Validate configuration. Raises FalconConfigError if invalid.
        Call this immediately on SDK initialization to fail fast.
        """
        errors: list[str] = []

        # Validate api_key
        if not self.api_key:
            errors.append("api_key is required")
        elif not isinstance(self.api_key, str):
            errors.append("api_key must be a string")
        elif not self.api_key.startswith("sk_"):
            errors.append("api_key must start with 'sk_' (e.g., 'sk_falcon_...')")
        elif len(self.api_key) < 10:
            errors.append("api_key appears too short - check your API key")

        # Validate app_name
        if not self.app_name:
            errors.append("app_name is required")
        elif not isinstance(self.app_name, str):
            errors.append("app_name must be a string")
        elif len(self.app_name) > 100:
            errors.append("app_name must be 100 characters or less")

        # Validate api_url
        if self.api_url:
            if not self.api_url.startswith(("http://", "https://")):
                errors.append("api_url must start with http:// or https://")

        # Validate environment
        if self.environment is not None:
            if not isinstance(self.environment, str):
                errors.append("environment must be a string")
            elif len(self.environment) > 50:
                errors.append("environment must be 50 characters or less")

        # Validate release
        if self.release is not None:
            if not isinstance(self.release, str):
                errors.append("release must be a string")
            elif len(self.release) > 100:
                errors.append("release must be 100 characters or less")

        if errors:
            raise FalconConfigError(
                f"Invalid Falcon configuration:\n  - " + "\n  - ".join(errors)
            )


class RateLimiter:
    """
    Simple sliding window rate limiter.
    Thread-safe for concurrent access.
    """

    def __init__(self, max_per_second: int = 10, max_per_minute: int = 60):
        self.max_per_second = max_per_second
        self.max_per_minute = max_per_minute
        self._second_window: deque[float] = deque()
        self._minute_window: deque[float] = deque()
        self._lock = Lock()
        self._dropped_count = 0

    def allow(self) -> bool:
        """Check if an event is allowed under rate limits."""
        now = time.time()

        with self._lock:
            # Clean old entries from windows
            second_cutoff = now - 1.0
            minute_cutoff = now - 60.0

            while self._second_window and self._second_window[0] < second_cutoff:
                self._second_window.popleft()
            while self._minute_window and self._minute_window[0] < minute_cutoff:
                self._minute_window.popleft()

            # Check limits (0 = unlimited)
            if self.max_per_second > 0 and len(self._second_window) >= self.max_per_second:
                self._dropped_count += 1
                return False
            if self.max_per_minute > 0 and len(self._minute_window) >= self.max_per_minute:
                self._dropped_count += 1
                return False

            # Allow and record
            self._second_window.append(now)
            self._minute_window.append(now)
            return True

    @property
    def dropped_count(self) -> int:
        """Number of events dropped due to rate limiting."""
        return self._dropped_count


class Falcon:
    """
    Falcon error tracking client.

    Supports both synchronous and asynchronous error reporting.

    Example:
        >>> falcon = Falcon(FalconConfig(
        ...     api_key="fk_xxx",
        ...     app_name="my-app",
        ...     environment="production",
        ... ))
        >>>
        >>> # Install automatic exception handler
        >>> falcon.install()
        >>>
        >>> # Sync capture
        >>> falcon.capture_exception(error)
        >>>
        >>> # Async capture
        >>> await falcon.capture_exception_async(error)
    """

    def __init__(self, config: FalconConfig):
        # Validate configuration IMMEDIATELY - fail fast before any errors happen
        config.validate()

        self.config = config
        self._user: UserContext | None = None
        self._context: dict[str, Any] = {}
        self._installed = False
        self._original_excepthook: Callable | None = None

        # Initialize rate limiter
        self._rate_limiter = RateLimiter(
            max_per_second=config.max_events_per_second,
            max_per_minute=config.max_events_per_minute,
        )

        if config.debug:
            logging.basicConfig(level=logging.DEBUG)
            logger.setLevel(logging.DEBUG)

        self._log("Falcon SDK initialized", {"app_name": config.app_name})

    # =========================================================================
    # Installation
    # =========================================================================

    def install(self) -> None:
        """
        Install global exception handler for automatic error capture.
        Call this once at application startup.
        """
        if self._installed or not self.config.enabled:
            return

        # Store original excepthook
        self._original_excepthook = sys.excepthook

        # Install our exception handler
        sys.excepthook = self._excepthook

        # Register cleanup on exit
        atexit.register(self.uninstall)

        self._installed = True
        self._log("Installed global exception handler")

    def uninstall(self) -> None:
        """Uninstall global exception handler."""
        if not self._installed:
            return

        if self._original_excepthook:
            sys.excepthook = self._original_excepthook
            self._original_excepthook = None

        self._installed = False
        self._log("Uninstalled global exception handler")

    def _excepthook(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: Any,
    ) -> None:
        """Custom exception hook for uncaught exceptions."""
        # Capture the exception
        self.capture_exception(exc_value, level="fatal")

        # Call the original excepthook
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_tb)

    # =========================================================================
    # Synchronous API
    # =========================================================================

    def capture_exception(
        self,
        error: BaseException,
        *,
        context: dict[str, Any] | None = None,
        level: ErrorLevel = "error",
        tags: dict[str, str] | None = None,
    ) -> None:
        """
        Capture an exception synchronously.

        Args:
            error: The exception to capture
            context: Additional context to attach
            level: Error level (debug, info, warning, error, fatal)
            tags: Tags for categorization
        """
        if not self.config.enabled:
            return

        event = self._build_event(error, context, level, tags)
        self._send_event_sync(event)

    def capture_message(
        self,
        message: str,
        *,
        level: ErrorLevel = "info",
        context: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        """
        Capture a message synchronously.

        Args:
            message: The message to capture
            level: Message level (debug, info, warning, error, fatal)
            context: Additional context to attach
            tags: Tags for categorization
        """
        if not self.config.enabled:
            return

        event = FalconEvent(
            message=message,
            level=level,
            context=self._merge_context(context, tags),
            environment=self.config.environment,
            release=self.config.release,
            user_id=self._user.id if self._user else None,
        )
        self._send_event_sync(event)

    def capture_exception_background(
        self,
        error: BaseException,
        *,
        context: dict[str, Any] | None = None,
        level: ErrorLevel = "error",
        tags: dict[str, str] | None = None,
    ) -> None:
        """
        Capture an exception in a background thread (non-blocking).

        Args:
            error: The exception to capture
            context: Additional context to attach
            level: Error level (debug, info, warning, error, fatal)
            tags: Tags for categorization
        """
        if not self.config.enabled:
            return

        event = self._build_event(error, context, level, tags)
        thread = Thread(target=self._send_event_sync, args=(event,), daemon=True)
        thread.start()

    # =========================================================================
    # Asynchronous API
    # =========================================================================

    async def capture_exception_async(
        self,
        error: BaseException,
        *,
        context: dict[str, Any] | None = None,
        level: ErrorLevel = "error",
        tags: dict[str, str] | None = None,
    ) -> None:
        """
        Capture an exception asynchronously.

        Args:
            error: The exception to capture
            context: Additional context to attach
            level: Error level (debug, info, warning, error, fatal)
            tags: Tags for categorization
        """
        if not self.config.enabled:
            return

        event = self._build_event(error, context, level, tags)
        await self._send_event_async(event)

    async def capture_message_async(
        self,
        message: str,
        *,
        level: ErrorLevel = "info",
        context: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        """
        Capture a message asynchronously.

        Args:
            message: The message to capture
            level: Message level (debug, info, warning, error, fatal)
            context: Additional context to attach
            tags: Tags for categorization
        """
        if not self.config.enabled:
            return

        event = FalconEvent(
            message=message,
            level=level,
            context=self._merge_context(context, tags),
            environment=self.config.environment,
            release=self.config.release,
            user_id=self._user.id if self._user else None,
        )
        await self._send_event_async(event)

    # =========================================================================
    # Context Management
    # =========================================================================

    def set_user(self, user: UserContext | None) -> None:
        """
        Set user context for all future events.

        Args:
            user: User context, or None to clear
        """
        self._user = user
        self._log("User context updated", user.to_dict() if user else None)

    def set_context(self, key: str, value: Any) -> None:
        """
        Set global context that will be attached to all events.

        Args:
            key: Context key
            value: Context value
        """
        self._context[key] = value

    def clear_context(self) -> None:
        """Clear all global context and user."""
        self._context = {}
        self._user = None

    def add_breadcrumb(
        self,
        type: BreadcrumbType,
        message: str,
        *,
        category: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a breadcrumb to the trail.

        Args:
            type: Type of breadcrumb (http, console, click, navigation, custom)
            message: Description of the event
            category: Subcategory (e.g., 'fetch', 'log', 'warn')
            data: Additional context data

        Example:
            >>> falcon.add_breadcrumb(
            ...     type="custom",
            ...     message="User clicked checkout",
            ...     category="ui.click",
            ...     data={"button_id": "checkout"},
            ... )
        """
        add_breadcrumb_internal(type, message, category=category, data=data)

    # =========================================================================
    # Decorators
    # =========================================================================

    def capture_errors(self, func: Callable) -> Callable:
        """
        Decorator to automatically capture exceptions from a function.

        Example:
            >>> @falcon.capture_errors
            ... def risky_function():
            ...     raise ValueError("Something went wrong")
        """
        import asyncio
        import functools

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.capture_exception(e)
                raise

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                await self.capture_exception_async(e)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    # =========================================================================
    # Logging Handler
    # =========================================================================

    def get_logging_handler(self, level: int = logging.ERROR) -> logging.Handler:
        """
        Get a logging handler that sends errors to Falcon.

        Args:
            level: Minimum log level to capture (default: ERROR)

        Returns:
            A logging.Handler instance

        Example:
            >>> logging.getLogger().addHandler(falcon.get_logging_handler())
        """
        return FalconLoggingHandler(self, level)

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _build_event(
        self,
        error: BaseException,
        context: dict[str, Any] | None,
        level: ErrorLevel,
        tags: dict[str, str] | None,
    ) -> FalconEvent:
        """Build an event from an exception."""
        # Get breadcrumbs
        breadcrumbs = get_breadcrumbs()
        breadcrumbs_data = [b.to_dict() for b in breadcrumbs] if breadcrumbs else None

        return FalconEvent(
            message=str(error) or type(error).__name__,
            level=level,
            stack=traceback.format_exc(),
            context=self._merge_context(context, tags),
            environment=self.config.environment,
            release=self.config.release,
            user_id=self._user.id if self._user else None,
            breadcrumbs=breadcrumbs_data,
        )

    def _merge_context(
        self,
        context: dict[str, Any] | None,
        tags: dict[str, str] | None,
    ) -> dict[str, Any]:
        """Merge global and local context."""
        result = dict(self._context)
        if context:
            result.update(context)
        if tags:
            result["tags"] = tags
        return result

    def _send_event_sync(self, event: FalconEvent) -> None:
        """Send event synchronously."""
        # Check rate limit first
        if not self._rate_limiter.allow():
            self._log(
                f"Event dropped due to rate limit (dropped {self._rate_limiter.dropped_count} total)"
            )
            return

        # Apply before_send hook
        if self.config.before_send:
            result = self.config.before_send(event)
            if result is None:
                self._log("Event dropped by before_send hook")
                return
            event = result

        payload = {
            "app_name": self.config.app_name,
            **event.to_dict(),
        }

        self._log("Sending event", payload)

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    f"{self.config.api_url}/v1/error",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": self.config.api_key,
                    },
                )
                if not response.is_success:
                    self._log(f"Failed to send event: {response.status_code}")
                else:
                    self._log("Event sent successfully")
        except Exception as e:
            self._log(f"Failed to send event: {e}")

    async def _send_event_async(self, event: FalconEvent) -> None:
        """Send event asynchronously."""
        # Check rate limit first
        if not self._rate_limiter.allow():
            self._log(
                f"Event dropped due to rate limit (dropped {self._rate_limiter.dropped_count} total)"
            )
            return

        # Apply before_send hook
        if self.config.before_send:
            result = self.config.before_send(event)
            if result is None:
                self._log("Event dropped by before_send hook")
                return
            event = result

        payload = {
            "app_name": self.config.app_name,
            **event.to_dict(),
        }

        self._log("Sending event", payload)

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.config.api_url}/v1/error",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": self.config.api_key,
                    },
                )
                if not response.is_success:
                    self._log(f"Failed to send event: {response.status_code}")
                else:
                    self._log("Event sent successfully")
        except Exception as e:
            self._log(f"Failed to send event: {e}")

    def _log(self, message: str, data: Any = None) -> None:
        """Log debug message."""
        if self.config.debug:
            if data:
                logger.debug(f"[Falcon] {message}: {data}")
            else:
                logger.debug(f"[Falcon] {message}")


class FalconLoggingHandler(logging.Handler):
    """
    A logging handler that sends errors to Falcon.

    Example:
        >>> import logging
        >>> from falcon_sdk import Falcon, FalconConfig
        >>>
        >>> falcon = Falcon(FalconConfig(api_key="fk_xxx", app_name="my-app"))
        >>> logging.getLogger().addHandler(falcon.get_logging_handler())
        >>>
        >>> # Now logging.error() will also report to Falcon
        >>> logging.error("Something went wrong!")
    """

    def __init__(self, falcon: Falcon, level: int = logging.ERROR):
        super().__init__(level)
        self.falcon = falcon

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to Falcon."""
        try:
            # Map logging levels to Falcon levels
            level_map: dict[int, ErrorLevel] = {
                logging.DEBUG: "debug",
                logging.INFO: "info",
                logging.WARNING: "warning",
                logging.ERROR: "error",
                logging.CRITICAL: "fatal",
            }
            level = level_map.get(record.levelno, "error")

            # Build context from record
            context: dict[str, Any] = {
                "logger": record.name,
                "filename": record.filename,
                "lineno": record.lineno,
                "funcName": record.funcName,
            }

            # If there's exception info, capture it
            if record.exc_info and record.exc_info[1]:
                self.falcon.capture_exception_background(
                    record.exc_info[1],
                    context=context,
                    level=level,
                )
            else:
                # Just capture the message (in background to avoid blocking)
                event = FalconEvent(
                    message=record.getMessage(),
                    level=level,
                    stack=self.format(record) if record.exc_info else None,
                    context=context,
                    environment=self.falcon.config.environment,
                    release=self.falcon.config.release,
                    user_id=self.falcon._user.id if self.falcon._user else None,
                )
                thread = Thread(
                    target=self.falcon._send_event_sync,
                    args=(event,),
                    daemon=True,
                )
                thread.start()

        except Exception:
            self.handleError(record)
