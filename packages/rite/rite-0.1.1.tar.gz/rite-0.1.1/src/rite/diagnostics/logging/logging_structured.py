# =============================================================================
# Docstring
# =============================================================================

"""
Structured Logger
=================

Logger with structured output (JSON, key-value pairs).

Examples
--------
>>> from rite.diagnostics.logging import logging_structured
>>> logger = logging_structured("app")
>>> logger.info("User logged in", user_id=123, ip="192.168.1.1")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import json
import logging
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def logging_structured(
    name: str, level: int = logging.INFO, json_format: bool = True
) -> logging.Logger:
    """
    Create logger with structured output.

    Args:
        name: Logger name.
        level: Logging level (default INFO).
        json_format: If True, output as JSON; else key=value format.

    Returns:
        Configured logger with structured formatter.

    Examples:
        >>> logger = logging_structured("app")
        >>> logger.info("Event occurred", user_id=123)
        >>> logger = logging_structured("api", json_format=False)
        >>> logger.warning("Slow query", duration_ms=500)
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()

        formatter: logging.Formatter
        if json_format:
            formatter = _JSONFormatter()
        else:
            formatter = _KeyValueFormatter()

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# =============================================================================
# Formatters
# =============================================================================


class _JSONFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ):
                log_data[key] = value

        return json.dumps(log_data)


class _KeyValueFormatter(logging.Formatter):
    """Format log records as key=value pairs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as key=value string."""
        base = (
            f"{self.formatTime(record)} "
            f"level={record.levelname} "
            f"logger={record.name} "
            f'message="{record.getMessage()}"'
        )

        # Add extra fields
        extras = []
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ):
                extras.append(f'{key}="{value}"')

        if extras:
            base += " " + " ".join(extras)

        return base


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["logging_structured"]
