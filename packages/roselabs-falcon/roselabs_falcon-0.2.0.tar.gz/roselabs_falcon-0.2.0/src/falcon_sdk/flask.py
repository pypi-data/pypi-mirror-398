"""
Flask integration for Falcon error tracking.

Provides automatic error tracking, request context capture, and blueprint support.

Example:
    >>> from flask import Flask
    >>> from falcon_sdk import init
    >>> from falcon_sdk.flask import init_app
    >>>
    >>> app = Flask(__name__)
    >>> falcon = init(api_key="fk_xxx", app_name="my-app")
    >>> init_app(app, falcon)

With configuration from app.config:
    >>> app.config["FALCON_API_KEY"] = "fk_xxx"
    >>> app.config["FALCON_APP_NAME"] = "my-app"
    >>> init_app(app)
"""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask, Blueprint
    from werkzeug.exceptions import HTTPException

from .client import Falcon, FalconConfig


# Store falcon instance on app for access in request handlers
_FALCON_ATTR = "_falcon_sdk"


def init_app(app: "Flask", falcon: Falcon | None = None) -> Falcon:
    """
    Initialize Falcon for a Flask application.

    Registers error handlers and stores the Falcon instance on the app.
    Can be called with an existing Falcon instance or configured from app.config.

    Args:
        app: The Flask application instance
        falcon: Optional Falcon instance. If not provided, will be created from
                app.config using FALCON_API_KEY, FALCON_APP_NAME, etc.

    Returns:
        The Falcon instance attached to the app

    Config keys (when falcon is None):
        FALCON_API_KEY: Your Falcon API key (required)
        FALCON_APP_NAME: Application name (required)
        FALCON_ENVIRONMENT: Environment (defaults to Flask config or 'production')
        FALCON_RELEASE: Application version/release
        FALCON_API_URL: Falcon API URL (defaults to https://api.falcon.roselabs.io)
        FALCON_ENABLED: Enable/disable SDK (default: True)
        FALCON_DEBUG: Enable debug logging (default: False)

    Example:
        >>> from flask import Flask
        >>> from falcon_sdk import init
        >>> from falcon_sdk.flask import init_app
        >>>
        >>> app = Flask(__name__)
        >>> falcon = init(api_key="fk_xxx", app_name="my-app")
        >>> init_app(app, falcon)

    Example with app.config:
        >>> app = Flask(__name__)
        >>> app.config["FALCON_API_KEY"] = "fk_xxx"
        >>> app.config["FALCON_APP_NAME"] = "my-flask-app"
        >>> init_app(app)
    """
    if falcon is None:
        # Create from app config
        api_key = app.config.get("FALCON_API_KEY")
        app_name = app.config.get("FALCON_APP_NAME")

        if not api_key or not app_name:
            raise ValueError(
                "FALCON_API_KEY and FALCON_APP_NAME are required in app.config "
                "when falcon instance is not provided"
            )

        # Determine environment
        environment = app.config.get("FALCON_ENVIRONMENT")
        if environment is None:
            if app.debug:
                environment = "development"
            elif app.testing:
                environment = "testing"
            else:
                environment = "production"

        falcon = Falcon(
            FalconConfig(
                api_key=api_key,
                app_name=app_name,
                environment=environment,
                release=app.config.get("FALCON_RELEASE"),
                api_url=app.config.get(
                    "FALCON_API_URL", "https://api.falcon.roselabs.io"
                ),
                enabled=app.config.get("FALCON_ENABLED", True),
                debug=app.config.get("FALCON_DEBUG", False),
            )
        )

    # Store on app for later access
    setattr(app, _FALCON_ATTR, falcon)

    # Register error handlers
    _register_error_handlers(app, falcon)

    # Register request hooks for timing
    _register_request_hooks(app)

    return falcon


