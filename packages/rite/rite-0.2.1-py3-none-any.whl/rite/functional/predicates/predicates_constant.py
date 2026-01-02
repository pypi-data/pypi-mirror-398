# =============================================================================
# Docstring
# =============================================================================

"""
Constant Function
=================

Returns constant value regardless of input.

Examples
--------
>>> from rite.functional.predicates import predicates_constant
>>> always_42 = predicates_constant(42)
>>> always_42("anything")
42

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Callable
from typing import Any, TypeVar

# =============================================================================
# Types
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def predicates_constant(value: T) -> Callable[..., T]:
    """
    Create function that always returns same value.

    Args:
        value: Constant value to return.

    Returns:
        Function that returns constant.

    Examples:
        >>> always_true = predicates_constant(True)
        >>> always_true()
        True
        >>> always_true(1, 2, 3)
        True

    Notes:
        Useful for default callbacks or testing.
    """

    def constant(*args: Any, **kwargs: Any) -> T:
        return value

    return constant


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["predicates_constant"]
