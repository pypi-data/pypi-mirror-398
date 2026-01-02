# =============================================================================
# Docstring
# =============================================================================

"""
Locals Dumper
=============

Dump all local variables in current scope.

Examples
--------
>>> from rite.diagnostics.debugging import debugging_locals
>>> def example():
...     x = 1
...     y = 2
...     debugging_locals()

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import inspect
import pprint
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def debugging_locals(show_private: bool = False) -> dict[str, Any]:
    """
    Dump local variables from calling scope.

    Args:
        show_private: Include private variables (starting with _).

    Returns:
        Dictionary of local variables.

    Examples:
        >>> def test():
        ...     x = 42
        ...     y = "hello"
        ...     locals_dict = debugging_locals()
        ...     return "x" in locals_dict
        >>> test()
        True

    Notes:
        This function inspects the caller's frame to get locals.
    """
    frame = inspect.currentframe()
    if frame is None:
        return {}

    try:
        caller_frame = frame.f_back
        if caller_frame is None:
            return {}

        caller_locals = caller_frame.f_locals.copy()

        # Filter variables
        if not show_private:
            caller_locals = {
                k: v for k, v in caller_locals.items() if not k.startswith("_")
            }

        print("=== LOCAL VARIABLES ===")
        pprint.pprint(caller_locals, width=70, compact=True)

        return caller_locals
    finally:
        del frame


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["debugging_locals"]
