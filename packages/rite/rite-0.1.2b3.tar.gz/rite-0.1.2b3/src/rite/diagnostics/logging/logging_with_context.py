# =============================================================================
# Docstring
# =============================================================================

"""
Context Logger
==============

Logger that includes contextual information in all messages.

Examples
--------
>>> from rite.diagnostics.logging import logging_with_context
>>> logger = logging_with_context("app", request_id="abc123")
>>> logger.info("Processing request")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import logging
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def logging_with_context(
    name: str, level: int = logging.INFO, **context: Any
) -> logging.LoggerAdapter:
    """
    Create logger that includes context in all messages.

    Args:
        name: Logger name.
        level: Logging level (default INFO).
        **context: Context key-value pairs to include.

    Returns:
        Logger adapter with context.

    Examples:
        >>> logger = logging_with_context(
        ...     "api",
        ...     request_id="req123",
        ...     user_id=456
        ... )
        >>> logger.info("Request processed")
        >>> logger = logging_with_context(
        ...     "worker",
        ...     worker_id="w1",
        ...     queue="default"
        ... )
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logging.LoggerAdapter(logger, context)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["logging_with_context"]
