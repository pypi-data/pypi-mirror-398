PREETI_TO_UNICODE_MAPPING = {
    "mappings": {
        # Lowercase letters (a-z)
        "a": "ब",
        "b": "द",
        "c": "अ",
        "d": "म",
        "e": "भ",
        "f": "ा",
        "g": "न",
        "h": "ज",
        "i": "ष्",
        "j": "व",
        "k": "प",
        "l": "ि",
        "m": "m",
        "n": "ल",
        "o": "य",
        "p": "उ",
        "q": "त्र",
        "r": "च",
        "s": "क",
        "t": "त",
        "u": "ग",
        "v": "ख",
        "w": "ध",
        "x": "ह",
        "y": "थ",
        "z": "श",
        # Uppercase letters (A-Z)
        "A": "ब्",
        "B": "द्य",
        "C": "ऋ",
        "D": "म्",
        "E": "भ्",
        "F": "ँ",
        "G": "न्",
        "H": "ज्",
        "I": "क्ष्",
        "J": "व्",
        "K": "प्",
        "L": "ी",
        "M": "ः",
        "N": "ल्",
        "O": "इ",
        "P": "ए",
        "Q": "त्त",
        "R": "च्",
        "S": "क्",
        "T": "त्",
        "U": "ग्",
        "V": "ख्",
        "W": "ध्",
        "X": "ह्",
        "Y": "थ्",
        "Z": "श्",
        # Numbers (0-9)
        "0": "ण्",
        "1": "ज्ञ",
        "2": "द्द",
        "3": "घ",
        "4": "द्ध",
        "5": "छ",
        "6": "ट",
        "7": "ठ",
        "8": "ड",
        "9": "ढ",
        # Special characters (Shift + numbers)
        "!": "१",
        "@": "२",
        "#": "३",
        "$": "४",
        "%": "५",
        "^": "६",
        "&": "७",
        "*": "८",
        "(": "९",
        ")": "०",
        # Brackets and punctuation
        "[": "ृ",
        "]": "े",
        "{": "{",
        "}": "ै",
        "|": "्र",
        # Other special characters
        ";": "स",
        ":": "स्",
        "'": "ु",
        '"': "ू",
        ",": ",",
        ".": "।",
        "/": "र",
        "<": "?",
        ">": "श्र",
        "?": "रु",
        "\\": "्",
        "`": "ञ",
        "~": "ञ्",
        "_": ")",
        "-": "(",
        "=": ".",
        "+": "ं",
    },
    # Post-processing rules applied after character mapping
    # Format: [pattern, replacement] - applied in order using regex
    "post_rules": [
        # 1. Remove invalid combinations
        ["्ा", ""],  # halant + aa-kar is invalid
        # 2. Handle 'm' character contextually
        [
            r"(त्र|त्त)([^उभप]+?)m",
            r"\1m\2",
        ],  # preserve m position for certain combinations
        ["त्रm", "क्र"],  # त्र + m = क्र
        ["त्तm", "क्त"],  # त्त + m = क्त
        [r"([^उभप]+?)m", r"m\1"],  # move m before (except after उ, भ, प)
        ["उm", "ऊ"],  # उ + m = ऊ
        ["भm", "झ"],  # भ + m = झ
        ["पm", "फ"],  # प + m = फ
        # 3. Handle reph ({) contextually
        ["इ{", "ई"],  # इ + { = ई (special case)
        [r"ि((.्)*[^्])", r"\1ि"],  # move short i (ि) after consonant
        [r"(.[ािीुूृेैोौंःँ]*?){", r"{\1"],  # move { before matras
        [r"((.्)*){", r"{\1"],  # move { before halant sequences
        ["{", "र्"],  # finally convert { to reph (र्)
        # 4. Reorder matras (vowel signs) to correct positions
        [r"([ाीुूृेैोौंःँ]+?)(्(.्)*[^्])", r"\2\1"],  # move matras after halant+consonant
        [r"्([ाीुूृेैोौंःँ]+?)((.्)*[^्])", r"्\2\1"],  # reorder matras after halant
        # 5. Move anusvara and chandrabindu to end
        [r"([ंँ])([ािीुूृेैोौः]*)", r"\2\1"],  # move ं/ँ after other matras
        # 6. Remove duplicates
        ["ँँ", "ँ"],  # duplicate chandrabindu
        ["ंं", "ं"],  # duplicate anusvara
        ["ेे", "े"],  # duplicate e-matra
        ["ैै", "ै"],  # duplicate ai-matra
        ["ुु", "ु"],  # duplicate u-matra
        ["ूू", "ू"],  # duplicate uu-matra
        # 7. Handle visarga at start of line
        ["^ः", ":"],  # visarga at start should remain colon
        # 8. Special combinations
        ["टृ", "ट्ट"],  # ट + ृ = ट्ट
        # 9. Combine vowel signs with independent vowels
        ["ेा", "ाे"],  # reorder e-matra and aa-matra
        ["ैा", "ाै"],  # reorder ai-matra and aa-matra
        ["अाे", "ओ"],  # अ + ा + े = ओ
        ["अाै", "औ"],  # अ + ा + ै = औ
        ["अा", "आ"],  # अ + ा = आ
        ["एे", "ऐ"],  # ए + े = ऐ
        ["ाे", "ो"],  # ा + े = ो
        ["ाै", "ौ"],  # ा + ै = ौ
    ],
}


