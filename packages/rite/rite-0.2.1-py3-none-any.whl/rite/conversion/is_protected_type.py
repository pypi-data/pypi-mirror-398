# =============================================================================
# Docstring
# =============================================================================

"""
Protected Type Check Module
===========================

Utilities for identifying protected scalar types.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import datetime
from decimal import Decimal
from types import NoneType
from typing import Any

# =============================================================================
# Constants
# =============================================================================

PROTECTED_TYPES = (
    NoneType,
    int,
    float,
    Decimal,
    datetime.datetime,
    datetime.date,
    datetime.time,
)


# =============================================================================
# Functions
# =============================================================================


def is_protected_type(obj: Any) -> bool:
    """
    Check if an object is a protected scalar type.

    Protected types are simple scalar values that should not be converted
    to strings or bytes when strings_only mode is enabled.

    Args:
    ----
        obj: Object to check.

    Returns:
    -------
        bool: True if obj is a protected type.

    Example:
    -------
        >>> is_protected_type(42)
        True
        >>> is_protected_type(None)
        True
        >>> is_protected_type("hello")
        False

    """
    return isinstance(obj, PROTECTED_TYPES)


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "is_protected_type",
    "PROTECTED_TYPES",
]
