# =============================================================================
# Docstring
# =============================================================================

"""
Pickle Dumps
============

Serialize object to bytes.

Examples
--------
>>> from rite.serialization.pickle import pickle_dumps
>>> data = pickle_dumps({"key": "value"})

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import pickle
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def pickle_dumps(data: Any) -> bytes:
    """
    Serialize object to bytes.

    Args:
        data: Object to serialize.

    Returns:
        Serialized bytes.

    Examples:
        >>> pickle_dumps({"key": "value"})
        b'\\x80\\x04...'

    Notes:
        Returns bytes for network transmission.
    """
    result: bytes = pickle.dumps(data)
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["pickle_dumps"]
