# =============================================================================
# Docstring
# =============================================================================

"""
Environment List
================

Get all environment variables.

Examples
--------
>>> from rite.system.environment import env_list
>>> env_list()

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


def env_list() -> dict[str, str]:
    """
    Get all environment variables as dictionary.

    Returns:
        Dictionary of environment variables.

    Examples:
        >>> env_list()
        {'PATH': '/usr/bin', 'HOME': '/home/user', ...}

    Notes:
        Returns a copy, modifications don't affect environment.
    """
    return dict(os.environ)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["env_list"]
