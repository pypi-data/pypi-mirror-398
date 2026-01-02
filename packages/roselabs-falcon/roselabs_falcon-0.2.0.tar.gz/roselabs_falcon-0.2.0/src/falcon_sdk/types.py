"""Type definitions for Falcon SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ErrorLevel = Literal["debug", "info", "warning", "error", "fatal"]


@dataclass
class UserContext:
    """User context for error tracking."""

    id: str | None = None
    email: str | None = None
    name: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        id: str | None = None,
        email: str | None = None,
        name: str | None = None,
        **extra: Any,
    ):
        self.id = id
        self.email = email
        self.name = name
        self.extra = extra

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API payload."""
        result: dict[str, Any] = {}
        if self.id:
            result["id"] = self.id
        if self.email:
            result["email"] = self.email
        if self.name:
            result["name"] = self.name
        result.update(self.extra)
        return result


@dataclass
class FalconEvent:
    """An error event to be sent to Falcon."""

    message: str
    level: ErrorLevel = "error"
    stack: str | None = None
    context: dict[str, Any] | None = None
    environment: str | None = None
    release: str | None = None
    user_id: str | None = None
    breadcrumbs: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API payload."""
        result: dict[str, Any] = {
            "message": self.message,
            "level": self.level,
        }
        if self.stack:
            result["stack"] = self.stack
        if self.context:
            result["context"] = self.context
        if self.environment:
            result["environment"] = self.environment
        if self.release:
            result["release"] = self.release
        if self.user_id:
            result["user_id"] = self.user_id
        if self.breadcrumbs:
            result["breadcrumbs"] = self.breadcrumbs
        return result


@dataclass
class CaptureOptions:
    """Options for capturing exceptions and messages."""

    context: dict[str, Any] | None = None
    level: ErrorLevel = "error"
    tags: dict[str, str] | None = None
