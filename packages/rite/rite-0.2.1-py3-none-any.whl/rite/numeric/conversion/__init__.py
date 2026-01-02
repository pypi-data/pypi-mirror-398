# =============================================================================
# Docstring
# =============================================================================

"""
Conversion Module
=================

Numeric conversion utilities.

This submodule provides utilities for converting between different
numeric representations like decimal, percentage, etc.

Examples
--------
>>> from rite.numeric.conversion import (
...     conversion_to_decimal,
...     conversion_to_percentage
... )
>>> conversion_to_decimal("3.14")
Decimal('3.14')
>>> conversion_to_percentage(0.25)
25.0

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .conversion_from_percentage import conversion_from_percentage
from .conversion_to_decimal import conversion_to_decimal
from .conversion_to_percentage import conversion_to_percentage

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "conversion_to_decimal",
    "conversion_to_percentage",
    "conversion_from_percentage",
]
