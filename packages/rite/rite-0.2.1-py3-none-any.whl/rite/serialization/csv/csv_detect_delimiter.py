# =============================================================================
# Docstring
# =============================================================================

"""
CSV Delimiter Detector
=======================

Detect delimiter from filename.

Examples
--------
>>> from rite.serialization.csv import csv_detect_delimiter
>>> csv_detect_delimiter("data.tsv")
'\\t'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def csv_detect_delimiter(filename: str) -> str:
    """
    Detect delimiter from filename extension.

    Args:
        filename: CSV filename or path.

    Returns:
        Delimiter character (tab or comma).

    Examples:
        >>> csv_detect_delimiter("data.csv")
        ','
        >>> csv_detect_delimiter("data.tsv")
        '\\t'
        >>> csv_detect_delimiter("path/to/data.tsv")
        '\\t'

    Notes:
        Returns tab for .tsv, comma otherwise.
    """
    if filename.endswith(".tsv"):
        return "\t"
    return ","


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["csv_detect_delimiter"]
