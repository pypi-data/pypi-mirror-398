# =============================================================================
# Docstring
# =============================================================================

"""
Float Conversion
================

Convert values to floating-point representation.

Examples
--------
>>> from rite.conversion.types import types_to_float
>>> types_to_float("3.14")
3.14
>>> types_to_float(42)
42.0
>>> types_to_float("invalid")

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

_float_pat = re.compile(r"^\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*$")

# =============================================================================
# Functions
# =============================================================================


def types_to_float(x: Any, default: float | None = None) -> float | None:
    """
    Convert a value to a float.

    Args:
        x: Value to convert (string, number, bool, or None).
        default: Default value if conversion fails.

    Returns:
        Float representation or default/None if conversion fails.

    Examples:
        >>> types_to_float("3.14")
        3.14
        >>> types_to_float(42)
        42.0
        >>> types_to_float("1.5e3")
        1500.0
        >>> types_to_float("invalid")

        >>> types_to_float("invalid", 0.0)
        0.0
        >>> types_to_float(True)
        1.0
    """
    if x is None:
        return default

    if isinstance(x, bool):
        return float(x)

    if isinstance(x, (int, float)):
        return float(x)

    if isinstance(x, str):
        # Try direct conversion
        try:
            return float(x)
        except (ValueError, TypeError):
            pass

        # Try pattern match for strings with whitespace
        match = _float_pat.match(x)
        if match:
            return float(match.group(1))

    return default


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_to_float"]
