# =============================================================================
# Docstring
# =============================================================================

"""
File Logger
===========

Create logger that writes to a file with rotation support.

Examples
--------
>>> from rite.diagnostics.logging import logging_to_file
>>> logger = logging_to_file("app", "app.log")
>>> logger.info("Application started")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import logging
from logging.handlers import RotatingFileHandler

# =============================================================================
# Functions
# =============================================================================


def logging_to_file(
    name: str,
    filepath: str,
    level: int = logging.INFO,
    max_bytes: int = 10485760,
    backup_count: int = 5,
    format_string: str | None = None,
) -> logging.Logger:
    """
    Create logger that writes to a file with rotation.

    Args:
        name: Logger name.
        filepath: Path to log file.
        level: Logging level (default INFO).
        max_bytes: Max file size before rotation (default 10MB).
        backup_count: Number of backup files to keep (default 5).
        format_string: Custom format string.

    Returns:
        Configured file logger.

    Examples:
        >>> logger = logging_to_file("app", "logs/app.log")
        >>> logger.info("Starting application")
        >>> logger = logging_to_file(
        ...     "api",
        ...     "logs/api.log",
        ...     max_bytes=5242880,
        ...     backup_count=3
        ... )
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = RotatingFileHandler(
            filepath, maxBytes=max_bytes, backupCount=backup_count
        )

        if format_string is None:
            format_string = (
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["logging_to_file"]
