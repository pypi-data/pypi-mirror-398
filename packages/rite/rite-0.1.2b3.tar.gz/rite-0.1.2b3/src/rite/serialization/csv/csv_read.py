# =============================================================================
# Docstring
# =============================================================================

"""
CSV Reader
==========

Read CSV file to list of dicts.

Examples
--------
>>> from rite.serialization.csv import csv_read
>>> rows = csv_read("data.csv")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import csv
from pathlib import Path
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def csv_read(path: str | Path, delimiter: str = ",") -> list[dict[str, Any]]:
    """
    Read CSV file to list of dictionaries.

    Args:
        path: Path to CSV file.
        delimiter: CSV delimiter character.

    Returns:
        List of row dictionaries.

    Examples:
        >>> csv_read("data.csv")
        [{'col1': 'val1', 'col2': 'val2'}, ...]
        >>> csv_read("data.tsv", delimiter="\\t")
        [...]

    Notes:
        Uses DictReader for named columns.
        First row is header.
    """
    file_path = Path(path)
    rows: list[dict[str, Any]] = []

    with file_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            rows.append(dict(row))

    return rows


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["csv_read"]
