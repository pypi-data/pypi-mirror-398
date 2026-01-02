# =============================================================================
# Docstring
# =============================================================================

"""
Random Choice Selection
=======================

Cryptographically secure random choice from sequence.

Examples
--------
>>> from rite.crypto.random import random_choice
>>> random_choice(['a', 'b', 'c']) in ['a', 'b', 'c']
True
>>> random_choice("ABC") in "ABC"
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Sequence
import secrets
from typing import TypeVar

# =============================================================================
# Types
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def random_choice(seq: Sequence[T]) -> T:
    """
    Choose random element from sequence (cryptographically secure).

    Args:
        seq: Non-empty sequence to choose from.

    Returns:
        Randomly selected element.

    Raises:
        IndexError: If sequence is empty.

    Examples:
        >>> random_choice(['a', 'b', 'c']) in ['a', 'b', 'c']
        True
        >>> random_choice("XYZ") in "XYZ"
        True
        >>> random_choice([1, 2, 3]) in [1, 2, 3]
        True
    """
    return secrets.choice(seq)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["random_choice"]
