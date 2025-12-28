"""Structured logging models with enum support.

Provides:
- LogEntry model with enum validation for levels and categories
- Type-safe enums for LogLevel and LogCategory
"""

from typing import Any

from pydantic import BaseModel, Field

from pylogger.utils.template import LogCategory, LogLevel


class LogEntry(BaseModel):
    """Base log entry model with enum validation."""

    level: LogLevel | str
    message: str = Field(..., min_length=1, max_length=2000)
    logCategory: LogCategory | str | None = None  # noqa: N815
    component: str | None = Field(None, max_length=100)
    system: str | None = Field(None, max_length=100)
    method: str | None = Field(None, max_length=20)
    traceId: str | None = Field(None, max_length=100)  # noqa: N815
    tenantInfo: dict[str, Any] | None = None  # noqa: N815
    requestPath: str | None = Field(None, max_length=500)  # noqa: N815
    timestamp: str | None = None
    userId: str | None = Field(None, max_length=100)  # noqa: N815
    properties: dict[str, Any] | None = Field(
        None, description="Additional custom properties or contextual data."
    )
