# =============================================================================
# Docstring
# =============================================================================

"""
Length Unit Conversion
======================

Convert between meters, feet, inches, miles, and kilometers.

Examples
--------
>>> from rite.conversion.units import units_meters_to_feet
>>> units_meters_to_feet(1)
3.28084
>>> units_meters_to_feet(10)
32.8084

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def units_meters_to_feet(meters: float) -> float:
    """
    Convert meters to feet.

    Args:
        meters: Length in meters.

    Returns:
        Length in feet.

    Examples:
        >>> units_meters_to_feet(1)
        3.28084
        >>> units_meters_to_feet(10)
        32.8084
    """
    return meters * 3.28084


def units_feet_to_meters(feet: float) -> float:
    """
    Convert feet to meters.

    Args:
        feet: Length in feet.

    Returns:
        Length in meters.

    Examples:
        >>> round(units_feet_to_meters(3.28084), 2)
        1.0
        >>> round(units_feet_to_meters(10), 2)
        3.05
    """
    return feet / 3.28084


def units_meters_to_inches(meters: float) -> float:
    """
    Convert meters to inches.

    Args:
        meters: Length in meters.

    Returns:
        Length in inches.

    Examples:
        >>> round(units_meters_to_inches(1), 2)
        39.37
        >>> round(units_meters_to_inches(0.1), 2)
        3.94
    """
    return meters * 39.3701


def units_inches_to_meters(inches: float) -> float:
    """
    Convert inches to meters.

    Args:
        inches: Length in inches.

    Returns:
        Length in meters.

    Examples:
        >>> round(units_inches_to_meters(39.3701), 2)
        1.0
        >>> round(units_inches_to_meters(10), 2)
        0.25
    """
    return inches / 39.3701


def units_meters_to_kilometers(meters: float) -> float:
    """
    Convert meters to kilometers.

    Args:
        meters: Length in meters.

    Returns:
        Length in kilometers.

    Examples:
        >>> units_meters_to_kilometers(1000)
        1.0
        >>> units_meters_to_kilometers(500)
        0.5
    """
    return meters / 1000


def units_kilometers_to_meters(kilometers: float) -> float:
    """
    Convert kilometers to meters.

    Args:
        kilometers: Length in kilometers.

    Returns:
        Length in meters.

    Examples:
        >>> units_kilometers_to_meters(1)
        1000.0
        >>> units_kilometers_to_meters(0.5)
        500.0
    """
    return kilometers * 1000


def units_meters_to_miles(meters: float) -> float:
    """
    Convert meters to miles.

    Args:
        meters: Length in meters.

    Returns:
        Length in miles.

    Examples:
        >>> round(units_meters_to_miles(1609.34), 2)
        1.0
        >>> round(units_meters_to_miles(1000), 2)
        0.62
    """
    return meters / 1609.34


def units_miles_to_meters(miles: float) -> float:
    """
    Convert miles to meters.

    Args:
        miles: Length in miles.

    Returns:
        Length in meters.

    Examples:
        >>> round(units_miles_to_meters(1), 2)
        1609.34
        >>> round(units_miles_to_meters(10), 2)
        16093.4
    """
    return miles * 1609.34


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "units_meters_to_feet",
    "units_feet_to_meters",
    "units_meters_to_inches",
    "units_inches_to_meters",
    "units_meters_to_kilometers",
    "units_kilometers_to_meters",
    "units_meters_to_miles",
    "units_miles_to_meters",
]
