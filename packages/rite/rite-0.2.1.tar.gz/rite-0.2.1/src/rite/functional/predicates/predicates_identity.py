# =============================================================================
# Docstring
# =============================================================================

"""
Identity Predicate
==================

Returns input unchanged.

Examples
--------
>>> from rite.functional.predicates import predicates_identity
>>> predicates_identity(42)
42

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import TypeVar

# =============================================================================
# Types
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def predicates_identity(value: T) -> T:
    """
    Return input value unchanged.

    Args:
        value: Any value.

    Returns:
        The same value.

    Examples:
        >>> predicates_identity("hello")
        'hello'
        >>> predicates_identity([1, 2, 3])
        [1, 2, 3]

    Notes:
        Useful for filtering or as default function.
    """
    return value


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["predicates_identity"]
