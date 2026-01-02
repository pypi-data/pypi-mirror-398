# =============================================================================
# Docstring
# =============================================================================

"""
Decimal to Percentage Converter
================================

Convert percentage to decimal.

Examples
--------
>>> from rite.numeric.conversion import conversion_from_percentage
>>> conversion_from_percentage(25)
0.25

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def conversion_from_percentage(value: float) -> float:
    """
    Convert percentage to decimal.

    Args:
        value: Percentage value (0.0 to 100.0).

    Returns:
        Decimal value (0.0 to 1.0).

    Examples:
        >>> conversion_from_percentage(25)
        0.25
        >>> conversion_from_percentage(50)
        0.5
        >>> conversion_from_percentage(12.5)
        0.125

    Notes:
        Divides by 100.
    """
    return value / 100


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["conversion_from_percentage"]
