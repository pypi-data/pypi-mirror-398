# =============================================================================
# Docstring
# =============================================================================

"""
Percentage Conversion
=====================

Accepts numbers, strings with %, or floats between 0-1 and converts to
percentage value (0-100).

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


def to_percentage(x: Any) -> float | None:
    """
    Convert value to percentage (0-100).

    Accepts 35, "35", "35%", 0.35 (interpreted as 35% if 0<=x<=1).

    Args:
        x: Value to convert (number, string, or None)

    Returns:
        Percentage value (0.0-100.0) or None if conversion fails

    Example:
        >>> to_percentage(0.35)
        35.0
        >>> to_percentage("35%")
        35.0
        >>> to_percentage(150)
        100.0

    """
    if x is None:
        return None
    if isinstance(x, (int, float)):
        val = float(x)
        if 0 <= val <= 1.0:
            val = val * 100.0
        return max(0.0, min(100.0, val))
    m = _percent_pat.match(str(x))
    if not m:
        return None
    val = float(m.group("num"))
    # If someone passes 0..1 as string, treat as fraction
    if 0 <= val <= 1.0:
        val = val * 100.0
    return max(0.0, min(100.0, val))
