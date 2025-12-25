from ... import MissingDependencyError, NamedMetric

try:
    from nltk.tokenize import word_tokenize
    from nltk.translate.bleu_score import sentence_bleu
except ImportError as err:
    raise MissingDependencyError("Please install nltk package") from err


class BleuMetric(NamedMetric):
    """
    Computes sentence-level BLEU metric.

    - **bleu_order** (`int`): Use `1` for BLEU-1 (default), or `4` for BLEU-4.
    """

    def __init__(self, bleu_order=1):
        if not (1 <= bleu_order <= 4):
            raise ValueError("bleu_order can only be 1, 2, 3, or 4")
        self._weights = [0, 0, 0, 0]
        self._weights[bleu_order - 1] = 1

        super().__init__(f"bleu-{bleu_order}", self.__engine)

    def __engine(self, expected: str, actual: str) -> float:
        return sentence_bleu([word_tokenize(expected)], word_tokenize(actual), weights=self._weights)


class BleuCJKMetric(NamedMetric):
    """
    Computes sentence-level BLEU metric for CJK languages (uses character-level tokenizer).

    - **bleu_order** (`int`): Use `1` for BLEU-1 (default), or `4` for BLEU-4.
    """

    def __init__(self, bleu_order=1):
        if not (1 <= bleu_order <= 4):
            raise ValueError("bleu_order can only be 1, 2, 3, or 4")
        self._weights = [0, 0, 0, 0]
        self._weights[bleu_order - 1] = 1

        super().__init__(f"cjk-bleu-{bleu_order}", self.__engine)

    def __engine(self, expected: str, actual: str) -> float:
        return sentence_bleu([_char_tokenize(expected)], _char_tokenize(actual), weights=self._weights)


def _char_tokenize(text):
    """For CJK languages just split on every character"""
    return list(text)
