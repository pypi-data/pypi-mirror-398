# =============================================================================
# Docstring
# =============================================================================

"""
Extension Guesser
=================

Guess file extension from MIME type.

Examples
--------
>>> from rite.net.mime import mime_guess_extension
>>> mime_guess_extension("application/json")
'.json'

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


def mime_guess_extension(mime_type: str) -> str | None:
    """
    Guess file extension from MIME type.

    Args:
        mime_type: MIME type string.

    Returns:
        Extension with dot or None.

    Examples:
        >>> mime_guess_extension("application/json")
        '.json'
        >>> mime_guess_extension("image/png")
        '.png'
        >>> mime_guess_extension("unknown/type") is None
        True

    Notes:
        Uses mimetypes module.
        Returns extension with leading dot.
    """
    return mimetypes.guess_extension(mime_type)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["mime_guess_extension"]
