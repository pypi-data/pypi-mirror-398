# =============================================================================
# Docstring
# =============================================================================

"""
Parameters Inspector
====================

Get function parameters.

Examples
--------
>>> from rite.reflection.signature import signature_get_parameters
>>> def func(a: int, b: str = "default") -> str:
...     return f"{a}{b}"
>>> params = signature_get_parameters(func)
>>> list(params.keys())
['a', 'b']

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


def signature_get_parameters(
    obj: Any,
) -> dict[str, inspect.Parameter]:
    """
    Get function parameters.

    Args:
        obj: Function or method to inspect.

    Returns:
        Dictionary of parameter names to Parameter objects.

    Examples:
        >>> def func(a: int, b: str = "default") -> str:
        ...     return f"{a}{b}"
        >>> params = signature_get_parameters(func)
        >>> 'a' in params
        True
        >>> 'b' in params
        True

    Notes:
        Uses inspect.signature.
        Returns ordered dict of parameters.
    """
    sig = inspect.signature(obj)
    return dict(sig.parameters)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["signature_get_parameters"]
