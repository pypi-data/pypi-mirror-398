# =============================================================================
# Docstring
# =============================================================================

"""
Rounding Module
===============

Numeric rounding utilities.

This submodule provides utilities for rounding operations like
round, floor, ceil, and truncate.

Examples
--------
>>> from rite.numeric.rounding import (
...     rounding_round,
...     rounding_floor
... )
>>> rounding_round(3.14159, 2)
3.14
>>> rounding_floor(3.9)
3

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .rounding_ceil import rounding_ceil
from .rounding_floor import rounding_floor
from .rounding_round import rounding_round
from .rounding_trunc import rounding_trunc

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "rounding_round",
    "rounding_floor",
    "rounding_ceil",
    "rounding_trunc",
]
