# =============================================================================
# Docstring
# =============================================================================

"""
Environment Set
===============

Set environment variable value.

Examples
--------
>>> from rite.system.environment import env_set
>>> env_set("MY_VAR", "value")

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


def env_set(key: str, value: str) -> None:
    """
    Set environment variable value.

    Args:
        key: Environment variable name.
        value: Value to set.

    Returns:
        None

    Examples:
        >>> env_set("MY_VAR", "value")
        >>> env_get("MY_VAR")
        'value'

    Notes:
        Affects current process and children.
    """
    os.environ[key] = value


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["env_set"]
