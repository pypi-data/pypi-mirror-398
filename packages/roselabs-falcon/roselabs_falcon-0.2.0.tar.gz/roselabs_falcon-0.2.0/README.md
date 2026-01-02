# roselabs-falcon

Official Falcon error tracking SDK for Python.

## Installation

```bash
pip install roselabs-falcon
```

## Quick Start

```python
from falcon_sdk import init, capture_exception

# Initialize Falcon - validates immediately, fails fast on bad config
init(
    api_key="sk_your_api_key",
    app_name="my-app",
    environment="production",
)

# That's it! Now capture errors manually or install auto-capture.
```

## Automatic Exception Capture

```python
from falcon_sdk import Falcon, FalconConfig

falcon = Falcon(FalconConfig(
    api_key="sk_your_api_key",
    app_name="my-app",
    environment="production",
))

# Install automatic exception handler
falcon.install()

# Now uncaught exceptions are automatically reported
```

## Manual Error Capture

```python
from falcon_sdk import capture_exception

try:
    risky_operation()
except Exception as e:
    capture_exception(e, context={"user_id": "123", "action": "checkout"})
```

## Capture Messages

```python
from falcon_sdk import capture_message

capture_message("User completed signup", level="info", context={"plan": "pro"})
```

## User Context

```python
from falcon_sdk import set_user

# Set user context for all future events
set_user(user_id="user-123", email="user@example.com", name="John Doe")

# Clear user on logout
set_user()
```

## Async Support

```python
from falcon_sdk import Falcon, FalconConfig

falcon = Falcon(FalconConfig(
    api_key="sk_your_api_key",
    app_name="my-app",
))

# Async capture
await falcon.capture_exception_async(error)
await falcon.capture_message_async("Hello", level="info")
```

## Configuration Options

```python
from falcon_sdk import Falcon, FalconConfig

falcon = Falcon(FalconConfig(
    # Required
    api_key="sk_your_api_key",
    app_name="my-app",

    # Optional
    environment="production",           # Default: None
    release="1.0.0",                    # Default: None
    api_url="https://api.falcon.roselabs.io",  # Default
    enabled=True,                       # Default: True
    debug=False,                        # Default: False

    # Rate limiting (prevents error storms)
    max_events_per_minute=60,           # Default: 60, 0=unlimited
    max_events_per_second=10,           # Default: 10, 0=unlimited

    # Before send hook
    before_send=lambda event: event,    # Return None to drop
))
```

## Pre-validation

The SDK validates configuration immediately on initialization. If your config is invalid, you'll get a `FalconConfigError` right away instead of silent failures later:

```python
from falcon_sdk import init, FalconConfigError

try:
    init(api_key="bad_key", app_name="my-app")  # Missing sk_ prefix
except FalconConfigError as e:
    print(f"Config error: {e}")
    # Invalid Falcon configuration:
    #   - apiKey must start with 'sk_' (e.g., 'sk_your_key_here')
```

## Rate Limiting

Built-in rate limiting prevents error storms from overwhelming your server:

```python
init(
    api_key="sk_xxx",
    app_name="my-app",
    max_events_per_second=10,   # Burst limit
    max_events_per_minute=60,   # Sustained limit
)
```

When limits are exceeded, events are silently dropped (logged in debug mode).

## Logging Integration

Automatically send Python logging errors to Falcon:

```python
import logging
from falcon_sdk import Falcon, FalconConfig

falcon = Falcon(FalconConfig(api_key="sk_xxx", app_name="my-app"))

# Add Falcon handler to root logger
logging.getLogger().addHandler(falcon.get_logging_handler())

# Now logging.error() also reports to Falcon
logging.error("Something went wrong!")
```

## Decorator

Automatically capture errors from functions:

```python
from falcon_sdk import Falcon, FalconConfig

falcon = Falcon(FalconConfig(api_key="sk_xxx", app_name="my-app"))

@falcon.capture_errors
def risky_function():
    raise ValueError("Something went wrong")

@falcon.capture_errors
async def risky_async_function():
    raise ValueError("Async error")
```

## FastAPI Integration

Use `instrument_fastapi` for automatic error capture, health checks, and metrics:

```python
from fastapi import FastAPI
from falcon_sdk import Falcon, FalconConfig, instrument_fastapi

app = FastAPI()
falcon = Falcon(FalconConfig(
    api_key="sk_your_api_key",
    app_name="my-app",
))

# Full instrumentation with uptime and metrics
instrument_fastapi(
    app,
    falcon,
    auto_uptime=True,   # Creates /__falcon/health endpoint
    auto_metrics=True,  # Creates /__falcon/metrics endpoint
)

# Or with custom paths and health check
async def check_db():
    await db.execute("SELECT 1")
    return True

instrument_fastapi(
    app,
    falcon,
    auto_uptime=True,
    auto_metrics=True,
    health_path="/health",   # Custom path
    metrics_path="/metrics", # Custom path
    health_check=check_db,   # Custom health check
)
```

The SDK automatically:

- Captures uncaught errors from your routes
- Creates a health endpoint for Falcon uptime monitoring
- Exposes Prometheus-compatible metrics (CPU, memory, request counts)

## Custom Metrics

```python
from falcon_sdk import increment_counter, set_gauge

# Increment a counter (e.g., user signups)
increment_counter("user_signups", labels={"plan": "pro"})

# Set a gauge (e.g., active connections)
set_gauge("active_connections", 42)
```

## License

MIT
