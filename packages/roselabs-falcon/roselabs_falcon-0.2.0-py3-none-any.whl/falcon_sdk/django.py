"""
Django middleware for Falcon error tracking.

Example:
    # settings.py
    FALCON_API_KEY = "fk_xxx"
    FALCON_APP_NAME = "my-django-app"

    MIDDLEWARE = [
        # ... other middleware
        "falcon_sdk.django.FalconMiddleware",
    ]

    # Or initialize manually:
    from falcon_sdk import init
    init(api_key="fk_xxx", app_name="my-app")
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from . import get_instance, init
from .client import Falcon

logger = logging.getLogger("falcon_sdk.django")


class FalconMiddleware:
    """
    Django middleware that captures unhandled exceptions.

    Add to MIDDLEWARE in settings.py:
        MIDDLEWARE = [
            # ... other middleware
            "falcon_sdk.django.FalconMiddleware",
        ]

    Configure via Django settings:
        FALCON_API_KEY = "fk_xxx"
        FALCON_APP_NAME = "my-app"
        FALCON_ENVIRONMENT = "production"  # optional
        FALCON_RELEASE = "1.0.0"  # optional
        FALCON_DEBUG = False  # optional
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self._falcon: Falcon | None = None
        self._initialized = False

    def _ensure_initialized(self) -> Falcon | None:
        """Lazily initialize Falcon from Django settings."""
        if self._initialized:
            return self._falcon

        self._initialized = True

        # Check if already initialized via init()
        instance = get_instance()
        if instance:
            self._falcon = instance
            return self._falcon

        # Try to initialize from Django settings
        try:
            from django.conf import settings

            api_key = getattr(settings, "FALCON_API_KEY", None)
            app_name = getattr(settings, "FALCON_APP_NAME", None)

            if not api_key or not app_name:
                logger.warning(
                    "Falcon SDK not configured. Set FALCON_API_KEY and FALCON_APP_NAME in settings."
                )
                return None

            self._falcon = init(
                api_key=api_key,
                app_name=app_name,
                environment=getattr(settings, "FALCON_ENVIRONMENT", None),
                release=getattr(settings, "FALCON_RELEASE", None),
                debug=getattr(settings, "FALCON_DEBUG", False),
            )
            logger.info("Falcon SDK initialized from Django settings")

        except Exception as e:
            logger.error(f"Failed to initialize Falcon SDK: {e}")

        return self._falcon

    def __call__(self, request):
        """Process the request."""
        start_time = time.time()

        # Store start time on request for later use
        request._falcon_start_time = start_time

        response = self.get_response(request)
        return response

    def process_exception(self, request, exception: Exception) -> None:
        """
        Called when a view raises an exception.

        This is called by Django's exception handling and allows us to
        capture the error before Django's error handlers process it.
        """
        falcon = self._ensure_initialized()
        if not falcon:
            return None

        # Build request context
        context = _build_request_context(request)

        # Add duration if we have start time
        if hasattr(request, "_falcon_start_time"):
            context["duration_ms"] = round(
                (time.time() - request._falcon_start_time) * 1000, 2
            )

        # Capture synchronously (Django is sync by default)
        falcon.capture_exception(exception, context=context, level="error")

        # Return None to let Django continue processing the exception
        return None


def _build_request_context(request) -> dict[str, Any]:
    """Build context dict from a Django HttpRequest."""
    context: dict[str, Any] = {
        "request": {
            "method": request.method,
            "path": request.path,
            "full_path": request.get_full_path(),
            "headers": _sanitize_headers(_get_headers(request)),
            "client_ip": _get_client_ip(request),
        }
    }

    # Add user info if authenticated
    if hasattr(request, "user") and request.user.is_authenticated:
        context["user"] = {
            "id": str(request.user.pk),
            "username": getattr(request.user, "username", None),
            "email": getattr(request.user, "email", None),
        }

    # Add URL parameters
    if hasattr(request, "resolver_match") and request.resolver_match:
        if request.resolver_match.kwargs:
            context["request"]["url_params"] = request.resolver_match.kwargs

    return context


def _get_headers(request) -> dict[str, str]:
    """Extract headers from Django request."""
    headers = {}
    for key, value in request.META.items():
        if key.startswith("HTTP_"):
            # Convert HTTP_CONTENT_TYPE to Content-Type
            header_name = key[5:].replace("_", "-").title()
            headers[header_name] = value
        elif key in ("CONTENT_TYPE", "CONTENT_LENGTH"):
            header_name = key.replace("_", "-").title()
            headers[header_name] = value
    return headers


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Remove sensitive headers before sending to Falcon."""
    sensitive = {
        "authorization",
        "cookie",
        "x-api-key",
        "x-auth-token",
        "x-access-token",
        "x-csrftoken",
    }
    return {
        k: "[REDACTED]" if k.lower() in sensitive else v for k, v in headers.items()
    }


def _get_client_ip(request) -> str | None:
    """Get client IP from request, handling proxies."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
