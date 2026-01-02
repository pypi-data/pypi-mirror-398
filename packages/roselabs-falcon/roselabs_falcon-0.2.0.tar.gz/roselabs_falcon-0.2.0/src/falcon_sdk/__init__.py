"""
Falcon Error Tracking SDK for Python.

Simple, lightweight error tracking for your Python applications.

Example:
    >>> from falcon_sdk import Falcon
    >>>
    >>> falcon = Falcon(
    ...     api_key="fk_your_api_key",
    ...     app_name="my-app",
    ...     environment="production",
    ... )
    >>>
    >>> # Install automatic exception handler
    >>> falcon.install()
    >>>
    >>> # Manual capture
    >>> try:
    ...     risky_operation()
    ... except Exception as e:
    ...     falcon.capture_exception(e)
"""

from __future__ import annotations

from .client import Falcon, FalconConfig, FalconConfigError, RateLimiter
from .types import CaptureOptions, FalconEvent, UserContext
from .cron import cron_heartbeat, cron_heartbeat_async, cron_job, CronHeartbeatError
from .metrics import increment_counter, set_gauge, record_request, format_prometheus
from .fastapi import instrument_fastapi
from .breadcrumbs import (
    Breadcrumb,
    BreadcrumbType,
    add_breadcrumb as add_breadcrumb_internal,
    get_breadcrumbs,
    clear_breadcrumbs,
    install_breadcrumb_integrations,
)

__version__ = "0.1.0"
__all__ = [
    "Falcon",
    "FalconConfig",
    "FalconConfigError",
    "RateLimiter",
    "FalconEvent",
    "UserContext",
    "CaptureOptions",
    # Module-level functions
    "init",
    "capture_exception",
    "capture_message",
    "set_user",
    "get_instance",
    # Breadcrumbs
    "add_breadcrumb",
    "get_breadcrumbs",
    "clear_breadcrumbs",
    "install_breadcrumb_integrations",
    "Breadcrumb",
    "BreadcrumbType",
    # Cron monitoring
    "cron_heartbeat",
    "cron_heartbeat_async",
    "cron_job",
    "CronHeartbeatError",
    # Metrics
    "increment_counter",
    "set_gauge",
    "record_request",
    "format_prometheus",
    # FastAPI integration
    "instrument_fastapi",
]

# Framework integrations available as submodules:
#
# Flask:
#   from falcon_sdk.flask import init_app
#   init_app(app, falcon)  # or configure via app.config
#
# FastAPI:
#   from falcon_sdk.fastapi import FalconMiddleware, instrument_fastapi
#   instrument_fastapi(app, falcon)
#
# Django:
#   # settings.py
#   FALCON_API_KEY = "fk_xxx"
#   FALCON_APP_NAME = "my-app"
#   MIDDLEWARE = [..., "falcon_sdk.django.FalconMiddleware"]

# Module-level singleton
_default_instance: Falcon | None = None


def init(
    api_key: str,
    app_name: str,
    *,
    environment: str | None = None,
    release: str | None = None,
    api_url: str = "https://api.falcon.roselabs.io",
    enabled: bool = True,
    debug: bool = False,
    max_events_per_minute: int = 60,
    max_events_per_second: int = 10,
) -> Falcon:
    """
    Initialize the default Falcon instance.

    Args:
        api_key: Your Falcon API key (starts with fk_)
        app_name: Name of your application
        environment: Environment (e.g., 'production', 'staging')
        release: Application version/release
        api_url: Falcon API URL (defaults to https://api.falcon.roselabs.io)
        enabled: Enable/disable the SDK (defaults to True)
        debug: Enable debug logging (defaults to False)
        max_events_per_minute: Max events per minute, 0=unlimited (default: 60)
        max_events_per_second: Burst limit per second, 0=unlimited (default: 10)

    Returns:
        The initialized Falcon instance

    Raises:
        FalconConfigError: If configuration is invalid (fails fast on init)
    """
    global _default_instance
    _default_instance = Falcon(
        FalconConfig(
            api_key=api_key,
            app_name=app_name,
            environment=environment,
            release=release,
            api_url=api_url,
            enabled=enabled,
            debug=debug,
            max_events_per_minute=max_events_per_minute,
            max_events_per_second=max_events_per_second,
        )
    )
    return _default_instance


def get_instance() -> Falcon | None:
    """Get the default Falcon instance."""
    return _default_instance


def capture_exception(
    error: BaseException,
    *,
    context: dict | None = None,
    level: str = "error",
    tags: dict[str, str] | None = None,
) -> None:
    """
    Capture an exception using the default instance.

    Args:
        error: The exception to capture
        context: Additional context to attach
        level: Error level (debug, info, warning, error, fatal)
        tags: Tags for categorization
    """
    if _default_instance:
        _default_instance.capture_exception(
            error,
            context=context,
            level=level,
            tags=tags,
        )


def capture_message(
    message: str,
    *,
    level: str = "info",
    context: dict | None = None,
    tags: dict[str, str] | None = None,
) -> None:
    """
    Capture a message using the default instance.

    Args:
        message: The message to capture
        level: Message level (debug, info, warning, error, fatal)
        context: Additional context to attach
        tags: Tags for categorization
    """
    if _default_instance:
        _default_instance.capture_message(
            message,
            level=level,
            context=context,
            tags=tags,
        )


def set_user(
    user_id: str | None = None,
    email: str | None = None,
    name: str | None = None,
    **extra: str,
) -> None:
    """
    Set user context on the default instance.

    Args:
        user_id: User's unique identifier
        email: User's email address
        name: User's display name
        **extra: Additional user attributes
    """
    if _default_instance:
        if user_id is None and email is None and name is None and not extra:
            _default_instance.set_user(None)
        else:
            _default_instance.set_user(
                UserContext(
                    id=user_id,
                    email=email,
                    name=name,
                    **extra,
                )
            )


def add_breadcrumb(
    type: BreadcrumbType,
    message: str,
    *,
    category: str | None = None,
    data: dict | None = None,
) -> None:
    """
    Add a breadcrumb to the trail.

    Args:
        type: Type of breadcrumb (http, console, click, navigation, custom)
        message: Description of the event
        category: Subcategory (e.g., 'fetch', 'log', 'warn')
        data: Additional context data

    Example:
        >>> add_breadcrumb(
        ...     type="custom",
        ...     message="User clicked checkout",
        ...     category="ui.click",
        ...     data={"button_id": "checkout"},
        ... )
    """
    add_breadcrumb_internal(type, message, category=category, data=data)
