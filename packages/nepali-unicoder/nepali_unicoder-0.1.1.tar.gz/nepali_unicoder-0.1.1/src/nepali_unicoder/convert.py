from nepali_unicoder.engine import Engine


class Converter:
    """
    Wrapper around Engine for backward compatibility.
    """

    def __init__(self, mode: str = "roman"):
        self.engine = Engine(mode=mode)

    def convert(self, text: str) -> str:
        return self.engine.transliterate(text)
