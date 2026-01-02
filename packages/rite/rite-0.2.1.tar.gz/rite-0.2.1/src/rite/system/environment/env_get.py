# =============================================================================
# Docstring
# =============================================================================

"""
Environment Get
===============

Get environment variable value.

Examples
--------
>>> from rite.system.environment import env_get
>>> env_get("PATH")

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


def env_get(key: str, default: str | None = None) -> str | None:
    """
    Get environment variable value.

    Args:
        key: Environment variable name.
        default: Default value if not found.

    Returns:
        Variable value or default.

    Examples:
        >>> env_get("PATH")
        '/usr/bin:/bin'
        >>> env_get("MISSING", "default")
        'default'

    Notes:
        Returns None if not found and no default.
    """
    return os.environ.get(key, default)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["env_get"]
