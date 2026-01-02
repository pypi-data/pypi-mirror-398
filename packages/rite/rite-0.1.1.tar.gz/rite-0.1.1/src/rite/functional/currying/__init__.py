# =============================================================================
# Docstring
# =============================================================================

"""
Currying Module
===============

Function currying and uncurrying utilities.

This submodule provides utilities for transforming functions
between curried and uncurried forms.

Examples
--------
>>> from rite.functional.currying import (
...     currying_curry,
...     currying_uncurry
... )
>>> def add(a, b, c):
...     return a + b + c
>>> curried = currying_curry(add)
>>> curried(1)(2)(3)
6

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .currying_curry import currying_curry
from .currying_uncurry import currying_uncurry

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "currying_curry",
    "currying_uncurry",
]
