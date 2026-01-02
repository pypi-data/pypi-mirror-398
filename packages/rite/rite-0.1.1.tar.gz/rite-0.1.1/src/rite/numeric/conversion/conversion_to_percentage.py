# =============================================================================
# Docstring
# =============================================================================

"""
Percentage Converter
====================

Convert decimal to percentage.

Examples
--------
>>> from rite.numeric.conversion import conversion_to_percentage
>>> conversion_to_percentage(0.25)
25.0

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def conversion_to_percentage(
    value: float, decimals: int | None = None
) -> float:
    """
    Convert decimal to percentage.

    Args:
        value: Decimal value (0.0 to 1.0).
        decimals: Number of decimal places to round to.

    Returns:
        Percentage value (0.0 to 100.0).

    Examples:
        >>> conversion_to_percentage(0.25)
        25.0
        >>> conversion_to_percentage(0.5)
        50.0
        >>> conversion_to_percentage(0.12345, decimals=2)
        12.35

    Notes:
        Multiplies by 100.
        Optional rounding to specified decimals.
    """
    result = value * 100
    if decimals is not None:
        result = round(result, decimals)
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["conversion_to_percentage"]
