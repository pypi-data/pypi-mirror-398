# =============================================================================
# Docstring
# =============================================================================

"""
Return Annotation Inspector
===========================

Get function return annotation.

Examples
--------
>>> from rite.reflection.signature import (
...     signature_get_return_annotation
... )
>>> def func(a: int) -> str:
...     return str(a)
>>> signature_get_return_annotation(func)
<class 'str'>

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


def signature_get_return_annotation(obj: Any) -> Any:
    """
    Get function return annotation.

    Args:
        obj: Function or method to inspect.

    Returns:
        Return annotation or Signature.empty.

    Examples:
        >>> def func(a: int) -> str:
        ...     return str(a)
        >>> signature_get_return_annotation(func)
        <class 'str'>

    Notes:
        Returns Signature.empty if no annotation.
    """
    sig = inspect.signature(obj)
    return sig.return_annotation


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["signature_get_return_annotation"]