ROMAN_TO_UNICODE_RULES = {
    "consonants": {
        "k": "क",
        "kh": "ख",
        "g": "ग",
        "gh": "घ",
        "ng": "ङ",
        "ch": "च",
        "chh": "छ",
        "j": "ज",
        "jh": "झ",
        "ny": "ञ",
        "T": "ट",
        "Th": "ठ",
        "D": "ड",
        "Dh": "ढ",
        "N": "ण",
        "t": "त",
        "th": "थ",
        "d": "द",
        "dh": "ध",
        "n": "न",
        "p": "प",
        "ph": "फ",
        "f": "फ",
        "b": "ब",
        "bh": "भ",
        "m": "म",
        "y": "य",
        "r": "र",
        "l": "ल",
        "v": "व",
        "w": "व",
        "sh": "श",
        "Sh": "ष",
        "s": "स",
        "h": "ह",
        "ksh": "क्ष",
        "tra": "त्र",
        "gy": "ज्ञ",
        "shr": "श्र",
    },
    "vowels": {
        "a": "अ",
        "aa": "आ",
        "A": "आ",
        "i": "इ",
        "I": "इ",
        "ee": "ई",
        "ii": "ई",
        "u": "उ",
        "U": "उ",
        "oo": "ऊ",
        "uu": "ऊ",
        "Ri": "ऋ",
        "R": "ऋ",
        "Ree": "ॠ",
        "lRi": "ऌ",
        "e": "ए",
        "ai": "ऐ",
        "o": "ओ",
        "au": "औ",
    },
    "matras": {
        "a": "",
        "aa": "ा",
        "A": "ा",
        "i": "ि",
        "I": "ि",
        "ee": "ी",
        "ii": "ी",
        "u": "ु",
        "U": "ु",
        "oo": "ू",
        "uu": "ू",
        "Ri": "ृ",
        "R": "ृ",
        "Ree": "ॄ",
        "e": "े",
        "ai": "ै",
        "o": "ो",
        "au": "ौ",
    },
    "special": {
        "om": "ॐ",
        "Om": "ॐ",
        "aum": "ॐ",
        ".": "।",
        "..": "॥",
        "|": "।",
        "||": "॥",
        "M": "ं",
        "H": "ः",
        "~": "ँ",
    },
    "digits": {
        "0": "०",
        "1": "१",
        "2": "२",
        "3": "३",
        "4": "४",
        "5": "५",
        "6": "६",
        "7": "७",
        "8": "८",
        "9": "९",
    },
}
