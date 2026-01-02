"""
Metrics endpoint for Falcon SDK.

Provides a Prometheus-compatible metrics endpoint that Falcon can scrape
to collect application metrics.
"""

from __future__ import annotations

import gc
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

DEFAULT_METRICS_PATH = "/__falcon/metrics"

# Track process start time
_start_time = time.time()

# Internal metrics storage
_counters: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
_gauges: dict[str, float] = {}

# Request metrics
_total_requests = 0
_requests_by_method: dict[str, int] = defaultdict(int)
_requests_by_status: dict[int, int] = defaultdict(int)
_request_durations: list[float] = []


@dataclass
class Metric:
    """A single metric."""

    name: str
    help: str
    type: str  # "counter", "gauge", "histogram"
    value: float
    labels: dict[str, str] = field(default_factory=dict)


def increment_counter(
    name: str, labels: dict[str, str] | None = None, value: float = 1.0
) -> None:
    """
    Increment a counter metric.

    Args:
        name: Metric name
        labels: Optional labels
        value: Amount to increment (default: 1)
    """
    label_key = _labels_to_key(labels or {})
    _counters[name][label_key] += value


def set_gauge(name: str, value: float) -> None:
    """
    Set a gauge metric.

    Args:
        name: Metric name
        value: Gauge value
    """
    _gauges[name] = value


def record_request(method: str, status_code: int, duration_ms: float) -> None:
    """
    Record a request for metrics.

    Args:
        method: HTTP method
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    """
    global _total_requests

    _total_requests += 1
    _requests_by_method[method] += 1
    _requests_by_status[status_code] += 1
    _request_durations.append(duration_ms)

    # Keep only last 1000 durations
    if len(_request_durations) > 1000:
        _request_durations.pop(0)


def _labels_to_key(labels: dict[str, str]) -> str:
    """Convert labels dict to a hashable key."""
    if not labels:
        return ""
    sorted_items = sorted(labels.items())
    return ",".join(f'{k}="{v}"' for k, v in sorted_items)


def _collect_builtin_metrics() -> list[Metric]:
    """Collect built-in process and request metrics."""
    metrics: list[Metric] = []

    # Process metrics
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        metrics.append(
            Metric(
                name="process_cpu_user_seconds",
                help="Process CPU user time in seconds",
                type="counter",
                value=usage.ru_utime,
            )
        )
        metrics.append(
            Metric(
                name="process_cpu_system_seconds",
                help="Process CPU system time in seconds",
                type="counter",
                value=usage.ru_stime,
            )
        )
        metrics.append(
            Metric(
                name="process_memory_rss_bytes",
                help="Process RSS memory in bytes",
                type="gauge",
                value=usage.ru_maxrss * 1024,  # Convert KB to bytes on most systems
            )
        )
    except ImportError:
        # resource not available on Windows
        pass

    # Python GC stats
    gc_stats = gc.get_stats()
    for i, gen_stats in enumerate(gc_stats):
        metrics.append(
            Metric(
                name="python_gc_collections",
                help="Number of GC collections",
                type="counter",
                value=gen_stats["collections"],
                labels={"generation": str(i)},
            )
        )

    # Uptime
    metrics.append(
        Metric(
            name="process_uptime_seconds",
            help="Process uptime in seconds",
            type="gauge",
            value=time.time() - _start_time,
        )
    )

    # PID
    metrics.append(
        Metric(
            name="process_pid",
            help="Process ID",
            type="gauge",
            value=os.getpid(),
        )
    )

    # Request metrics
    metrics.append(
        Metric(
            name="http_requests_total_count",
            help="Total number of HTTP requests",
            type="counter",
            value=_total_requests,
        )
    )

    # Average request duration
    if _request_durations:
        avg_duration = sum(_request_durations) / len(_request_durations)
        metrics.append(
            Metric(
                name="http_request_duration_avg_ms",
                help="Average HTTP request duration in milliseconds",
                type="gauge",
                value=round(avg_duration, 2),
            )
        )

    # Requests by method
    for method, count in _requests_by_method.items():
        metrics.append(
            Metric(
                name="http_requests_by_method",
                help="HTTP requests by method",
                type="counter",
                value=count,
                labels={"method": method},
            )
        )

    # Requests by status
    for status, count in _requests_by_status.items():
        metrics.append(
            Metric(
                name="http_requests_by_status",
                help="HTTP requests by status code",
                type="counter",
                value=count,
                labels={"status": str(status)},
            )
        )

    # Custom counters
    for name, label_values in _counters.items():
        for label_key, value in label_values.items():
            labels = {}
            if label_key:
                for pair in label_key.split(","):
                    k, v = pair.split("=")
                    labels[k] = v.strip('"')
            metrics.append(
                Metric(
                    name=name,
                    help=f"Counter {name}",
                    type="counter",
                    value=value,
                    labels=labels if labels else {},
                )
            )

    # Custom gauges
    for name, value in _gauges.items():
        metrics.append(
            Metric(
                name=name,
                help=f"Gauge {name}",
                type="gauge",
                value=value,
            )
        )

    return metrics


def format_prometheus(metrics: list[Metric] | None = None) -> str:
    """
    Format metrics in Prometheus text format.

    Args:
        metrics: List of metrics to format (default: collect built-in)

    Returns:
        Prometheus-formatted metrics string
    """
    if metrics is None:
        metrics = _collect_builtin_metrics()

    lines: list[str] = []
    seen: set[str] = set()

    for metric in metrics:
        # Add HELP and TYPE only once per metric name
        if metric.name not in seen:
            lines.append(f"# HELP {metric.name} {metric.help}")
            lines.append(f"# TYPE {metric.name} {metric.type}")
            seen.add(metric.name)

        # Format the metric line
        if metric.labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in metric.labels.items())
            lines.append(f"{metric.name}{{{label_str}}} {metric.value}")
        else:
            lines.append(f"{metric.name} {metric.value}")

    return "\n".join(lines)
