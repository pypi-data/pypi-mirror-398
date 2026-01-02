# =============================================================================
# Docstring
# =============================================================================

"""
Character Frequency Analysis
============================

Count character frequency in text.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections import Counter

# =============================================================================
# Functions
# =============================================================================


def char_frequency(text: str) -> dict[str, int]:
    """
    Count the frequency of each character in text.

    Args:
        text: Input text string

    Returns:
        Dictionary mapping characters to their frequency count

    Example:
        >>> char_frequency("hello")
        {'h': 1, 'e': 1, 'l': 2, 'o': 1}
    """
    return dict(Counter(text))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "char_frequency",
]
