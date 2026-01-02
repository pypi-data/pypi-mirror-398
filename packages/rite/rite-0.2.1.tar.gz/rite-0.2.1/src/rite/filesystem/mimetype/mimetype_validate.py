# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Filesystem - MIME Type Validation Module
===============================================

Provides functionality to validate MIME types of files or data.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import Any, Iterable

# Import | Local Modules
from .mimetype_guess import mimetype_guess
from .mimetype_match import mimetype_match


# =============================================================================
# Classes & Functions
# =============================================================================
class MimeValidationError(ValueError):
    """Raised when a value does not satisfy MIME type constraints."""


def validate_mimetype(
    input_object: Any,
    *,
    allowed: Iterable[str] | None = None,
    forbidden: Iterable[str] | None = None,
) -> str:
    """
    Validate MIME type of ``input_object`` without any Django dependency.

    Returns the detected MIME string on success.
    Raises MimeValidationError on failure.
    """
    mime = mimetype_guess(input_object)
    if not mime:
        raise MimeValidationError("Could not determine MIME type.")

    if forbidden:
        for pattern in forbidden:
            if mimetype_match(mime, str(pattern)):
                raise MimeValidationError(
                    f"Files of type '{mime}' are not allowed."
                )

    if allowed:
        for pattern in allowed:
            if mimetype_match(mime, str(pattern)):
                break
        else:
            allowed_list = ", ".join(map(str, allowed))
            raise MimeValidationError(
                f"Only the following types are allowed: {allowed_list}."
            )

    return mime


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["validate_mimetype"]
