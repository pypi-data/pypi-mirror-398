import contextvars
import inspect
import json
import sys
from contextvars import Token
from typing import Any
from urllib.parse import urlparse

import requests
from loguru import logger
from requests.models import Request, Response

from pylogger.config import get_settings
from pylogger.model import LogEntry
from pylogger.utils.helper import decode_base64_string, get_header_with_fallback
from pylogger.utils.template import LogCategory, LogLevel

# Global configuration from service's environment variables
FLUENTBIT_URL: str | None = get_settings().FLUENTBIT_URL
COMPONENT_NAME: str | None = get_settings().COMPONENT_NAME
SYSTEM_NAME: str | None = get_settings().SYSTEM_NAME

# Context variable for storing request-scoped log data
log_context_var: contextvars.ContextVar = contextvars.ContextVar(
    "log_context", default=None
)

MAX_MESSAGE_LENGTH = 2000


class PyLogger:
    """Centralized logging with Fluent Bit integration and request context management."""

    _instance = None  # Singleton instance

    def __new__(cls, *args, **kwargs):
        """Ensure only one global instance of PyLogger is created (Singleton pattern)."""
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.setup_logger()
        return cls._instance

    def __init__(self):
        # Instance already initialized in __new__, no additional setup needed
        pass

    def setup_logger(self):
        """Configure loguru with custom sink for Fluent Bit integration."""
        logger.remove()  # Remove default handlers

        # Add console output
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            level="DEBUG",
            colorize=True,
        )
        # Add Custom Fluent Bit sink
        logger.add(
            self.custom_sink,
            format="{message}",
            serialize=True,
            level="INFO",
            enqueue=True,
        )

    def begin_request(self) -> Token:
        """Start a new request log context (clears previous)."""
        return log_context_var.set(logger.bind())

    def end_request(self, token: Token) -> None:
        """Clear request context after request ends."""
        if token is not None:
            log_context_var.reset(token)

    def bind_base_info(self):
        """Bind component and system info to log context."""
        base_info: dict[str, str] = {
            "component": COMPONENT_NAME.lower() if COMPONENT_NAME else "unknown",
            "system": SYSTEM_NAME.lower() if SYSTEM_NAME else "unknown",
        }
        self._bind_persistent(base_info)

    def bind_request_properties(self, request: Request) -> dict[str, Any]:
        """Initializes new log context and bind base properties"""
        required_fields: dict[str, Any] = self._extract_request_fields(request)
        if required_fields:
            self._bind_persistent(required_fields)
        return required_fields

    # Remove this function after 1.54.0 release - kept for backward compatibility
    def add_to_log(self, data: dict[str, Any]) -> None:
        curr_context: logger | None = log_context_var.get()

        if curr_context:
            new_context: logger = curr_context.bind(**data)
        else:
            new_context: logger = logger.bind(**data)

        log_context_var.set(new_context)

    def send_log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        data: dict[str, Any] | None = None,
        force_clean: bool | None = False,
    ) -> None:
        """Send structured log entry with context to Fluent Bit."""
        # Get current context or fallback to base logger
        if force_clean:
            current_context = logger.bind()  # fresh logger, no ContextVar
        else:
            current_context = log_context_var.get() or logger

        base_info = {
            "component": COMPONENT_NAME.lower() if COMPONENT_NAME else "unknown",
            "system": SYSTEM_NAME.lower() if SYSTEM_NAME else "unknown",
        }
        current_context = current_context.bind(**base_info)

        # Extract caller information for source tracking
        caller_frame = inspect.stack()[2]
        per_log = {
            "logCategory": category.lower(),
            "sourceContext": caller_frame.filename,
        }

        # Merge additional data if provided
        if data:
            per_log.update(data)

        # Send log with all context and metadata
        current_context.bind(**per_log).opt(depth=2).log(
            level.upper(),
            self._format_message(level.upper(), category.upper(), message),
        )

    def custom_sink(self, message) -> None:
        """Custom loguru sink that forwards logs to log pipeline."""
        try:
            if FLUENTBIT_URL is None:
                print("Fluentbit URL is not set. Skip logging.")
                return

            # Parse and validate log entry
            log_entry_json = self._parse_before_send(message.record)
            if log_entry_json == "{}":
                print("Log entry rejected. Log will not be sent.")
                return

            # Send to Fluent Bit
            response: Response = requests.post(
                FLUENTBIT_URL,
                data=log_entry_json,
                headers={"Content-Type": "application/json"},
                timeout=5.0,
            )

            if response.status_code != 201:
                print(f"Failed to send log: {response.status_code} {response.text}")

        except Exception as e:
            print(
                f"Error while sending log: {e}"
                f"at {message.record.get('name')}"
                f"at {message.record.get('line')}"
            )

    def _bind_persistent(self, data: dict[str, Any]) -> None:
        base = log_context_var.get() or logger
        log_context_var.set(base.bind(**data))

    def _parse_before_send(self, record) -> str:
        """Parse loguru record into structured log entry."""
        # Build core log structure
        log_entry: dict[str, Any] = {
            "level": record["level"].name,
            "message": self._truncate_message(
                record["message"]
            ),  # truncate message if it exceeds max length
            "timestamp": record["time"].isoformat() if "time" in record else "Unknown",
            "component": record["extra"].get("component"),
            "system": record["extra"].get("system"),
            "method": record["extra"].get("method"),
            "traceId": record["extra"].get("traceId"),
            "tenantInfo": record["extra"].get("tenantInfo"),
            "requestPath": record["extra"].get("requestPath"),
            "logCategory": record["extra"].get("logCategory"),
            "userId": record["extra"].get("userId"),
            "properties": {},
        }

        # Add system and runtime properties
        system_props: dict[str, Any] = {
            "threadId": record["thread"].id,
            "processId": record["process"].id,
            "userAgent": record["extra"].get("userAgent"),
            "sourceContext": record["extra"].get("sourceContext"),
        }
        log_entry["properties"].update(system_props)

        # Add any additional service-specific fields
        for key, value in record.get("extra", {}).items():
            if value is not None and key not in system_props and key not in log_entry:
                camel_case_key = self._to_camel_case(key)
                log_entry["properties"][camel_case_key] = value

        # Validate structure before sending
        try:
            validated_entry: LogEntry = LogEntry(**log_entry)
            final_log_entry: dict[str, Any] = validated_entry.model_dump(
                exclude_none=True
            )
        except Exception as e:
            print(
                f"LogEntry validation failed for {COMPONENT_NAME}. Skipping logging: {e}"
            )
            return "{}"  # Return empty JSON to reject invalid entries

        return json.dumps(final_log_entry)

    def _format_message(self, level: str, category: str, message: str) -> str:
        return f"[{level.upper()}] [{category.upper()}] - {message}"

    def _truncate_message(self, message: str) -> str:
        if len(message) > MAX_MESSAGE_LENGTH:
            return "[TRUNCATED] " + message[: MAX_MESSAGE_LENGTH - 13]
        return message

    def _to_camel_case(self, unformatted_str: str) -> str:
        """Convert snake_case, kebab-case, or PascalCase to camelCase"""
        if not unformatted_str:
            return unformatted_str

        # Handle kebab-case by replacing hyphens with underscores
        unformatted_str: str = unformatted_str.replace("-", "_")

        # Split on underscores and handle each component
        components: list[str] = unformatted_str.split("_")

        # If there's only one component, check if it's PascalCase and convert
        if len(components) == 1:
            # Convert PascalCase to camelCase (first letter lowercase)
            return components[0][0].lower() + components[0][1:] if components[0] else ""

        # For multiple components, first component stays lowercase, rest become title case
        return components[0].lower() + "".join(word.title() for word in components[1:])

    def _extract_request_fields(self, request: Request) -> dict[str, Any]:
        """Extract logging fields from HTTP request and headers."""
        headers: dict[str, str] = request.headers
        extracted_fields: dict[str, Any] = {}

        # Extract tenant information with case-insensitive header lookup
        tenant_id = decode_base64_string(
            get_header_with_fallback(headers, ["tenant-id", "tenant-Id", "Tenant-Id"])
        )
        tenant_name = decode_base64_string(
            get_header_with_fallback(
                headers, ["tenant-name", "tenant-Name", "Tenant-Name"]
            )
        )
        project_name = decode_base64_string(
            get_header_with_fallback(
                headers, ["project-name", "project-Name", "Project-Name"]
            )
        )
        project_id = decode_base64_string(
            get_header_with_fallback(headers, ["projectID", "ProjectID"])
        )

        # Build tenant info object (exclude None values)
        tenant_info: dict[str, Any] = {}
        if project_id:
            tenant_info["projectId"] = project_id
        if project_name:
            tenant_info["projectName"] = project_name
        if tenant_id:
            tenant_info["tenantId"] = tenant_id
        if tenant_name:
            tenant_info["tenantName"] = tenant_name

        if tenant_info:
            extracted_fields["tenantInfo"] = tenant_info

        # Extract standard request fields
        request_fields = {
            "traceId": headers.get("TraceID"),
            "userId": headers.get("UserID"),
            "userAgent": headers.get("User-Agent"),
            "requestPath": urlparse(str(request.url)).path,
            "method": request.method,
        }

        # Only include non-None values
        extracted_fields.update({k: v for k, v in request_fields.items() if v})

        return extracted_fields


# Initialize the global logger instance
logger_instance = PyLogger()
