# =============================================================================
# Docstring
# =============================================================================

"""
Trie (Prefix Tree)
==================

A trie data structure for efficient string prefix operations.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import Any

# Import | Libraries

# Import | Local Modules


# =============================================================================
# Classes
# =============================================================================


class TrieNode:
    """
    TrieNode Class
    ==============

    A single node in a Trie structure.

    """

    def __init__(self) -> None:
        """Initialize a trie node."""
        self.children: dict[str, TrieNode] = {}
        self.is_end_of_word: bool = False
        self.value: Any | None = None


class Trie:
    """
    Trie Class
    ==========

    A prefix tree (trie) for efficient string operations like autocomplete,
    spell checking, and prefix matching.

    """

    def __init__(self) -> None:
        """Initialize an empty trie."""
        self.root = TrieNode()
        self._size = 0

    def insert(self, word: str, value: Any | None = None) -> None:
        """
        Insert a word into the trie.

        Args:
        ----
            word: The word to insert.
            value: Optional value to associate with the word.

        """
        if word == "":
            return

        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]

        if not node.is_end_of_word:
            self._size += 1
        node.is_end_of_word = True
        node.value = value

    def search(self, word: str) -> bool:
        """
        Search for an exact word in the trie.

        Args:
        ----
            word: The word to search for.

        Returns:
        -------
            bool: True if word exists in trie.

        """
        if word == "":
            return False
        node = self._find_node(word)
        return node is not None and node.is_end_of_word

    def starts_with(self, prefix: str) -> bool:
        """
        Check if any word in trie starts with given prefix.

        Args:
        ----
            prefix: The prefix to check.

        Returns:
        -------
            bool: True if prefix exists in trie.

        """
        return self._find_node(prefix) is not None

    def get(self, word: str) -> Any | None:
        """
        Get the value associated with a word.

        Args:
        ----
            word: The word to look up.

        Returns:
        -------
            Any | None: Associated value or None if not found.

        """
        node = self._find_node(word)
        if node and node.is_end_of_word:
            return node.value
        return None

    def delete(self, word: str) -> bool:
        """
        Delete a word from the trie.

        Args:
        ----
            word: The word to delete.

        Returns:
        -------
            bool: True if word was deleted, False if not found.

        """

        def _delete_helper(node: TrieNode, word: str, index: int) -> bool:
            if index == len(word):
                if not node.is_end_of_word:
                    return False
                node.is_end_of_word = False
                node.value = None
                return len(node.children) == 0

            char = word[index]
            if char not in node.children:
                return False

            child = node.children[char]
            should_delete_child = _delete_helper(child, word, index + 1)

            if should_delete_child:
                del node.children[char]
                return len(node.children) == 0 and not node.is_end_of_word

            return False

        if self.search(word):
            _delete_helper(self.root, word, 0)
            self._size -= 1
            return True
        return False

    def get_words_with_prefix(self, prefix: str) -> list[str]:
        """
        Get all words that start with given prefix.

        Args:
        ----
            prefix: The prefix to match.

        Returns:
        -------
            list[str]: List of words with the prefix.

        """
        node = self._find_node(prefix)
        if node is None:
            return []

        words = []
        self._collect_words(node, prefix, words)
        return words

    def autocomplete(self, prefix: str) -> list[str]:
        """Return all completions for the given prefix."""
        return self.get_words_with_prefix(prefix)

    def get_all_words(self) -> list[str]:
        """
        Get all words stored in the trie.

        Returns:
        -------
            list[str]: All words in the trie.

        """
        words = []
        self._collect_words(self.root, "", words)
        return words

    def _find_node(self, prefix: str) -> TrieNode | None:
        """
        Find the node corresponding to a prefix.

        Args:
        ----
            prefix: The prefix to find.

        Returns:
        -------
            TrieNode | None: The node or None if not found.

        """
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node

    def _collect_words(
        self, node: TrieNode, prefix: str, words: list[str]
    ) -> None:
        """
        Recursively collect all words from a node.

        Args:
        ----
            node: Current node.
            prefix: Current prefix string.
            words: List to collect words into.

        """
        if node.is_end_of_word:
            words.append(prefix)

        for char, child_node in node.children.items():
            self._collect_words(child_node, prefix + char, words)

    def __len__(self) -> int:
        """Return number of words in trie."""
        return self._size

    def __contains__(self, word: str) -> bool:
        """Check if word is in trie."""
        return self.search(word)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Trie(words={self._size})"


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "Trie",
    "TrieNode",
]

__all__: list[str] = [
    "Trie",
    "TrieNode",
]
