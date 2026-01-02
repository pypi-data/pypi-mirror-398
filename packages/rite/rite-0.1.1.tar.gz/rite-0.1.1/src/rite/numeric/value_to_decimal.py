# =============================================================================
# Docstring
# =============================================================================

"""
Decimal Conversion
==================

Convert values to Decimal type with validation.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import decimal
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def value_to_decimal(value: Any) -> decimal.Decimal:
    """
    Convert a value into a Decimal and handle any conversion required.

    Args:
        value: Value to convert to Decimal

    Returns:
        Decimal representation of the value

    Raises:
        ValueError: If value is None or cannot be converted to Decimal

    Example:
        >>> value_to_decimal(12.5)
        Decimal('12.5')
        >>> value_to_decimal("12.5")
        Decimal('12.5')
    """
    if value is None:
        raise ValueError("None is not a valid decimal value.")
    if not isinstance(value, decimal.Decimal):
        try:
            return decimal.Decimal(str(value))
        except decimal.InvalidOperation as exc:
            raise ValueError(
                "Value could not be converted into a decimal."
            ) from exc
    return value


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "value_to_decimal",
]
