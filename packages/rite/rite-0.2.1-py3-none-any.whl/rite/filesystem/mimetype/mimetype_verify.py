# =============================================================================
# Docstring
# =============================================================================

"""
Verify Mimetype Function
=================================

Check File Type

This function checks the MIME type of a file to determine if it matches
allowed types, which is useful for validating uploaded files.

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


def mimetype_verify(filename: str, allowed_types: list) -> bool:
    """
    Verify Mimetype Function
    ========================

    Verifies if the MIME type of a given file is within the allowed types.

    Parameters:
    - filename (str): The path or name of the file to check.
    - allowed_types (list): A list of allowed MIME types (e.g.,
      ['image/jpeg', 'image/png']).

    Returns:
    - bool: True if the file's MIME type is allowed, False otherwise.
    """

    if not isinstance(allowed_types, list) or not all(
        isinstance(item, str) for item in allowed_types
    ):
        raise ValueError("'allowed_types' must be a list of strings.")

    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type in allowed_types


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "mimetype_verify",
]
