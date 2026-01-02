# =============================================================================
# Docstring
# =============================================================================

"""
Text Cleaning
=============

Remove extra whitespace from text.

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


def clean(text: str) -> str:
    """
    Remove extra whitespace from text.

    Args:
    ----
        text: The input text to clean.

    Returns:
    -------
        str: The cleaned text with normalized whitespace.

    """
    cleaned = re.sub(r"\s+", " ", text)
    return cleaned.strip()


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "clean",
]
