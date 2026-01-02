# =============================================================================
# Docstring
# =============================================================================

"""
Filename Sanitizer
==================

Sanitize filenames for safe filesystem use.

Examples
--------
>>> from rite.markup.sanitize import sanitize_filename
>>> sanitize_filename("file:name?.txt")
'filename.txt'

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


def sanitize_filename(filename: str, replacement: str = "") -> str:
    """
    Sanitize filename by removing unsafe characters.

    Args:
        filename: Filename to sanitize.
        replacement: Character to replace unsafe chars with.

    Returns:
        Safe filename.

    Examples:
        >>> sanitize_filename("my/file:name.txt")
        'myfilename.txt'
        >>> sanitize_filename("file<>name.txt", "_")
        'file__name.txt'

    Notes:
        Removes: / \\ : * ? " < > |
        Preserves file extension.
    """
    # Remove unsafe characters
    unsafe_pattern = r'[/\\:*?"<>|]'
    safe = re.sub(unsafe_pattern, replacement, filename)

    # Remove leading/trailing dots and spaces
    safe = safe.strip(". ")

    # Ensure not empty
    if not safe:
        safe = "file"

    return safe


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["sanitize_filename"]
