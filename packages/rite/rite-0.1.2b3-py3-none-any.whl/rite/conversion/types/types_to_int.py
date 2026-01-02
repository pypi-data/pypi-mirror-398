# =============================================================================
# Docstring
# =============================================================================

"""
Integer Conversion
==================

Convert values to integer representation.

Examples
--------
>>> from rite.conversion.types import types_to_int
>>> types_to_int("42")
42
>>> types_to_int(3.14)
3
>>> types_to_int("invalid")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import re
from typing import Any

# =============================================================================
# Pattern
# =============================================================================

_int_pat = re.compile(r"^\s*([-+]?\d+)\s*$")

# =============================================================================
# Functions
# =============================================================================


def types_to_int(x: Any, default: int | None = None) -> int | None:
    """
    Convert a value to an integer.

    Args:
        x: Value to convert (string, number, bool, or None).
        default: Default value if conversion fails.

    Returns:
        Integer representation or default/None if conversion fails.

    Examples:
        >>> types_to_int("42")
        42
        >>> types_to_int(3.14)
        3
        >>> types_to_int("invalid")

        >>> types_to_int("invalid", 0)
        0
        >>> types_to_int(True)
        1
    """
    if x is None:
        return default

    if isinstance(x, bool):
        return int(x)

    if isinstance(x, int):
        return x

    if isinstance(x, float):
        return int(x)

    if isinstance(x, str):
        # Try direct conversion
        try:
            return int(x)
        except (ValueError, TypeError):
            pass

        # Try pattern match for strings with whitespace
        match = _int_pat.match(x)
        if match:
            return int(match.group(1))

    return default


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_to_int"]
