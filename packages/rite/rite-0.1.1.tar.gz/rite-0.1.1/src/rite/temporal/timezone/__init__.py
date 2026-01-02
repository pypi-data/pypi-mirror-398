# =============================================================================
# Docstring
# =============================================================================

"""
Timezone Module
===============

Timezone operations.

This submodule provides utilities for working with timezones
using the standard library zoneinfo module (Python 3.9+).

Examples
--------
>>> from rite.temporal.timezone import timezone_get, timezone_convert
>>> from datetime import datetime, timezone
>>> dt = datetime.now(timezone.utc)
>>> timezone_convert(dt, "Europe/Amsterdam")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .timezone_convert import timezone_convert
from .timezone_get import timezone_get
from .timezone_list import timezone_list

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "timezone_get",
    "timezone_convert",
    "timezone_list",
]
