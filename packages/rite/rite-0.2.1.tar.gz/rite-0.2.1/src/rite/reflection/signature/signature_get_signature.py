# =============================================================================
# Docstring
# =============================================================================

"""
Signature Inspector
===================

Get function or method signature.

Examples
--------
>>> from rite.reflection.signature import signature_get_signature
>>> def func(a: int, b: str = "default") -> str:
...     return f"{a}{b}"
>>> sig = signature_get_signature(func)
>>> str(sig)
"(a: int, b: str = 'default') -> str"

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import inspect
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def signature_get_signature(obj: Any) -> inspect.Signature:
    """
    Get function or method signature.

    Args:
        obj: Function, method, or class to inspect.

    Returns:
        Signature object.

    Examples:
        >>> def func(a: int, b: str = "default") -> str:
        ...     return f"{a}{b}"
        >>> sig = signature_get_signature(func)
        >>> len(sig.parameters)
        2

    Notes:
        Uses inspect.signature.
        Returns Signature object.
    """
    return inspect.signature(obj)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["signature_get_signature"]
