# =============================================================================
# Docstring
# =============================================================================

"""
Module Importer
===============

Dynamically import module by name.

Examples
--------
>>> from rite.reflection.importing import importing_load_module
>>> json_module = importing_load_module("json")
>>> json_module.dumps({"key": "value"})
'{"key": "value"}'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from importlib import import_module
from types import ModuleType

# =============================================================================
# Functions
# =============================================================================


def importing_load_module(name: str) -> ModuleType:
    """
    Dynamically import module by name.

    Args:
        name: Module name (e.g., "json", "os.path").

    Returns:
        Imported module object.

    Raises:
        ModuleNotFoundError: If module cannot be imported.

    Examples:
        >>> importing_load_module("json")
        <module 'json' from '...'>
        >>> importing_load_module("os.path")
        <module 'posixpath' from '...'>

    Notes:
        Uses importlib.import_module.
    """
    return import_module(name)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["importing_load_module"]
