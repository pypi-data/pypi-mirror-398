# =============================================================================
# Docstring
# =============================================================================

"""
Random Alphanumeric Generator
==============================

Generate random alphanumeric strings.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import secrets
import string

# =============================================================================
# Functions
# =============================================================================


def random_alphanumeric(
    length: int = 16,
    include_lowercase: bool = True,
    include_uppercase: bool = True,
) -> str:
    """
    Generate a random alphanumeric string.

    Args:
        length: Length of the random string
        include_lowercase: Include lowercase letters
        include_uppercase: Include uppercase letters

    Returns:
        Random alphanumeric string

    Raises:
        ValueError: If both include_lowercase and include_uppercase are False

    Example:
        >>> len(random_alphanumeric(10))
        10
    """
    charset = string.digits
    if include_lowercase:
        charset += string.ascii_lowercase
    if include_uppercase:
        charset += string.ascii_uppercase
    if charset == string.digits:
        raise ValueError(
            "At least one of include_lowercase or include_uppercase must be True"
        )
    return "".join(secrets.choice(charset) for _ in range(length))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "random_alphanumeric",
]
