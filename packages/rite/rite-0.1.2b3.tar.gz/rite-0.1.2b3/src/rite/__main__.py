# =============================================================================
# Docstring
# =============================================================================

"""
Provides a rite entry point
===========================



"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import platform

# Import | Local Modules
import rite

# =============================================================================
# Main
# =============================================================================


def main():
    """Main entry point for rite package."""
    print()
    print("rite is set!")
    print()
    print(f"rite: {rite.__version__}")
    print(
        f"Python: {platform.python_version()}"
        f" ({platform.python_implementation()})"
    )
    print()


if __name__ == "__main__":
    main()
