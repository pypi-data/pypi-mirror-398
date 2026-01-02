# =============================================================================
# Docstring
# =============================================================================

"""
Weight Unit Conversion
======================

Convert between grams, kilograms, pounds, and ounces.

Examples
--------
>>> from rite.conversion.units import units_grams_to_kilograms
>>> units_grams_to_kilograms(1000)
1.0
>>> units_grams_to_kilograms(500)
0.5

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def units_grams_to_kilograms(grams: float) -> float:
    """
    Convert grams to kilograms.

    Args:
        grams: Weight in grams.

    Returns:
        Weight in kilograms.

    Examples:
        >>> units_grams_to_kilograms(1000)
        1.0
        >>> units_grams_to_kilograms(500)
        0.5
    """
    return grams / 1000


def units_kilograms_to_grams(kilograms: float) -> float:
    """
    Convert kilograms to grams.

    Args:
        kilograms: Weight in kilograms.

    Returns:
        Weight in grams.

    Examples:
        >>> units_kilograms_to_grams(1)
        1000.0
        >>> units_kilograms_to_grams(0.5)
        500.0
    """
    return kilograms * 1000


def units_grams_to_pounds(grams: float) -> float:
    """
    Convert grams to pounds.

    Args:
        grams: Weight in grams.

    Returns:
        Weight in pounds.

    Examples:
        >>> round(units_grams_to_pounds(453.592), 2)
        1.0
        >>> round(units_grams_to_pounds(1000), 2)
        2.2
    """
    return grams / 453.592


def units_pounds_to_grams(pounds: float) -> float:
    """
    Convert pounds to grams.

    Args:
        pounds: Weight in pounds.

    Returns:
        Weight in grams.

    Examples:
        >>> round(units_pounds_to_grams(1), 3)
        453.592
        >>> round(units_pounds_to_grams(2.2), 2)
        997.9
    """
    return pounds * 453.592


def units_grams_to_ounces(grams: float) -> float:
    """
    Convert grams to ounces.

    Args:
        grams: Weight in grams.

    Returns:
        Weight in ounces.

    Examples:
        >>> round(units_grams_to_ounces(28.3495), 2)
        1.0
        >>> round(units_grams_to_ounces(100), 2)
        3.53
    """
    return grams / 28.3495


def units_ounces_to_grams(ounces: float) -> float:
    """
    Convert ounces to grams.

    Args:
        ounces: Weight in ounces.

    Returns:
        Weight in grams.

    Examples:
        >>> round(units_ounces_to_grams(1), 4)
        28.3495
        >>> round(units_ounces_to_grams(10), 2)
        283.5
    """
    return ounces * 28.3495


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "units_grams_to_kilograms",
    "units_kilograms_to_grams",
    "units_grams_to_pounds",
    "units_pounds_to_grams",
    "units_grams_to_ounces",
    "units_ounces_to_grams",
]
