# =============================================================================
# Docstring
# =============================================================================

"""
MIME Type Guesser
=================

Guess MIME type from filename.

Examples
--------
>>> from rite.net.mime import mime_guess_type
>>> mime_guess_type("file.json")
'application/json'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import mimetypes

# =============================================================================
# Functions
# =============================================================================


def mime_guess_type(filename: str) -> str | None:
    """
    Guess MIME type from filename.

    Args:
        filename: Filename or path.

    Returns:
        MIME type string or None.

    Examples:
        >>> mime_guess_type("file.json")
        'application/json'
        >>> mime_guess_type("image.png")
        'image/png'
        >>> mime_guess_type("unknown.xyz") is None
        True

    Notes:
        Uses mimetypes module.
        Returns None for unknown types.
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["mime_guess_type"]
