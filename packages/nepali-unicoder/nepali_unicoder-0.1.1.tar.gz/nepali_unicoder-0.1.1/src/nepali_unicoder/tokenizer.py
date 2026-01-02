from dataclasses import dataclass
from typing import List


@dataclass
class Token:
    value: str
    type: str  # 'ROMAN', 'BLOCK', 'PUNCTUATION', 'UNKNOWN', 'LITERAL', 'NUMBER'


class Tokenizer:
    def tokenize(self, text: str) -> List[Token]:
        """
        Split text into tokens.
        This simple tokenizer handles {blocks}, numbers, and treats everything else as ROMAN for now.
        """
        tokens = []
        i = 0
        n = len(text)

        while i < n:
            if text[i] == "{":
                # Check for escape {{
                if i + 1 < n and text[i + 1] == "{":
                    # Actually, if it's escaped, it should probably be treated as a literal '{' in the output.
                    tokens.append(Token(value="{", type="LITERAL"))
                    i += 2
                else:
                    # Start of block
                    j = i + 1
                    while j < n and text[j] != "}":
                        j += 1

                    if j < n:  # Found closing brace
                        content = text[i + 1 : j]
                        tokens.append(Token(value=content, type="BLOCK"))
                        i = j + 1
                    else:  # Unclosed brace, treat as literal
                        tokens.append(Token(value="{", type="LITERAL"))
                        i += 1
            elif text[i] == "}":
                # Unmatched closing brace, treat as literal
                tokens.append(Token(value="}", type="LITERAL"))
                i += 1
            elif text[i].isdigit():
                # Start of a number
                j = i
                while j < n and text[j].isdigit():
                    j += 1

                # Check for decimal part
                if j < n and text[j] == ".":
                    # Look ahead to see if there are digits after dot
                    if j + 1 < n and text[j + 1].isdigit():
                        j += 1  # Consume dot
                        while j < n and text[j].isdigit():
                            j += 1

                tokens.append(Token(value=text[i:j], type="NUMBER"))
                i = j
            else:
                # Accumulate Roman text
                j = i
                while j < n and text[j] not in "{}" and not text[j].isdigit():
                    j += 1
                tokens.append(Token(value=text[i:j], type="ROMAN"))
                i = j

        return tokens
