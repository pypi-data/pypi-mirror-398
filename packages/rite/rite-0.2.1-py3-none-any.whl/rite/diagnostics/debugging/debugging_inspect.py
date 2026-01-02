# =============================================================================
# Docstring
# =============================================================================

"""
Variable Inspector
==================

Inspect variables and their attributes.

Examples
--------
>>> from rite.diagnostics.debugging import debugging_inspect
>>> obj = {"key": "value"}
>>> debugging_inspect(obj)

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def debugging_inspect(
    obj: Any,
    show_private: bool = False,
) -> dict[str, Any]:
    """
    Inspect object attributes and methods.

    Args:
        obj: Object to inspect.
        show_private: Include private attributes (starting with _).

    Returns:
        Dictionary with object information.

    Examples:
        >>> class Example:
        ...     def __init__(self):
        ...         self.value = 42
        >>> info = debugging_inspect(Example())
        >>> "value" in info["attributes"]
        True
    """
    result: dict[str, Any] = {
        "type": type(obj).__name__,
        "module": getattr(type(obj), "__module__", None),
        "attributes": {},
        "methods": [],
        "is_callable": callable(obj),
    }

    # Get attributes
    for name in dir(obj):
        if not show_private and name.startswith("_"):
            continue

        try:
            attr = getattr(obj, name)
            if callable(attr):
                result["methods"].append(name)
            else:
                result["attributes"][name] = attr
        except (AttributeError, TypeError):
            result["attributes"][name] = "<unavailable>"

    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["debugging_inspect"]
