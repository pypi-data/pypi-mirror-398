# =============================================================================
# Docstring
# =============================================================================

"""
Rainbow Case Converter
======================

Assign color codes to letters.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def to_rainbow_case(text: str) -> str:
    """
    Assigns a different color code to each letter.

    Note: Actual color cannot be represented in plain text; using symbolic
    representation.

    Args:
        text: The text to convert

    Returns:
        The text with symbolic color codes

    Example:
        >>> to_rainbow_case("Hello")
        '🟥H🟧e🟨l🟩l🟦o'
    """
    colors = ["🟥", "🟧", "🟨", "🟩", "🟦", "🟪"]
    return "".join(
        f"{colors[i % len(colors)]}{char}" for i, char in enumerate(text)
    )


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_rainbow_case",
]
