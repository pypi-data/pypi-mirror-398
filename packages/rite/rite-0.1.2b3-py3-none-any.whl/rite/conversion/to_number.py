# =============================================================================
# Docstring
# =============================================================================

"""
Number Conversion
=================

Parse a number from strings including those with units or suffixes like
'20 m', '45.5 %', '100/ha'.

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
    r"^\s*([-+]?\d*\.?\d+)\s*(?:[a-zA-Z%/]*?)\s*$",
)


# =============================================================================
# Functions
# =============================================================================


def to_number(x: Any) -> float | None:
    """
    Parse a number from messy strings like '20 m', '45.5 %', '100/ha'.

    Args:
        x: Value to convert (number, string, or None)

    Returns:
        Float representation or None if parsing fails

    Example:
        >>> to_number("45.5 %")
        45.5
        >>> to_number(100)
        100.0
        >>> to_number("invalid")
        None
    """

    if x is None:
        return None

    if isinstance(x, (int, float)):
        return float(x)

    m = _number_pat.match(str(x))

    return float(m.group(1)) if m else None


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_number",
]
