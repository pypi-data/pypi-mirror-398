# =============================================================================
# Docstring
# =============================================================================

"""
Rite - String - String to Int Converter Module
==============================================

Provides functionality to convert strings to integer values.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def convert_string_to_int(val: str) -> int | None:
    """
    Convert a string representation of an integer value to an integer.
    """

    val = (val or "").strip()

    if val == "":
        return None

    try:
        return int(val)

    except ValueError:
        return None


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "convert_string_to_int",
]
