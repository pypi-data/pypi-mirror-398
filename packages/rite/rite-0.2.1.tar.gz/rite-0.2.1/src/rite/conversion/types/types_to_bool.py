# =============================================================================
# Docstring
# =============================================================================

"""
Boolean Conversion
==================

Convert values to boolean representation.

Examples
--------
>>> from rite.conversion.types import types_to_bool
>>> types_to_bool("yes")
True
>>> types_to_bool("no")
False
>>> types_to_bool(1)
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import Any

# =============================================================================
# Constants
# =============================================================================

TRUTHY = {"true", "t", "yes", "y", "1", "on"}
FALSY = {"false", "f", "no", "n", "0", "off", ""}

# =============================================================================
# Functions
# =============================================================================


def types_to_bool(x: Any, default: bool | None = None) -> bool | None:
    """
    Convert a value to a boolean.

    Args:
        x: Value to convert (string, number, bool, or None).
        default: Default value if conversion fails.

    Returns:
        Boolean representation or default/None if conversion fails.

    Examples:
        >>> types_to_bool("yes")
        True
        >>> types_to_bool("no")
        False
        >>> types_to_bool(1)
        True
        >>> types_to_bool(0)
        False
        >>> types_to_bool(None)

        >>> types_to_bool(None, False)
        False
        >>> types_to_bool("invalid")

        >>> types_to_bool("invalid", True)
        True
    """
    if x is None:
        return default

    if isinstance(x, bool):
        return x

    if isinstance(x, (int, float)):
        return bool(x)

    if isinstance(x, str):
        normalized = x.strip().lower()

        if normalized in TRUTHY:
            return True

        if normalized in FALSY:
            return False

    return default


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_to_bool", "TRUTHY", "FALSY"]
