# =============================================================================
# Docstring
# =============================================================================

"""
Filename Sanitization Module
============================

Provides utilities for sanitizing filenames for filesystem safety.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import re

# =============================================================================
# Functions
# =============================================================================


def filename_sanitize(
    filename: str,
    *,
    replacement: str = "_",
    max_length: int | None = 255,
) -> str:
    """
    Sanitize a filename for safe filesystem usage.

    Removes or replaces characters that may be problematic for filesystems.
    Only allows alphanumeric characters, underscores, dots, and hyphens.

    Args:
    ----
        filename: The original filename to sanitize.
        replacement: Character to replace invalid characters with.
        max_length: Optional maximum filename length.

    Returns:
    -------
        str: Sanitized filename.

    Example:
    -------
        >>> filename_sanitize("my file (copy).txt")
        'my_file__copy_.txt'
        >>> filename_sanitize("file:name?.txt", replacement="-")
        'file-name-.txt'
        >>> filename_sanitize("a" * 300, max_length=100)
        'aaaa...'  # (truncated to 100 chars)

    """
    # Remove or replace invalid characters
    sanitized = re.sub(
        r"[^a-zA-Z0-9_.-]",
        replacement,
        filename,
    )

    # Truncate to max length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")

    # Ensure not empty
    if not sanitized:
        sanitized = "unnamed"

    return sanitized


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "filename_sanitize",
]
