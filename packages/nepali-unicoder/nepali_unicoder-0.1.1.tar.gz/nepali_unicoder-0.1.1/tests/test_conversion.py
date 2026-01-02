import os
import sys
import unittest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from nepali_unicoder.convert import Converter


class TestNepaliUnicoder(unittest.TestCase):
    def setUp(self):
        self.converter = Converter()

    def test_basic_consonants(self):
        # k -> क् (halanta)
        self.assertEqual(self.converter.convert("k"), "क्")
        # ka -> क (schwa)
        self.assertEqual(self.converter.convert("ka"), "क")
        # kaa -> का (aa)
        self.assertEqual(self.converter.convert("kaa"), "का")

        # kh -> ख्
        self.assertEqual(self.converter.convert("kh"), "ख्")
        # kha -> ख
        self.assertEqual(self.converter.convert("kha"), "ख")

    def test_words(self):
        self.assertEqual(self.converter.convert("namaste"), "नमस्ते")
        # nepaala -> ne (ने) pa (प) -> paa (पा) la (ल)
        # nepaala -> नेपाल
        self.assertEqual(self.converter.convert("nepaala"), "नेपाल")
        self.assertEqual(self.converter.convert("nepal"), "नेपाल")  # form word_maps.txt
        self.assertEqual(self.converter.convert("mero"), "मेरो")
        # naam -> नाम्. naama -> नाम
        self.assertEqual(self.converter.convert("naama"), "नाम")
        # bhaat -> भात्. bhaata -> भात
        self.assertEqual(self.converter.convert("bhaata"), "भात")

    def test_vowels(self):
        self.assertEqual(self.converter.convert("a"), "अ")
        self.assertEqual(self.converter.convert("aa"), "आ")
        self.assertEqual(self.converter.convert("i"), "इ")
        self.assertEqual(self.converter.convert("u"), "उ")

        # Matras
        self.assertEqual(self.converter.convert("ki"), "कि")
        self.assertEqual(self.converter.convert("kee"), "की")
        self.assertEqual(self.converter.convert("ku"), "कु")
        self.assertEqual(self.converter.convert("koo"), "कू")
        self.assertEqual(self.converter.convert("ke"), "के")
        self.assertEqual(self.converter.convert("kai"), "कै")
        self.assertEqual(self.converter.convert("ko"), "को")
        self.assertEqual(self.converter.convert("kau"), "कौ")

    def test_special_chars(self):
        self.assertEqual(self.converter.convert("."), "।")
        self.assertEqual(self.converter.convert(".."), "॥")
        self.assertEqual(self.converter.convert("0123456789"), "०१२३४५६७८९")
        # Decimal number test
        self.assertEqual(self.converter.convert("123.34"), "१२३.३४")

    def test_as_is_block(self):
        self.assertEqual(self.converter.convert("{english}"), "english")
        self.assertEqual(self.converter.convert("mero {name} ho"), "मेरो name हो")
        self.assertEqual(self.converter.convert("{{"), "{")

    def test_conjuncts(self):
        # k + t -> क्त
        self.assertEqual(self.converter.convert("kt"), "क्त्")

        # gy -> ज्ञ (base) -> ज्ञ् (halanta)
        self.assertEqual(self.converter.convert("gy"), "ज्ञ्")
        # gya -> ज्ञ
        self.assertEqual(self.converter.convert("gya"), "ज्ञ")
        # gyaana -> ज्ञान
        self.assertEqual(self.converter.convert("gyaana"), "ज्ञान")


class TestPreetiUnicoder(unittest.TestCase):
    def setUp(self):
        self.converter = Converter(mode="preeti")

    def test_qwerty_alphabet(self):
        # Basic consonants from Preeti mapping
        # self.assertEqual(self.converter.convert("qwertyuiop QWERTYUIOP"), "त्रधभचतथगष्यउ त्तध्भ्च्त्थ्ग्क्ष्इए")
        self.assertEqual(
            self.converter.convert("q w e r t y u i o p Q W E R T Y U I O P"),
            "त्र ध भ च त थ ग ष् य उ त्त ध् भ् च् त् थ् ग् क्ष् इ ए",
        )
        pass

    def test_arabic_numbers(self):
        self.assertEqual(self.converter.convert("0123456789"), "ण्ज्ञद्दघद्धछटठडढ")

    def test_special_characters_to_num(self):
        # Special characters
        self.assertEqual(self.converter.convert("!@#$%^&*()"), "१२३४५६७८९०")

    def test_special_characters_to_unicoder(self):
        # Special characters
        # self.assertEqual(self.converter.convert("[]\\;',./{}|:\"<>?"), "ृे्सु,।र्रै्रस्ू?श्ररु")
        pass

    def test_reph_positioning(self):
        """Test that { (reph) is correctly positioned"""
        # { should map to र् and move before the preceding consonant
        # s{ should become र्क (not कर्)
        self.assertEqual(self.converter.convert("s{"), "र्क")
        # More complex: sf{ should become र्का
        self.assertEqual(self.converter.convert("sf{"), "र्का")
        self.assertEqual(self.converter.convert("s{sf"), "र्कका")

    def test_matra_reordering(self):
        """Test that matras (vowel signs) are correctly reordered"""
        # Short i (l = ि) should move after consonant
        # sl should become कि (not िक)
        self.assertEqual(self.converter.convert("sl"), "कि")
        # sL should become की
        self.assertEqual(self.converter.convert("sL"), "की")

    def test_m_character_contextual(self):
        """Test special m character transformations"""
        # qm should become क्र (त्र + m = क्र)
        self.assertEqual(self.converter.convert("qm"), "क्र")
        # Qm should become क्त (त्त + m = क्त)
        self.assertEqual(self.converter.convert("Qm"), "क्त")
        # pm should become ऊ (उ + m = ऊ)
        self.assertEqual(self.converter.convert("pm"), "ऊ")
        # em should become झ (भ + m = झ)
        self.assertEqual(self.converter.convert("em"), "झ")
        # km should become फ (प + m = फ)
        self.assertEqual(self.converter.convert("km"), "फ")

    def test_complex_words(self):
        """Test complex words with multiple contextual rules"""
        # Test word with reph and matras
        # This would need actual Preeti text examples
        pass

    def test_duplicate_removal(self):
        """Test that duplicate matras are removed"""
        # The post-rules should remove duplicate matras
        # This is handled automatically by post-processing
        pass

    def test_vowel_combinations(self):
        """Test vowel sign combinations"""
        # cf] should become आे then ओ (अ + ा + े = ओ)
        self.assertEqual(self.converter.convert("cf]"), "ओ")
        # cf should become आ (अ + ा = आ)
        self.assertEqual(self.converter.convert("cf"), "आ")


if __name__ == "__main__":
    unittest.main()
