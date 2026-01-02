# =============================================================================
# Docstring
# =============================================================================

"""
Negate Predicate
================

Negate boolean result of predicate function.

Examples
--------
>>> from rite.functional.predicates import predicates_negate
>>> is_even = lambda x: x % 2 == 0
>>> is_odd = predicates_negate(is_even)
>>> is_odd(3)
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Callable
from functools import wraps
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def predicates_negate(
    predicate: Callable[..., bool],
) -> Callable[..., bool]:
    """
    Negate predicate function result.

    Args:
        predicate: Function returning boolean.

    Returns:
        Negated predicate function.

    Examples:
        >>> is_positive = lambda x: x > 0
        >>> is_not_positive = predicates_negate(is_positive)
        >>> is_not_positive(-5)
        True
        >>> is_not_positive(5)
        False

    Notes:
        Equivalent to: lambda *args: not predicate(*args).
    """

    @wraps(predicate)
    def negated(*args: Any, **kwargs: Any) -> bool:
        return not predicate(*args, **kwargs)

    return negated


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["predicates_negate"]
