# =============================================================================
# Docstring
# =============================================================================

"""
Functional Programming Module
==============================

Comprehensive functional programming utilities.

This module provides utilities for decorators, function composition,
currying, partial application, memoization, and predicates.

Submodules
----------
- decorators: Debounce, throttle, once, deprecated decorators
- composition: Function composition, piping, chaining
- currying: Curry and uncurry functions
- partial: Partial application from left and right
- memoization: Result caching with various strategies
- predicates: Identity, constant, negate predicates

Examples
--------
Decorators:
    >>> from rite.functional import decorators_throttle
    >>> @decorators_throttle(1.0)
    ... def api_call():
    ...     return "response"

Composition:
    >>> from rite.functional import composition_pipe
    >>> f = composition_pipe(lambda x: x + 1, lambda x: x * 2)
    >>> f(3)
    8

Currying:
    >>> from rite.functional import currying_curry
    >>> def add(a, b, c):
    ...     return a + b + c
    >>> curried = currying_curry(add)
    >>> curried(1)(2)(3)
    6

Memoization:
    >>> from rite.functional import memoization_memoize
    >>> @memoization_memoize()
    ... def fibonacci(n):
    ...     if n <= 1:
    ...         return n
    ...     return fibonacci(n-1) + fibonacci(n-2)

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .composition import (
    composition_chain,
    composition_compose,
    composition_pipe,
)
from .currying import currying_curry, currying_uncurry
from .decorators import (
    decorators_debounce,
    decorators_deprecated,
    decorators_once,
    decorators_throttle,
)
from .memoization import memoization_lru_cache, memoization_memoize
from .partial import partial_apply, partial_right
from .predicates import (
    predicates_constant,
    predicates_identity,
    predicates_negate,
)

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # Decorators
    "decorators_debounce",
    "decorators_throttle",
    "decorators_once",
    "decorators_deprecated",
    # Composition
    "composition_compose",
    "composition_pipe",
    "composition_chain",
    # Currying
    "currying_curry",
    "currying_uncurry",
    # Partial
    "partial_apply",
    "partial_right",
    # Memoization
    "memoization_memoize",
    "memoization_lru_cache",
    # Predicates
    "predicates_identity",
    "predicates_constant",
    "predicates_negate",
]
