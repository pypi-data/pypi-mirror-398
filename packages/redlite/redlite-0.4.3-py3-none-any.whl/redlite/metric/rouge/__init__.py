from ... import NamedMetric, MissingDependencyError
from typing import Literal

try:
    from rouge_score import rouge_scorer
except ImportError as err:
    raise MissingDependencyError("Please install rouge-score package") from err


class RougeMetric(NamedMetric):
    """Computes sentence-level ROUGE metric.

    - **rouge_type** (`str`): Rouge type: `"rouge1"`, `"rouge2"`, or `"rougeL"`.
    - **use_stemmer** (`bool`): Default `True`.

    """

    def __init__(self, *, rouge_type: Literal["rouge1", "rouge2", "rougeL"], use_stemmer=True):
        self._rouge_type = rouge_type
        self._use_stemmer = use_stemmer

        self._scorer = rouge_scorer.RougeScorer([rouge_type], use_stemmer=use_stemmer)

        name = f"{rouge_type}"
        if use_stemmer:
            name += "-stemmer"

        super().__init__(name, self.__engine)

    def __engine(self, expected: str, actual: str) -> float:
        scores = self._scorer.score(expected, actual)
        return scores[self._rouge_type].fmeasure


def rouge_score(gold: str, pred: str, rouge_type: str, scorer: rouge_scorer.RougeScorer) -> float:
    scores = scorer.score(gold, pred)
    return scores[rouge_type].fmeasure


class RougeCJKMetric(NamedMetric):
    """Computes sentence-level ROUGE metric for CJK texts.

    - **rouge_type** (`str`): Rouge type: `"rouge1"`, `"rouge2"`, or `"rougeL"`.
    """

    def __init__(self, *, rouge_type: Literal["rouge1", "rouge2", "rougeL"]):
        self._rouge_type = rouge_type

        self._scorer = rouge_scorer.RougeScorer([rouge_type], use_stemmer=False, tokenizer=_CharTokenizer())

        super().__init__(f"cjk-{rouge_type}", self.__engine)

    def __engine(self, expected: str, actual: str) -> float:
        scores = self._scorer.score(expected, actual)
        return scores[self._rouge_type].fmeasure


class _CharTokenizer:
    """For CJK languages just split on every character"""

    def tokenize(self, text):
        return list(text)
