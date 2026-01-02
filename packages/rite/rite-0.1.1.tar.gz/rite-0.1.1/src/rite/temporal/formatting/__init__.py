# =============================================================================
# Docstring
# =============================================================================

"""
Formatting Module
=================

Date/time formatting utilities.

This submodule provides utilities for formatting datetime objects
into various string representations.

Examples
--------
>>> from rite.temporal.formatting import format_iso8601
>>> from datetime import datetime, timezone
>>> dt = datetime.now(timezone.utc)
>>> format_iso8601(dt)

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .format_human_readable import format_human_readable
from .format_iso8601 import format_iso8601
from .format_rfc3339 import format_rfc3339

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "format_iso8601",
    "format_rfc3339",
    "format_human_readable",
]
