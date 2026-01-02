"""
FastAPI middleware for Falcon error tracking.

Example:
    >>> from fastapi import FastAPI
    >>> from falcon_sdk import init
    >>> from falcon_sdk.fastapi import instrument_fastapi
    >>>
    >>> falcon = init(api_key="sk_falcon_xxx", app_name="my-app")
    >>> app = FastAPI()
    >>>
    >>> # Full instrumentation with auto health/metrics
    >>> instrument_fastapi(app, falcon, auto_uptime=True, auto_metrics=True)
"""

from __future__ import annotations

import time
from typing import Any, Callable, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse, JSONResponse
from starlette.types import ASGIApp

from .client import Falcon
from .health import create_health_response, DEFAULT_HEALTH_PATH
from .metrics import format_prometheus, record_request, DEFAULT_METRICS_PATH


class FalconMiddleware(BaseHTTPMiddleware):
    """
    FastAPI/Starlette middleware that captures unhandled exceptions.

    Usage:
        app.add_middleware(FalconMiddleware, falcon=falcon_instance)
    """

    def __init__(
        self,
        app: ASGIApp,
        falcon: Falcon,
        collect_metrics: bool = False,
    ) -> None:
        super().__init__(app)
        self.falcon = falcon
        self.collect_metrics = collect_metrics

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        try:
            response = await call_next(request)

            # Record request metrics if enabled
            if self.collect_metrics:
                duration_ms = (time.time() - start_time) * 1000
                record_request(request.method, response.status_code, duration_ms)

            return response
        except Exception as exc:
            # Record failed request
            if self.collect_metrics:
                duration_ms = (time.time() - start_time) * 1000
                record_request(request.method, 500, duration_ms)

            # Capture the exception with request context
            await self.falcon.capture_exception_async(
                exc,
                context=_build_request_context(request, start_time),
                level="error",
            )
            # Re-raise so FastAPI's exception handlers can process it
            raise


def instrument_fastapi(
    app: ASGIApp,
    falcon: Falcon,
    *,
    auto_uptime: bool = False,
    auto_metrics: bool = False,
    health_path: str = DEFAULT_HEALTH_PATH,
    metrics_path: str = DEFAULT_METRICS_PATH,
    health_check: Callable[[], bool | Awaitable[bool]] | None = None,
    version: str | None = None,
) -> None:
    """
    Instrument a FastAPI app with Falcon error tracking and optional health/metrics.

    Args:
        app: The FastAPI application instance
        falcon: The Falcon SDK instance
        auto_uptime: Auto-register health check endpoint (default: False)
        auto_metrics: Auto-register metrics endpoint (default: False)
        health_path: Custom health check path (default: /__falcon/health)
        metrics_path: Custom metrics path (default: /__falcon/metrics)
        health_check: Custom health check function (sync or async)
        version: Application version to report in health check

    Example:
        >>> from fastapi import FastAPI
        >>> from falcon_sdk import init
        >>> from falcon_sdk.fastapi import instrument_fastapi
        >>>
        >>> app = FastAPI()
        >>> falcon = init(api_key="sk_falcon_xxx", app_name="my-app")
        >>> instrument_fastapi(app, falcon, auto_uptime=True, auto_metrics=True)
    """
    # Get app name from Falcon config
    app_name = falcon.config.app_name if hasattr(falcon, "config") else None

    # Add health endpoint if enabled
    if auto_uptime:
        async def health_endpoint(request: Request) -> JSONResponse:
            response, status_code = await create_health_response(
                app_name=app_name,
                version=version,
                check=health_check,
            )
            return JSONResponse(content=response.to_dict(), status_code=status_code)

        # Add route to the app
        from starlette.routing import Route
        app.routes.insert(0, Route(health_path, health_endpoint, methods=["GET"]))  # type: ignore

    # Add metrics endpoint if enabled
    if auto_metrics:
        async def metrics_endpoint(request: Request) -> PlainTextResponse:
            output = format_prometheus()
            return PlainTextResponse(
                content=output,
                media_type="text/plain; version=0.0.4; charset=utf-8",
            )

        from starlette.routing import Route
        app.routes.insert(0, Route(metrics_path, metrics_endpoint, methods=["GET"]))  # type: ignore

    # Add error tracking middleware (with metrics collection if enabled)
    app.add_middleware(FalconMiddleware, falcon=falcon, collect_metrics=auto_metrics)  # type: ignore


def create_exception_handler(falcon: Falcon):
    """
    Create a FastAPI exception handler that reports to Falcon.

    Use this if you want to handle specific exception types while still
    reporting them to Falcon.

    Example:
        >>> from fastapi import FastAPI, HTTPException
        >>> from falcon_sdk import init
        >>> from falcon_sdk.fastapi import create_exception_handler
        >>>
        >>> app = FastAPI()
        >>> falcon = init(api_key="sk_falcon_xxx", app_name="my-app")
        >>>
        >>> @app.exception_handler(Exception)
        >>> async def handle_exception(request, exc):
        ...     handler = create_exception_handler(falcon)
        ...     return await handler(request, exc)
    """

    async def exception_handler(request: Request, exc: Exception) -> Response:
        # Capture to Falcon
        await falcon.capture_exception_async(
            exc,
            context=_build_request_context(request),
            level="error",
        )

        # Return a generic error response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return exception_handler


def _build_request_context(
    request: Request, start_time: float | None = None
) -> dict[str, Any]:
    """Build context dict from a Starlette/FastAPI request."""
    context: dict[str, Any] = {
        "request": {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_string": request.url.query,
            "headers": _sanitize_headers(dict(request.headers)),
            "client": request.client.host if request.client else None,
        }
    }

    if start_time:
        context["duration_ms"] = round((time.time() - start_time) * 1000, 2)

    # Add path parameters if available
    if hasattr(request, "path_params") and request.path_params:
        context["request"]["path_params"] = dict(request.path_params)

    return context


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Remove sensitive headers before sending to Falcon."""
    sensitive = {
        "authorization",
        "cookie",
        "x-api-key",
        "x-auth-token",
        "x-access-token",
    }
    return {
        k: "[REDACTED]" if k.lower() in sensitive else v for k, v in headers.items()
    }
