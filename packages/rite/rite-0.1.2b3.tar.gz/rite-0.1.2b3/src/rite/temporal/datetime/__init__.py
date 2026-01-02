# =============================================================================
# Docstring
# =============================================================================

"""
DateTime Module
===============

Date and time operations.

This submodule provides utilities for working with datetime objects
including creation, parsing, formatting, and conversions.

Examples
--------
>>> from rite.temporal.datetime import datetime_now, datetime_format
>>> now = datetime_now()
>>> datetime_format(now)
'2024-12-27 15:30:00'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .datetime_format import datetime_format
from .datetime_from_timestamp import datetime_from_timestamp
from .datetime_now import datetime_now
from .datetime_parse import datetime_parse
from .datetime_to_iso import datetime_to_iso
from .datetime_to_timestamp import datetime_to_timestamp

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "datetime_now",
    "datetime_from_timestamp",
    "datetime_to_timestamp",
    "datetime_parse",
    "datetime_format",
    "datetime_to_iso",
]
