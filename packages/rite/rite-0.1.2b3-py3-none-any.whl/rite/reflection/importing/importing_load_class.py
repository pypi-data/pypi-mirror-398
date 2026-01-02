# =============================================================================
# Docstring
# =============================================================================

"""
Class Importer
==============

Dynamically load class from module path.

Examples
--------
>>> from rite.reflection.importing import importing_load_class
>>> OrderedDict = importing_load_class("collections.OrderedDict")
>>> isinstance(OrderedDict(), dict)
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from importlib import import_module

# =============================================================================
# Exceptions
# =============================================================================


class ClassImportError(ImportError):
    """Raised when class cannot be dynamically imported."""


# =============================================================================
# Functions
# =============================================================================


def importing_load_class(path: str) -> type:
    """
    Dynamically load class from module path.

    Args:
        path: Fully qualified path (e.g., "module.Class").

    Returns:
        Loaded class object.

    Raises:
        ClassImportError: If module or class cannot be imported.

    Examples:
        >>> importing_load_class("collections.OrderedDict")
        <class 'collections.OrderedDict'>
        >>> importing_load_class("pathlib.Path")
        <class 'pathlib.Path'>

    Notes:
        Path format: "module.submodule.ClassName".
    """
    try:
        module_path, class_name = path.rsplit(".", 1)
    except ValueError as exc:
        raise ClassImportError(
            f"Invalid path format: '{path}'. " f"Expected 'module.ClassName'."
        ) from exc

    try:
        module = import_module(module_path)
    except ModuleNotFoundError as exc:
        raise ClassImportError(
            f"Module '{module_path}' not found: {exc}"
        ) from exc

    try:
        cls = getattr(module, class_name)
    except AttributeError as exc:
        raise ClassImportError(
            f"Module '{module_path}' has no class '{class_name}'."
        ) from exc

    result: type = cls
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["importing_load_class", "ClassImportError"]
