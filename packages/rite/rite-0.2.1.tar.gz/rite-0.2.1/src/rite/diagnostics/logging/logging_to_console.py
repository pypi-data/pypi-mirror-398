# =============================================================================
# Docstring
# =============================================================================

"""
Console Logger
==============

Create logger that writes to console/stdout.

Examples
--------
>>> from rite.diagnostics.logging import logging_to_console
>>> logger = logging_to_console("app")
>>> logger.info("Application started")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import logging

# =============================================================================
# Functions
# =============================================================================


def logging_to_console(
    name: str,
    level: int = logging.INFO,
    format_string: str | None = None,
    colorize: bool = False,
) -> logging.Logger:
    """
    Create logger that writes to console.

    Args:
        name: Logger name.
        level: Logging level (default INFO).
        format_string: Custom format string.
        colorize: If True, colorize output by level.

    Returns:
        Configured console logger.

    Examples:
        >>> logger = logging_to_console("app")
        >>> logger.info("Hello world")
        >>> logger = logging_to_console("debug", level=logging.DEBUG)
        >>> logger.debug("Debug message")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()

        if format_string is None:
            format_string = (
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        formatter: logging.Formatter
        if colorize:
            formatter = _ColorFormatter(format_string)
        else:
            formatter = logging.Formatter(format_string)

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# =============================================================================
# Color Formatter
# =============================================================================


class _ColorFormatter(logging.Formatter):
    """Colorize log output by level."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format with color codes."""
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["logging_to_console"]
