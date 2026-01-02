import json
import os

from nepali_unicoder.rules import PREETI_TO_UNICODE_MAPPING, ROMAN_TO_UNICODE_RULES
from nepali_unicoder.trie import Trie


class RuleLoader:
    def __init__(self):
        self.word_maps_path = os.path.join(os.path.dirname(__file__), "word_maps.json")

    def load(self) -> Trie:
        """Load rules and custom mappings into a Trie."""
        trie = Trie()
        self._load_rules(trie)
        self._load_custom_mappings(trie)
        return trie

    def _load_rules(self, trie: Trie):
        data = ROMAN_TO_UNICODE_RULES

        consonants = data.get("consonants", {})
        vowels = data.get("vowels", {})
        matras = data.get("matras", {})
        special = data.get("special", {})
        digits = data.get("digits", {})

        # 1. Independent Vowels
        for rom, dev in vowels.items():
            trie.add(rom, dev)

        # 2. Consonants and Combinations
        halanta = "्"

        for rom_cons, dev_cons in consonants.items():
            # Case 1: Consonant alone (halanta form) -> 'k' -> 'क्'
            trie.add(rom_cons, dev_cons + halanta)

            # Case 2: Consonant + 'a' (Schwa form) -> 'ka' -> 'क'
            trie.add(rom_cons + "a", dev_cons)

            # Case 3: Consonant + other vowels -> 'ki' -> 'कि'
            for rom_vowel, matra in matras.items():
                if rom_vowel == "a":
                    continue  # Handled above
                trie.add(rom_cons + rom_vowel, dev_cons + matra)

        # 3. Special, Digits, Punctuation
        for rom, dev in special.items():
            trie.add(rom, dev)

        for rom, dev in digits.items():
            trie.add(rom, dev)

        # Ensure 'a' maps to 'अ' (already in vowels, but good to double check)
        trie.add("a", vowels.get("a", "अ"))

    def _load_custom_mappings(self, trie: Trie):
        if not os.path.exists(self.word_maps_path):
            return

        try:
            with open(self.word_maps_path, "r", encoding="utf-8") as f:
                mappings = json.load(f)
                for roman, devanagari in mappings.items():
                    trie.add(roman.lower(), devanagari)
        except Exception as e:
            print(f"Error reading word_maps.json: {e}")


class PreetiLoader:
    def __init__(self):
        pass

    def load(self) -> Trie:
        """Load Preeti rules into a Trie."""
        trie = Trie()
        data = PREETI_TO_UNICODE_MAPPING

        mappings = data.get("mappings", {})
        for key, value in mappings.items():
            trie.add(key, value)

        return trie
