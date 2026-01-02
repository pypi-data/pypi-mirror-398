# =============================================================================
# Docstring
# =============================================================================

"""
Temperature Unit Conversion
===========================

Convert between Celsius, Fahrenheit, and Kelvin.

Examples
--------
>>> from rite.conversion.units import units_celsius_to_fahrenheit
>>> units_celsius_to_fahrenheit(0)
32.0
>>> units_celsius_to_fahrenheit(100)
212.0

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def units_celsius_to_fahrenheit(celsius: float) -> float:
    """
    Convert Celsius to Fahrenheit.

    Args:
        celsius: Temperature in Celsius.

    Returns:
        Temperature in Fahrenheit.

    Examples:
        >>> units_celsius_to_fahrenheit(0)
        32.0
        >>> units_celsius_to_fahrenheit(100)
        212.0
        >>> units_celsius_to_fahrenheit(-40)
        -40.0
    """
    return (celsius * 9 / 5) + 32


def units_fahrenheit_to_celsius(fahrenheit: float) -> float:
    """
    Convert Fahrenheit to Celsius.

    Args:
        fahrenheit: Temperature in Fahrenheit.

    Returns:
        Temperature in Celsius.

    Examples:
        >>> units_fahrenheit_to_celsius(32)
        0.0
        >>> units_fahrenheit_to_celsius(212)
        100.0
        >>> units_fahrenheit_to_celsius(-40)
        -40.0
    """
    return (fahrenheit - 32) * 5 / 9


def units_celsius_to_kelvin(celsius: float) -> float:
    """
    Convert Celsius to Kelvin.

    Args:
        celsius: Temperature in Celsius.

    Returns:
        Temperature in Kelvin.

    Examples:
        >>> units_celsius_to_kelvin(0)
        273.15
        >>> units_celsius_to_kelvin(100)
        373.15
        >>> units_celsius_to_kelvin(-273.15)
        0.0
    """
    return celsius + 273.15


def units_kelvin_to_celsius(kelvin: float) -> float:
    """
    Convert Kelvin to Celsius.

    Args:
        kelvin: Temperature in Kelvin.

    Returns:
        Temperature in Celsius.

    Examples:
        >>> units_kelvin_to_celsius(273.15)
        0.0
        >>> units_kelvin_to_celsius(373.15)
        100.0
        >>> units_kelvin_to_celsius(0)
        -273.15
    """
    return kelvin - 273.15


def units_fahrenheit_to_kelvin(fahrenheit: float) -> float:
    """
    Convert Fahrenheit to Kelvin.

    Args:
        fahrenheit: Temperature in Fahrenheit.

    Returns:
        Temperature in Kelvin.

    Examples:
        >>> units_fahrenheit_to_kelvin(32)
        273.15
        >>> units_fahrenheit_to_kelvin(212)
        373.15
    """
    return units_celsius_to_kelvin(units_fahrenheit_to_celsius(fahrenheit))


def units_kelvin_to_fahrenheit(kelvin: float) -> float:
    """
    Convert Kelvin to Fahrenheit.

    Args:
        kelvin: Temperature in Kelvin.

    Returns:
        Temperature in Fahrenheit.

    Examples:
        >>> units_kelvin_to_fahrenheit(273.15)
        32.0
        >>> units_kelvin_to_fahrenheit(373.15)
        212.0
    """
    return units_celsius_to_fahrenheit(units_kelvin_to_celsius(kelvin))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "units_celsius_to_fahrenheit",
    "units_fahrenheit_to_celsius",
    "units_celsius_to_kelvin",
    "units_kelvin_to_celsius",
    "units_fahrenheit_to_kelvin",
    "units_kelvin_to_fahrenheit",
]
