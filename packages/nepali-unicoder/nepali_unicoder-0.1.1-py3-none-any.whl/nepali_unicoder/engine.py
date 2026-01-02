import re
from typing import Optional

from nepali_unicoder.loader import PreetiLoader, RuleLoader
from nepali_unicoder.rules import PREETI_TO_UNICODE_MAPPING
from nepali_unicoder.tokenizer import Tokenizer
from nepali_unicoder.trie import Trie


class Engine:
    def __init__(
        self,
        trie: Optional[Trie] = None,
        tokenizer: Optional[Tokenizer] = None,
        mode: str = "roman",
    ):
        self.mode = mode
        self.post_rules = []

        if trie is None:
            if mode == "preeti":
                loader = PreetiLoader()
                # Load post-processing rules for Preeti mode
                self.post_rules = PREETI_TO_UNICODE_MAPPING.get("post_rules", [])
            else:
                loader = RuleLoader()
            self.trie = loader.load()
        else:
            self.trie = trie

        if tokenizer is None:
            self.tokenizer = Tokenizer()
        else:
            self.tokenizer = tokenizer

    def transliterate(self, text: str) -> str:
        """
        Convert Roman text to Devanagari using the Trie.
        """
        if not text:
            return ""

        tokens = self.tokenizer.tokenize(text)
        result = []

        for token in tokens:
            if token.type == "BLOCK":
                result.append(token.value)
            elif token.type == "LITERAL":
                result.append(token.value)
            elif token.type == "NUMBER":
                # Process Number chunk: transliterate digits, keep others (like .) as is
                for char in token.value:
                    if char.isdigit():
                        # Use Trie to find digit mapping (digits are single chars in rules)
                        match_val, _ = self.trie.longest_match(char)
                        if match_val:
                            result.append(match_val)
                        else:
                            result.append(char)
                    else:
                        result.append(char)
            elif token.type == "ROMAN":
                # Process Roman chunk with Trie
                chunk = token.value
                idx = 0
                chunk_len = len(chunk)

                while idx < chunk_len:
                    # Try to find longest match starting at idx
                    sub = chunk[idx:]
                    match_val, match_len = self.trie.longest_match(sub)

                    if match_val:
                        result.append(match_val)
                        idx += match_len
                    else:
                        # No match, keep character as is
                        result.append(chunk[idx])
                        idx += 1

        output = "".join(result)

        # Apply post-processing rules for Preeti mode
        if self.mode == "preeti" and self.post_rules:
            output = self._apply_post_rules(output)

        return output

    def _apply_post_rules(self, text: str) -> str:
        """
        Apply post-processing rules (regex replacements) to the text.
        Used for Preeti mode to handle contextual transformations.
        """
        for pattern, replacement in self.post_rules:
            text = re.sub(pattern, replacement, text)
        return text
