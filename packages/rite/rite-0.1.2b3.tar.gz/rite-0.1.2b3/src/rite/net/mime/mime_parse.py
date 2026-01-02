# =============================================================================
# Docstring
# =============================================================================

"""
MIME Type Parser
================

Parse MIME type into main type and subtype.

Examples
--------
>>> from rite.net.mime import mime_parse
>>> mime_parse("application/json")
('application', 'json')

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def mime_parse(mime_type: str) -> tuple[str, str]:
    """
    Parse MIME type into main type and subtype.

    Args:
        mime_type: MIME type string.

    Returns:
        Tuple of (main_type, subtype).

    Examples:
        >>> mime_parse("application/json")
        ('application', 'json')
        >>> mime_parse("text/html; charset=utf-8")
        ('text', 'html')
        >>> mime_parse("image/png")
        ('image', 'png')

    Notes:
        Strips parameters like charset.
        Raises ValueError for invalid format.
    """
    # Remove parameters
    base = mime_type.split(";")[0].strip()

    # Split into parts
    parts = base.split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid MIME type format: {mime_type}")

    return parts[0].strip(), parts[1].strip()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["mime_parse"]
