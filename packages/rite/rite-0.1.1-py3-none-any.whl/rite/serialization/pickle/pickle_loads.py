# =============================================================================
# Docstring
# =============================================================================

"""
Pickle Loads
============

Deserialize object from bytes.

Examples
--------
>>> from rite.serialization.pickle import pickle_loads
>>> data = pickle_loads(b'\\x80\\x04...')

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


def pickle_loads(data: bytes) -> Any:
    """
    Deserialize object from bytes.

    Args:
        data: Serialized bytes.

    Returns:
        Deserialized object.

    Examples:
        >>> pickle_loads(b'\\x80\\x04...')
        {'key': 'value'}

    Notes:
        Be careful with untrusted data.
    """
    result: Any = pickle.loads(data)
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["pickle_loads"]
