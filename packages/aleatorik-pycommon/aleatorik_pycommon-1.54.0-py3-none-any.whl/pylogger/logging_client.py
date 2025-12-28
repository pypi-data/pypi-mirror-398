from typing import Any

from pydantic import BaseModel

from pylogger.logger import logger_instance
from pylogger.utils.template import LogCategory, LogLevel


class LoggingClient:
    """Carries a RequestEntry and attaches it to every log."""

    class RequestEntry(BaseModel):
        traceId: str | None = None  # noqa: N815
        userId: str | None = None  # noqa: N815
        userAgent: str | None = None  # noqa: N815
        requestPath: str | None = None  # noqa: N815
        method: str | None = None
        tenantInfo: dict[str, Any] | None = None  # noqa: N815

    def __init__(self, request_entry: RequestEntry | None = None):
        self._request_entry = request_entry or self.RequestEntry()

    @classmethod
    def from_request_entry(cls, request_entry: dict[str, Any]) -> "LoggingClient":
        """Create LoggingClient from serialized context.

        Args:
            context: Dictionary from get_context() or manually built

        Returns:
            New LoggingClient with restored context.
        """
        return cls(cls.RequestEntry(**request_entry))

    def set_request_entry(self, context: dict[str, Any]) -> None:
        if context:
            self._request_entry = self.RequestEntry(**context)
        else:
            self._request_entry = self.RequestEntry()

    def get_request_entry(self) -> dict[str, Any]:
        """Get serializable current request entry.

        Returns:
            Dictionary containing request metadata.
        """
        return self._request_entry.model_dump(exclude_none=True)

    def send_log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        data: dict[str, Any] | None = None,
        force_clean: bool = False,
    ) -> None:
        """Send structured log with request context.

        Args:
            level: Log level (info, warning, error, debug)
            category: Log category (access, service, query, etc.)
            message: Log message
            data: Additional data to include in the 'properties' field
            force_clean: If True, reset log context
        """
        # Merge the structured request entry with any given data
        request_data = self._request_entry.model_dump(exclude_none=True)
        merged = {**request_data, **(data or {})}

        logger_instance.bind_base_info()
        logger_instance.send_log(
            level=level,
            category=category,
            message=message,
            data=merged,
            force_clean=force_clean,
        )


# Global instance for non-request contexts (empty request entry)
logger_client = LoggingClient()
