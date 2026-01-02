# =============================================================================
# Docstring
# =============================================================================

"""
State Dumper
============

Dump variable states for debugging.

Examples
--------
>>> from rite.diagnostics.debugging import debugging_dump
>>> debugging_dump(x=1, y=2, name="test")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import pprint
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def debugging_dump(
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Print variables in formatted way for debugging.

    Args:
        *args: Positional arguments to dump.
        **kwargs: Named arguments to dump.

    Examples:
        >>> debugging_dump(42, "hello", status="active")
        ARG 0: 42
        ARG 1: hello
        status: active
        >>> data = {"key": "value"}
        >>> debugging_dump(data=data)
        data: {'key': 'value'}
    """
    if args:
        for i, arg in enumerate(args):
            print(f"ARG {i}: {_format_value(arg)}")

    if kwargs:
        for key, value in kwargs.items():
            print(f"{key}: {_format_value(value)}")


def _format_value(value: Any) -> str:
    """Format value for readable output."""
    if isinstance(value, (dict, list, tuple, set)):
        return pprint.pformat(value, width=60, compact=True)
    return repr(value)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["debugging_dump"]
