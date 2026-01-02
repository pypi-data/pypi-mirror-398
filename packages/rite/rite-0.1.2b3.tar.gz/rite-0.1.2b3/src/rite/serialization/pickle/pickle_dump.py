# =============================================================================
# Docstring
# =============================================================================

"""
Pickle Dump
===========

Serialize object to pickle file.

Examples
--------
>>> from rite.serialization.pickle import pickle_dump
>>> pickle_dump("data.pkl", {"key": "value"})

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


def pickle_dump(path: str | Path, data: Any) -> None:
    """
    Serialize object to pickle file.

    Args:
        path: Path to output pickle file.
        data: Object to serialize.

    Returns:
        None

    Examples:
        >>> pickle_dump("data.pkl", {"key": "value"})
        >>> pickle_dump("data.pkl", [1, 2, 3])

    Notes:
        Creates parent directories if needed.
        Uses binary mode.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("wb") as f:
        pickle.dump(data, f)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["pickle_dump"]
