# =============================================================================
# Docstring
# =============================================================================

"""
Rite - String - String to Boolean Converter Module
==================================================

Provides functionality to convert strings to boolean values.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def convert_string_to_bool(val: str | None) -> bool | None:
    """
    String to Boolean Converter
    ===========================

    Convert a string representation of a boolean value to a boolean.

    """

    if val is None:
        return None

    v: str = val.strip().lower()

    if v in {
        "t",
        "true",
        "1",
        "yes",
        "y",
        "ja",
        "oui",
        "si",
    }:
        return True

    if v in {
        "f",
        "false",
        "0",
        "no",
        "n",
        "nee",
        "nein",
        "non",
    }:
        return False

    return None


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "convert_string_to_bool",
]
