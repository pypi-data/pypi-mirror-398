# =============================================================================
# Docstring
# =============================================================================

"""
Design Pattern Collections Module
===================================

Provides design pattern implementations for common software patterns.

Classes:
--------
- SingletonMeta: Singleton pattern metaclass
- Observer: Observer pattern implementation
- ObjectPool: Object pool pattern

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .object_pool import ObjectPool
from .observer import Observable, Observer

# Import | Local
from .singleton import SingletonMeta

# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "SingletonMeta",
    "Observer",
    "Observable",
    "ObjectPool",
]
