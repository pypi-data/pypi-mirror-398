from typing import Dict, Optional, Tuple


class TrieNode:
    __slots__ = ("children", "value", "is_end")

    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.value: Optional[str] = None
        self.is_end: bool = False


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def add(self, key: str, value: str) -> None:
        """Insert a key-value pair into the Trie."""
        node = self.root
        for char in key:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        node.value = value

    def longest_match(self, text: str) -> Tuple[Optional[str], int]:
        """
        Find the longest key in the Trie that matches the start of the text.
        Returns (value, length_of_match).
        If no match found, returns (None, 0).
        """
        node = self.root
        last_match_value = None
        last_match_len = 0
        current_len = 0

        for char in text:
            if char not in node.children:
                break
            node = node.children[char]
            current_len += 1
            if node.is_end:
                last_match_value = node.value
                last_match_len = current_len

        return last_match_value, last_match_len
