# =============================================================================
# Docstring
# =============================================================================

"""
Text Sanitization
=================

Sanitize text to create safe ASCII identifiers.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import re
import unicodedata

# =============================================================================
# Functions
# =============================================================================


def sanitize(
    text: str,
    replacement: str = "_",
) -> str:
    """
    Sanitize text to create safe ASCII identifiers.

    Args:
    ----
        text: The input text to sanitize.
        replacement: The character to replace non-alphanumeric characters.

    Returns:
    -------
        str: The sanitized text with only ASCII alphanumeric characters.

    """

    normalized = (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )

    normalized = re.sub(
        r"[^a-zA-Z0-9]",
        replacement,
        normalized,
    )

    if replacement:
        pattern = re.escape(replacement) + "{2,}"
        normalized = re.sub(
            pattern,
            replacement,
            normalized,
        )
    return normalized.strip(replacement)


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "sanitize",
]
