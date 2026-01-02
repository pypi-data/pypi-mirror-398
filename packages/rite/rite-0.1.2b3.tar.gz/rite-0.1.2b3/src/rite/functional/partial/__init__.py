# =============================================================================
# Docstring
# =============================================================================

"""
Partial Module
==============

Partial function application utilities.

This submodule provides utilities for partial application
of function arguments from left or right.

Examples
--------
>>> from rite.functional.partial import (
...     partial_apply,
...     partial_right
... )
>>> def power(base, exp):
...     return base ** exp
>>> square = partial_apply(power, exponent=2)
>>> square(5)
25

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .partial_apply import partial_apply
from .partial_right import partial_right

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "partial_apply",
    "partial_right",
]
