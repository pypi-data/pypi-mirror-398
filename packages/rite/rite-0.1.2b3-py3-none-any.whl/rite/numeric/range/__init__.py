# =============================================================================
# Docstring
# =============================================================================

"""
Range Module
============

Range and normalization utilities.

This submodule provides utilities for range operations like
checking if values are in range, normalizing, and scaling.

Examples
--------
>>> from rite.numeric.range import (
...     range_in_range,
...     range_normalize
... )
>>> range_in_range(5, 0, 10)
True
>>> range_normalize(5, 0, 10)
0.5

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .range_in_range import range_in_range
from .range_normalize import range_normalize
from .range_scale import range_scale

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "range_in_range",
    "range_normalize",
    "range_scale",
]