def get_falcon(app: "Flask") -> Falcon | None:
    """
    Get the Falcon instance attached to a Flask app.

    Args:
        app: The Flask application instance

    Returns:
        The Falcon instance or None if not initialized
    """
    return getattr(app, _FALCON_ATTR, None)


def init_blueprint(blueprint: "Blueprint", falcon: Falcon) -> None:
    """
    Initialize Falcon error handling for a Flask Blueprint.

    Registers blueprint-specific error handlers that report to Falcon.

    Args:
        blueprint: The Flask Blueprint instance
        falcon: The Falcon SDK instance

    Example:
        >>> from flask import Blueprint
        >>> from falcon_sdk import init
        >>> from falcon_sdk.flask import init_blueprint
        >>>
        >>> api_bp = Blueprint("api", __name__, url_prefix="/api")
        >>> falcon = init(api_key="fk_xxx", app_name="my-app")
        >>> init_blueprint(api_bp, falcon)
    """
    _register_error_handlers(blueprint, falcon)


def capture_route_errors(falcon: Falcon):
    """
    Decorator to wrap a route function with Falcon error capture.

    Use this for fine-grained control over error handling on specific routes.

    Args:
        falcon: The Falcon SDK instance

    Returns:
        A decorator function

    Example:
        >>> from flask import Flask
        >>> from falcon_sdk import init
        >>> from falcon_sdk.flask import capture_route_errors
        >>>
        >>> falcon = init(api_key="fk_xxx", app_name="my-app")
        >>>
        >>> @app.route("/api/risky")
        >>> @capture_route_errors(falcon)
        >>> def risky_endpoint():
        ...     # Errors here will be captured to Falcon
        ...     return {"result": do_risky_thing()}
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            try:
                return f(*args, **kwargs)
            except Exception as exc:
                from flask import request

                falcon.capture_exception(
                    exc,
                    context=_build_request_context(request),
                    level="error",
                )
                raise

        return wrapped

    return decorator


def _register_error_handlers(
    app_or_blueprint: "Flask | Blueprint", falcon: Falcon
) -> None:
    """Register error handlers on an app or blueprint."""

    @app_or_blueprint.errorhandler(Exception)
    def handle_exception(exc: Exception) -> tuple[dict, int]:
        """Global exception handler that reports to Falcon."""
        from flask import request, jsonify

        # Capture to Falcon
        falcon.capture_exception(
            exc,
            context=_build_request_context(request),
            level="error",
        )

        # Return error response
        return jsonify({"error": "Internal server error"}), 500

    @app_or_blueprint.errorhandler(500)
    def handle_500(exc: Exception) -> tuple[dict, int]:
        """Handle 500 errors."""
        from flask import request, jsonify

        # Get original exception if wrapped
        original = getattr(exc, "original_exception", exc)

        falcon.capture_exception(
            original,
            context=_build_request_context(request),
            level="error",
        )

        return jsonify({"error": "Internal server error"}), 500


def _register_request_hooks(app: "Flask") -> None:
    """Register request lifecycle hooks for timing and context."""

    @app.before_request
    def start_request_timer() -> None:
        """Store request start time for duration calculation."""
        from flask import g

        g._falcon_start_time = time.time()

    @app.after_request
    def log_request(response):
        """Optionally log request metrics."""
        # Currently just returns response as-is
        # Could add request logging here in the future
        return response


def _build_request_context(request: Any) -> dict[str, Any]:
    """Build context dict from a Flask request object."""
    from flask import g

    context: dict[str, Any] = {
        "request": {
            "method": request.method,
            "url": request.url,
            "path": request.path,
            "query_string": request.query_string.decode("utf-8", errors="replace"),
            "headers": _sanitize_headers(dict(request.headers)),
            "remote_addr": request.remote_addr,
            "endpoint": request.endpoint,
        }
    }

    # Add request duration if available
    start_time = getattr(g, "_falcon_start_time", None)
    if start_time:
        context["duration_ms"] = round((time.time() - start_time) * 1000, 2)

    # Add view args (route parameters) if available
    if request.view_args:
        context["request"]["view_args"] = dict(request.view_args)

    # Add form data keys (not values for security)
    if request.form:
        context["request"]["form_keys"] = list(request.form.keys())

    # Add JSON keys if JSON body (not values for security)
    if request.is_json and request.json:
        context["request"]["json_keys"] = list(request.json.keys())

    return context


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Remove sensitive headers before sending to Falcon."""
    sensitive = {
        "authorization",
        "cookie",
        "x-api-key",
        "x-auth-token",
        "x-access-token",
        "x-csrf-token",
        "x-xsrf-token",
    }
    return {
        k: "[REDACTED]" if k.lower() in sensitive else v for k, v in headers.items()
    }


