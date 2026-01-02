# =============================================================================
# Docstring
# =============================================================================

"""
Numeric Module
==============

Comprehensive numeric operations and utilities.

This module provides utilities organized into semantic submodules:
- math: Basic math operations (clamp, abs, sign, power)
- conversion: Type conversions (decimal, percentage)
- coordinates: Geographic coordinate conversions (DMS)
- rounding: Rounding operations (round, floor, ceil, trunc)
- statistics: Statistical calculations (mean, median, sum)
- range: Range operations (normalize, scale, in_range)

Examples
--------
>>> from rite.numeric import math_clamp, statistics_mean
>>> math_clamp(5, 0, 10)
5
>>> statistics_mean([1, 2, 3, 4, 5])
3.0

Legacy Functions
----------------
>>> from rite.numeric import clamp
>>> clamp(5, 0, 10)
5

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
# Import | Legacy
from .clamp import clamp

# Import | Conversion Utilities
from .conversion import (
    conversion_from_percentage,
    conversion_to_decimal,
    conversion_to_percentage,
)

# Import | Coordinate Utilities
from .coordinates import (
    coordinates_from_degree_minute_second,
    coordinates_to_degree_minute,
    coordinates_to_degree_minute_second,
)
from .float_to_degree_minute import float_to_degree_minute
from .float_to_degree_minute_second import float_to_degree_minute_second

# Import | Math Utilities
from .math import math_abs, math_clamp, math_pow, math_sign

# Import | Range Utilities
from .range import range_in_range, range_normalize, range_scale

# Import | Rounding Utilities
from .rounding import (
    rounding_ceil,
    rounding_floor,
    rounding_round,
    rounding_trunc,
)

# Import | Statistics Utilities
from .statistics import (
    statistics_max,
    statistics_mean,
    statistics_median,
    statistics_min,
    statistics_sum,
)
from .value_to_decimal import value_to_decimal

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # Legacy Functions
    "clamp",
    "float_to_degree_minute",
    "float_to_degree_minute_second",
    "value_to_decimal",
    # Math Utilities
    "math_clamp",
    "math_abs",
    "math_sign",
    "math_pow",
    # Conversion Utilities
    "conversion_to_decimal",
    "conversion_to_percentage",
    "conversion_from_percentage",
    # Coordinate Utilities
    "coordinates_to_degree_minute",
    "coordinates_to_degree_minute_second",
    "coordinates_from_degree_minute_second",
    # Rounding Utilities
    "rounding_round",
    "rounding_floor",
    "rounding_ceil",
    "rounding_trunc",
    # Statistics Utilities
    "statistics_mean",
    "statistics_median",
    "statistics_sum",
    "statistics_min",
    "statistics_max",
    # Range Utilities
    "range_in_range",
    "range_normalize",
    "range_scale",
]
