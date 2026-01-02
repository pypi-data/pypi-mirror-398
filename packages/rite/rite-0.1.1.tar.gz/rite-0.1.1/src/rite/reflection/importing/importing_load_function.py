# =============================================================================
# Docstring
# =============================================================================

"""
Function Importer
=================

Dynamically load function from module path.

Examples
--------
>>> from rite.reflection.importing import importing_load_function
>>> dumps = importing_load_function("json.dumps")
>>> dumps({"key": "value"})
'{"key": "value"}'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from importlib import import_module
from typing import Callable

# =============================================================================
# Functions
# =============================================================================


def importing_load_function(path: str) -> Callable:
    """
    Dynamically load function from module path.

    Args:
        path: Fully qualified path (e.g., "module.function").

    Returns:
        Loaded function object.

    Raises:
        ImportError: If module cannot be imported.
        AttributeError: If function not found.

    Examples:
        >>> importing_load_function("json.dumps")
        <function dumps at 0x...>
        >>> importing_load_function("os.path.join")
        <function join at 0x...>

    Notes:
        Path format: "module.submodule.function_name".
    """
    try:
        module_path, func_name = path.rsplit(".", 1)
    except ValueError as exc:
        raise ImportError(
            f"Invalid path format: '{path}'. " f"Expected 'module.function'."
        ) from exc

    module = import_module(module_path)
    func = getattr(module, func_name)

    result: Callable = func
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["importing_load_function"]