# =============================================================================
# Flask Extension Class (alternative API)
# =============================================================================


class FalconFlask:
    """
    Flask extension class for Falcon error tracking.

    This provides an alternative, more Flask-idiomatic API using the
    extension pattern with init_app().

    Example:
        >>> from flask import Flask
        >>> from falcon_sdk.flask import FalconFlask
        >>>
        >>> falcon_ext = FalconFlask()
        >>>
        >>> def create_app():
        ...     app = Flask(__name__)
        ...     app.config["FALCON_API_KEY"] = "fk_xxx"
        ...     app.config["FALCON_APP_NAME"] = "my-app"
        ...     falcon_ext.init_app(app)
        ...     return app

    With factory pattern and multiple apps:
        >>> falcon_ext = FalconFlask()
        >>>
        >>> app1 = Flask("app1")
        >>> app1.config["FALCON_API_KEY"] = "fk_key1"
        >>> app1.config["FALCON_APP_NAME"] = "app1"
        >>> falcon_ext.init_app(app1)
        >>>
        >>> app2 = Flask("app2")
        >>> app2.config["FALCON_API_KEY"] = "fk_key2"
        >>> app2.config["FALCON_APP_NAME"] = "app2"
        >>> falcon_ext.init_app(app2)
    """

    def __init__(self, app: "Flask | None" = None) -> None:
        """
        Initialize the extension.

        Args:
            app: Optional Flask app. If provided, init_app() is called immediately.
        """
        self._falcon_instances: dict[int, Falcon] = {}

        if app is not None:
            self.init_app(app)

    def init_app(self, app: "Flask", falcon: Falcon | None = None) -> Falcon:
        """
        Initialize Falcon for a Flask application.

        Args:
            app: The Flask application instance
            falcon: Optional Falcon instance

        Returns:
            The Falcon instance
        """
        instance = init_app(app, falcon)
        self._falcon_instances[id(app)] = instance
        return instance

    def get_falcon(self, app: "Flask") -> Falcon | None:
        """Get the Falcon instance for a specific app."""
        return self._falcon_instances.get(id(app))

    @property
    def falcon(self) -> Falcon | None:
        """
        Get Falcon instance for current app context.

        Returns:
            The Falcon instance or None if not in app context
        """
        from flask import current_app

        try:
            return get_falcon(current_app)
        except RuntimeError:
            # Not in app context
            return None

    def capture_exception(
        self,
        error: BaseException,
        *,
        context: dict | None = None,
        level: str = "error",
        tags: dict[str, str] | None = None,
    ) -> None:
        """
        Capture an exception using the current app's Falcon instance.

        Args:
            error: The exception to capture
            context: Additional context
            level: Error level
            tags: Tags for categorization
        """
        if self.falcon:
            self.falcon.capture_exception(
                error,
                context=context,
                level=level,
                tags=tags,
            )

    def capture_message(
        self,
        message: str,
        *,
        level: str = "info",
        context: dict | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        """
        Capture a message using the current app's Falcon instance.

        Args:
            message: The message to capture
            level: Message level
            context: Additional context
            tags: Tags for categorization
        """
        if self.falcon:
            self.falcon.capture_message(
                message,
                level=level,
                context=context,
                tags=tags,
            )
