# Import | Future
from __future__ import annotations

# Import | Local Modules
from .average_word_length import average_word_length
from .char_frequency import char_frequency
from .is_palindrome import is_palindrome
from .longest_word import longest_word
from .shortest_word import shortest_word
from .word_count import word_count

__all__: list[str] = [
    "char_frequency",
    "word_count",
    "is_palindrome",
    "longest_word",
    "shortest_word",
    "average_word_length",
]
