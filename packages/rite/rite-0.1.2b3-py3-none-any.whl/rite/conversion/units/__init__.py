# =============================================================================
# Docstring
# =============================================================================

"""
Unit Conversion Utilities
==========================

Physical unit conversions.

This submodule provides utilities for converting between different
units of measurement: temperature, length, weight, time, etc.

Examples
--------
>>> from rite.conversion.units import (
...     units_celsius_to_fahrenheit,
...     units_meters_to_feet,
...     units_grams_to_pounds
... )
>>> units_celsius_to_fahrenheit(0)
32.0
>>> units_meters_to_feet(1)
3.28084
>>> round(units_grams_to_pounds(453.592), 2)
1.0

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .units_length import (
    units_feet_to_meters,
    units_inches_to_meters,
    units_kilometers_to_meters,
    units_meters_to_feet,
    units_meters_to_inches,
    units_meters_to_kilometers,
    units_meters_to_miles,
    units_miles_to_meters,
)
from .units_temperature import (
    units_celsius_to_fahrenheit,
    units_celsius_to_kelvin,
    units_fahrenheit_to_celsius,
    units_fahrenheit_to_kelvin,
    units_kelvin_to_celsius,
    units_kelvin_to_fahrenheit,
)
from .units_time import (
    units_days_to_seconds,
    units_hours_to_minutes,
    units_hours_to_seconds,
    units_minutes_to_hours,
    units_minutes_to_seconds,
    units_seconds_to_days,
    units_seconds_to_hours,
    units_seconds_to_minutes,
)
from .units_weight import (
    units_grams_to_kilograms,
    units_grams_to_ounces,
    units_grams_to_pounds,
    units_kilograms_to_grams,
    units_ounces_to_grams,
    units_pounds_to_grams,
)

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # Temperature
    "units_celsius_to_fahrenheit",
    "units_fahrenheit_to_celsius",
    "units_celsius_to_kelvin",
    "units_kelvin_to_celsius",
    "units_fahrenheit_to_kelvin",
    "units_kelvin_to_fahrenheit",
    # Length
    "units_meters_to_feet",
    "units_feet_to_meters",
    "units_meters_to_inches",
    "units_inches_to_meters",
    "units_meters_to_kilometers",
    "units_kilometers_to_meters",
    "units_meters_to_miles",
    "units_miles_to_meters",
    # Weight
    "units_grams_to_kilograms",
    "units_kilograms_to_grams",
    "units_grams_to_pounds",
    "units_pounds_to_grams",
    "units_grams_to_ounces",
    "units_ounces_to_grams",
    # Time
    "units_seconds_to_minutes",
    "units_minutes_to_seconds",
    "units_seconds_to_hours",
    "units_hours_to_seconds",
    "units_seconds_to_days",
    "units_days_to_seconds",
    "units_minutes_to_hours",
    "units_hours_to_minutes",
]
