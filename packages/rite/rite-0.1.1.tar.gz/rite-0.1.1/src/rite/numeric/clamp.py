# =============================================================================
# Docstring
# =============================================================================

"""
Clamp Function
==============

Clamp a value between minimum and maximum bounds.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def clamp(
    val: float | None,
    lo: float,
    hi: float,
) -> float | None:
    """
    Clamp a value between a lower and upper bound.

    Args:
        val: Value to clamp (or None)
        lo: Lower bound
        hi: Upper bound

    Returns:
        Clamped value or None if input is None

    Example:
        >>> clamp(5, 0, 10)
        5
        >>> clamp(-5, 0, 10)
        0
        >>> clamp(None, 0, 10)
        None
    """
    if val is None:
        return None

    return max(lo, min(hi, val))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "clamp",
]
