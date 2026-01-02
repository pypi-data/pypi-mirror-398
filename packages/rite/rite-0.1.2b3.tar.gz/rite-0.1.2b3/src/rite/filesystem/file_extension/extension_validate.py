# =============================================================================
# Docstring
# =============================================================================

"""
File Extension Validation Module
================================

Provides utilities for validating file extensions.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Iterable
import re

# Import | Local Modules
from .extension_regex import EXTENSION_REGEX

# =============================================================================
# Functions
# =============================================================================


def extension_validate(
    extension: str | None,
    *,
    allowed: Iterable[str] | None = None,
    regex: re.Pattern[str] = EXTENSION_REGEX,
) -> None:
    """
    Validate a file extension.

    Args:
    ----
        extension: Extension string to validate (should be normalized).
        allowed: Optional iterable of allowed extensions (case-insensitive).
        regex: Pattern to match valid extensions.

    Raises:
    ------
        ValueError: If extension is None/empty, doesn't match regex, or not allowed.

    Example:
    -------
        >>> extension_validate("pdf")
        >>> extension_validate("jpg", allowed=["png", "jpg", "gif"])
        >>> extension_validate("exe", allowed=["png", "jpg"])
        Traceback (most recent call last):
        ValueError: Extension 'exe' not allowed...

    """
    if extension is None:
        raise ValueError("File extension is empty or None.")

    # Normalize: strip spaces, remove leading dots, lowercase
    normalized_extension = str(extension).strip().lstrip(".").lower()
    if not normalized_extension:
        raise ValueError("File extension is empty or None.")

    if not regex.match(normalized_extension):
        raise ValueError(f"Invalid file extension: {extension!r}")

    if allowed is not None:
        allowed_normalized = {
            str(candidate).lstrip(".").lower() for candidate in allowed
        }
        if normalized_extension not in allowed_normalized:
            allowed_str = ", ".join(sorted(allowed_normalized)) or "∅"
            raise ValueError(
                f"Extension '{normalized_extension}' not allowed. Allowed: {allowed_str}"
            )


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "extension_validate",
]
