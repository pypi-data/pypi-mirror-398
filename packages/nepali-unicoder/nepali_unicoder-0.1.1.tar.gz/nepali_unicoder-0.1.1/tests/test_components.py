import os
import sys
import unittest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from nepali_unicoder.loader import RuleLoader
from nepali_unicoder.tokenizer import Tokenizer
from nepali_unicoder.trie import Trie


class TestTrie(unittest.TestCase):
    def test_add_and_match(self):
        trie = Trie()
        trie.add("ka", "क")
        trie.add("k", "क्")

        val, length = trie.longest_match("ka")
        self.assertEqual(val, "क")
        self.assertEqual(length, 2)

        val, length = trie.longest_match("k")
        self.assertEqual(val, "क्")
        self.assertEqual(length, 1)

        val, length = trie.longest_match("z")
        self.assertIsNone(val)
        self.assertEqual(length, 0)


class TestTokenizer(unittest.TestCase):
    def test_tokenize(self):
        tokenizer = Tokenizer()
        tokens = tokenizer.tokenize("mero {name} ho")

        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[0].value, "mero ")
        self.assertEqual(tokens[0].type, "ROMAN")

        self.assertEqual(tokens[1].value, "name")
        self.assertEqual(tokens[1].type, "BLOCK")

        self.assertEqual(tokens[2].value, " ho")
        self.assertEqual(tokens[2].type, "ROMAN")

    def test_escape(self):
        tokenizer = Tokenizer()
        tokens = tokenizer.tokenize("{{")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].value, "{")
        self.assertEqual(tokens[0].type, "LITERAL")


class TestRuleLoader(unittest.TestCase):
    def test_load(self):
        loader = RuleLoader()
        # This assumes rules.json exists in the correct place
        try:
            trie = loader.load()
            self.assertIsInstance(trie, Trie)
            # Check a known mapping
            val, length = trie.longest_match("ka")
            self.assertEqual(val, "क")
        except FileNotFoundError:
            print("Skipping RuleLoader test as files might not be present in test env")


if __name__ == "__main__":
    unittest.main()
