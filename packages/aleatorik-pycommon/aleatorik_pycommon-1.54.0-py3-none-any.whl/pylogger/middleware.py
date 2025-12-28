"""Universal FastAPI logging middleware.

Provides:
- Base middleware for request lifecycle logging
- LoggingClient: For worker processes (threading/ProcessPool) only
- Direct logger access via request.state
- Optional response inspection callback for app-specific logging
"""

from collections.abc import Callable
from urllib.parse import urlparse

from fastapi import FastAPI, Request, Response

from pylogger.logger import logger_instance
from pylogger.logging_client import LoggingClient


def setup_http_middleware(
    app: FastAPI,
    *,
    excluded_paths: tuple[str, ...] | None = None,
    log_access: bool = True,
    attach_logger_client: bool = False,
    on_response_callback: Callable[[bytes, int, str], None] | None = None,
) -> None:
    """Registers HTTP logging middleware in the FastAPI app.

    Args:
        app: FastAPI application instance
        excluded_paths: Tuple of path suffixes to exclude from logging
        log_access: Enable access logging (path logging)
        attach_logger_client: Attach LoggingClient to request.state
        on_response_callback: Optional callback(body, status_code, path) for custom response inspection

    Example:
        >>> def inspect_responses(body: bytes, status_code: int, path: str):
        >>> # Custom app-specific response logging
        >>>     pass
        >>>
        >>> setup_http_middleware(app, on_response_callback=inspect_responses)
    """

    # Default excluded paths
    if excluded_paths is None:
        excluded_paths = (
            "/health",
            "/openapi.json",
            "/docs",
            "/redoc",
            "/metrics",
        )

    def _log_access(path: str) -> None:
        try:
            logger_instance.send_log(level="info", category="access", message=path)
        except Exception:
            pass

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        """Process request with logging context."""
        token = logger_instance.begin_request()
        try:
            logger_instance.bind_base_info()
            fields = logger_instance.bind_request_properties(request)

            # Optional: Create LoggingClient (for backward compatibility)
            if attach_logger_client:
                entry = LoggingClient.RequestEntry(**fields)
                request.state.logger = LoggingClient(entry)

            clean_path: str = urlparse(str(request.url)).path.rstrip("/")
            if clean_path.endswith(excluded_paths):
                return await call_next(request)

            if log_access:
                _log_access(clean_path)

            # Process request
            response = await call_next(request)

            # Streaming response - consume body_iterator
            try:
                response_body = b"".join(
                    [chunk async for chunk in response.body_iterator]
                )
            except Exception:
                response_body = b""  # Keep empty if iteration fails

            # Call custom response inspector if provided
            if on_response_callback:
                try:
                    on_response_callback(
                        response_body, response.status_code, clean_path
                    )
                except Exception:
                    pass  # Don't break response flow

            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        finally:
            logger_instance.end_request(token)
