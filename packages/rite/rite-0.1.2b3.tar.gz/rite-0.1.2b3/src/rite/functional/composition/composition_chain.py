# =============================================================================
# Docstring
# =============================================================================

"""
Function Chain
==============

Chain method calls fluently.

Examples
--------
>>> from rite.functional.composition import composition_chain
>>> result = composition_chain(3).pipe(
...     lambda x: x + 1,
...     lambda x: x * 2
... ).value()
>>> result
8

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
# Classes
# =============================================================================


class composition_chain:
    """
    Fluent chainable function application.

    Attributes:
        _value: Current value in chain.

    Examples:
        >>> chain = composition_chain(5)
        >>> result = chain.pipe(lambda x: x * 2).pipe(
        ...     lambda x: x + 1
        ... ).value()
        >>> result
        11
    """

    def __init__(self, value: Any) -> None:
        """
        Initialize chain with value.

        Args:
            value: Initial value.
        """
        self._value = value

    def pipe(self, *functions: Callable[[Any], Any]) -> composition_chain:
        """
        Apply functions to current value.

        Args:
            *functions: Functions to apply.

        Returns:
            Self for chaining.

        Examples:
            >>> composition_chain(3).pipe(
            ...     lambda x: x + 1
            ... ).value()
            4
        """
        for func in functions:
            self._value = func(self._value)
        return self

    def value(self) -> Any:
        """
        Get current value.

        Returns:
            Current value in chain.

        Examples:
            >>> composition_chain(42).value()
            42
        """
        return self._value


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["composition_chain"]
