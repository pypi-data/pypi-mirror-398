# =============================================================================
# Docstring
# =============================================================================

"""
Decimal Converter
=================

Convert value to Decimal type.

Examples
--------
>>> from rite.numeric.conversion import conversion_to_decimal
>>> conversion_to_decimal("3.14")
Decimal('3.14')

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from decimal import Decimal, InvalidOperation

# =============================================================================
# Functions
# =============================================================================


def conversion_to_decimal(value: str | int | float) -> Decimal | None:
    """
    Convert value to Decimal type.

    Args:
        value: Value to convert (string, int, or float).

    Returns:
        Decimal object or None if conversion fails.

    Examples:
        >>> conversion_to_decimal("3.14")
        Decimal('3.14')
        >>> conversion_to_decimal(42)
        Decimal('42')
        >>> conversion_to_decimal("invalid") is None
        True

    Notes:
        Returns None on invalid input.
        Preserves precision for strings.
    """
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["conversion_to_decimal"]
