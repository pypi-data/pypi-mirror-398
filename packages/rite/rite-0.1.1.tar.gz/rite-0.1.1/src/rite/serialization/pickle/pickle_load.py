# =============================================================================
# Docstring
# =============================================================================

"""
Pickle Load
===========

Deserialize object from pickle file.

Examples
--------
>>> from rite.serialization.pickle import pickle_load
>>> data = pickle_load("data.pkl")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from pathlib import Path
import pickle
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def pickle_load(path: str | Path) -> Any:
    """
    Deserialize object from pickle file.

    Args:
        path: Path to pickle file.

    Returns:
        Deserialized object.

    Examples:
        >>> pickle_load("data.pkl")
        {'key': 'value'}

    Notes:
        Uses binary mode.
        Be careful with untrusted data.
    """
    file_path = Path(path)

    with file_path.open("rb") as f:
        result: Any = pickle.load(f)

    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["pickle_load"]
