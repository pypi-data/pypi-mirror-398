

# =============================================================================
# Docstring
# =============================================================================

"""
File Extension Normalization Module
===================================

Provides utilities for normalizing file extensions.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def extension_normalize(
    extension: str | None,
    *,
    leading_dot: bool = False,
) -> str | None:
    """
    Normalize a file extension.

    Strips whitespace and leading dots, converts to lowercase.

    Args:
    ----
        extension: Extension string (e.g. ".JPG", " pdf ", "tar.gz").
        leading_dot: If True, return with a leading ".".

    Returns:
    -------
        str | None: Normalized extension, or None if empty/None.

    Example:
    -------
        >>> extension_normalize(".JPG")
        'jpg'
        >>> extension_normalize(" PDF ", leading_dot=True)
        '.pdf'
        >>> extension_normalize("  ")
        None

    """
    if extension is None:
        return None

    normalized_value = str(extension).strip().lstrip(".").lower()
    if not normalized_value:
        return None

    return f".{normalized_value}" if leading_dot else normalized_value


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "extension_normalize",
]
