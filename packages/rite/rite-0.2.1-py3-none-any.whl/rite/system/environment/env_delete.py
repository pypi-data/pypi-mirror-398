# =============================================================================
# Docstring
# =============================================================================

"""
Environment Delete
==================

Delete environment variable.

Examples
--------
>>> from rite.system.environment import env_delete
>>> env_delete("MY_VAR")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import os

# =============================================================================
# Functions
# =============================================================================


def env_delete(key: str) -> None:
    """
    Delete environment variable.

    Args:
        key: Environment variable name.

    Returns:
        None

    Examples:
        >>> env_delete("MY_VAR")

    Notes:
        Silently ignores if variable doesn't exist.
    """
    os.environ.pop(key, None)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["env_delete"]
