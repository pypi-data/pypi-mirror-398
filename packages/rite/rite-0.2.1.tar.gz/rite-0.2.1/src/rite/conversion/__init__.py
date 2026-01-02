# =============================================================================
# Docstring
# =============================================================================

"""
Conversion Module
=================

Comprehensive conversion utilities for types, formats, and units.

This module provides three main categories of conversions:

1. **Type Conversions** (types submodule)
   - Basic Python type conversions: int, float, str, bool, bytes
   - Collection conversions: list, dict, set, tuple
   - Number parsing and percentage conversions

2. **Format Conversions** (formats submodule)
   - JSON encoding/decoding
   - Base64 encoding/decoding
   - Hexadecimal encoding/decoding
   - URL encoding/decoding

3. **Unit Conversions** (units submodule)
   - Temperature: Celsius, Fahrenheit, Kelvin
   - Length: meters, feet, inches, miles, kilometers
   - Weight: grams, kilograms, pounds, ounces
   - Time: seconds, minutes, hours, days

Examples
--------
>>> from rite.conversion import (
...     types_to_bool,
...     formats_json_encode,
...     units_celsius_to_fahrenheit
... )
>>> types_to_bool("yes")
True
>>> formats_json_encode({"key": "value"})
'{"key": "value"}'
>>> units_celsius_to_fahrenheit(0)
32.0

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .formats import (
    formats_base64_decode,
    formats_base64_encode,
    formats_hex_decode,
    formats_hex_encode,
    formats_json_decode,
    formats_json_encode,
    formats_url_decode,
    formats_url_encode,
)
from .is_protected_type import is_protected_type, PROTECTED_TYPES
from .to_bool import to_bool
from .to_bytes import to_bytes
from .to_number import to_number
from .to_percentage import to_percentage
from .types import (
    FALSY,
    TRUTHY,
    types_to_bool,
    types_to_bytes,
    types_to_dict,
    types_to_float,
    types_to_int,
    types_to_list,
    types_to_number,
    types_to_percentage,
    types_to_set,
    types_to_str,
    types_to_tuple,
)
from .units import (
    units_celsius_to_fahrenheit,
    units_celsius_to_kelvin,
    units_days_to_seconds,
    units_fahrenheit_to_celsius,
    units_fahrenheit_to_kelvin,
    units_feet_to_meters,
    units_grams_to_kilograms,
    units_grams_to_ounces,
    units_grams_to_pounds,
    units_hours_to_minutes,
    units_hours_to_seconds,
    units_inches_to_meters,
    units_kelvin_to_celsius,
    units_kelvin_to_fahrenheit,
    units_kilograms_to_grams,
    units_kilometers_to_meters,
    units_meters_to_feet,
    units_meters_to_inches,
    units_meters_to_kilometers,
    units_meters_to_miles,
    units_miles_to_meters,
    units_minutes_to_hours,
    units_minutes_to_seconds,
    units_ounces_to_grams,
    units_pounds_to_grams,
    units_seconds_to_days,
    units_seconds_to_hours,
    units_seconds_to_minutes,
)

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # Legacy exports (backward compatibility)
    "to_bool",
    "to_number",
    "to_percentage",
    "to_bytes",
    "is_protected_type",
    "PROTECTED_TYPES",
    # Type conversions
    "types_to_bool",
    "types_to_bytes",
    "types_to_int",
    "types_to_float",
    "types_to_str",
    "types_to_number",
    "types_to_percentage",
    "types_to_list",
    "types_to_dict",
    "types_to_set",
    "types_to_tuple",
    "TRUTHY",
    "FALSY",
    # Format conversions
    "formats_json_encode",
    "formats_json_decode",
    "formats_base64_encode",
    "formats_base64_decode",
    "formats_hex_encode",
    "formats_hex_decode",
    "formats_url_encode",
    "formats_url_decode",
    # Unit conversions - Temperature
    "units_celsius_to_fahrenheit",
    "units_fahrenheit_to_celsius",
    "units_celsius_to_kelvin",
    "units_kelvin_to_celsius",
    "units_fahrenheit_to_kelvin",
    "units_kelvin_to_fahrenheit",
    # Unit conversions - Length
    "units_meters_to_feet",
    "units_feet_to_meters",
    "units_meters_to_inches",
    "units_inches_to_meters",
    "units_meters_to_kilometers",
    "units_kilometers_to_meters",
    "units_meters_to_miles",
    "units_miles_to_meters",
    # Unit conversions - Weight
    "units_grams_to_kilograms",
    "units_kilograms_to_grams",
    "units_grams_to_pounds",
    "units_pounds_to_grams",
    "units_grams_to_ounces",
    "units_ounces_to_grams",
    # Unit conversions - Time
    "units_seconds_to_minutes",
    "units_minutes_to_seconds",
    "units_seconds_to_hours",
    "units_hours_to_seconds",
    "units_seconds_to_days",
    "units_days_to_seconds",
    "units_minutes_to_hours",
    "units_hours_to_minutes",
]
