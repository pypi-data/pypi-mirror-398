# =============================================================================
# Docstring
# =============================================================================

"""
Percentage Conversion
=====================

Convert values to percentage (0-100 range).

Examples
--------
>>> from rite.conversion.types import types_to_percentage
>>> types_to_percentage(0.35)
35.0
>>> types_to_percentage("35%")
35.0

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

_percent_pat = re.compile(r"^\s*(?P<num>[-+]?\d*\.?\d+)\s*%?\s*$")

# =============================================================================
# Functions
# =============================================================================


def types_to_percentage(
    x: Any,
    default: float | None = None,
    clamp: bool = True,
) -> float | None:
    """
    Convert value to percentage (0-100).

    Accepts 35, "35", "35%", 0.35 (interpreted as 35% if 0<=x<=1).

    Args:
        x: Value to convert (number, string, or None).
        default: Default value if conversion fails.
        clamp: If True, clamp result to 0-100 range.

    Returns:
        Percentage value (0.0-100.0) or default if conversion fails.

    Examples:
        >>> types_to_percentage(0.35)
        35.0
        >>> types_to_percentage("35%")
        35.0
        >>> types_to_percentage(150)
        100.0
        >>> types_to_percentage(150, clamp=False)
        150.0
        >>> types_to_percentage("invalid")

        >>> types_to_percentage("invalid", 0.0)
        0.0
    """
    if x is None:
        return default

    if isinstance(x, (int, float)):
        val = float(x)
        # If 0..1, treat as fraction
        if 0 <= val <= 1.0:
            val = val * 100.0
    elif isinstance(x, str):
        match = _percent_pat.match(x)
        if not match:
            return default
        val = float(match.group("num"))
        # If 0..1 as string, treat as fraction
        if 0 <= val <= 1.0:
            val = val * 100.0
    else:
        return default

    if clamp:
        return max(0.0, min(100.0, val))

    return val


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_to_percentage"]
