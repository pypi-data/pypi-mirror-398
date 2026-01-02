# =============================================================================
# Docstring
# =============================================================================

"""
Coordinates Module
==================

Geographic coordinate conversion utilities.

This submodule provides utilities for converting between decimal
degrees and degree-minute-second (DMS) formats.

Examples
--------
>>> from rite.numeric.coordinates import (
...     coordinates_to_degree_minute_second,
...     coordinates_from_degree_minute_second
... )
>>> coordinates_to_degree_minute_second(12.5)
(12, 30, 0.0)
>>> coordinates_from_degree_minute_second(12, 30, 0)
12.5

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .coordinates_from_degree_minute_second import (
    coordinates_from_degree_minute_second,
)
from .coordinates_to_degree_minute import coordinates_to_degree_minute
from .coordinates_to_degree_minute_second import (
    coordinates_to_degree_minute_second,
)

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "coordinates_to_degree_minute",
    "coordinates_to_degree_minute_second",
    "coordinates_from_degree_minute_second",
]
