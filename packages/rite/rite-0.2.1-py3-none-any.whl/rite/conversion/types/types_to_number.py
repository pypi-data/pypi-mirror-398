# =============================================================================
# Docstring
# =============================================================================

"""
Number Conversion
=================

Parse numbers from strings including those with units or suffixes.

Examples
--------
>>> from rite.conversion.types import types_to_number
>>> types_to_number("45.5 %")
45.5
>>> types_to_number("20 m")
20.0

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

_number_pat = re.compile(
    r"^\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*[a-zA-Z%/]*?\s*$",
)

# =============================================================================
# Functions
# =============================================================================


def types_to_number(x: Any, default: float | None = None) -> float | None:
    """
    Parse a number from strings like '20 m', '45.5 %', '100/ha'.

    Args:
        x: Value to convert (number, string, or None).
        default: Default value if parsing fails.

    Returns:
        Float representation or default/None if parsing fails.

    Examples:
        >>> types_to_number("45.5 %")
        45.5
        >>> types_to_number(100)
        100.0
        >>> types_to_number("1.5e3")
        1500.0
        >>> types_to_number("invalid")

        >>> types_to_number("invalid", 0.0)
        0.0
        >>> types_to_number("20 meters")
        20.0
    """
    if x is None:
        return default

    if isinstance(x, (int, float)):
        return float(x)

    if isinstance(x, str):
        match = _number_pat.match(x)
        if match:
            return float(match.group(1))

    return default


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_to_number"]
