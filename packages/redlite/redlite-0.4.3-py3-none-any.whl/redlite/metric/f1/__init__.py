from ... import MissingDependencyError, NamedMetric
from ..util import normalize_string

try:
    from nltk.metrics.scores import f_measure
    from nltk.tokenize import word_tokenize
except ImportError as err:
    raise MissingDependencyError("Please install nltk package") from err


class F1Metric(NamedMetric):
    """
    Metric that checks that the actual resonse equals the expected string, using F1 measure on token (word) set.
    """

    def __init__(self):
        super().__init__("f1", self.__engine)

    def __engine(self, expected: str, actual: str) -> float:
        expected = normalize_string(
            expected,
            to_lower=True,
            strip_articles=True,
            strip_punct=True,
            normalize_whitespace=True,
        )
        actual = normalize_string(
            actual,
            to_lower=True,
            strip_articles=True,
            strip_punct=True,
            normalize_whitespace=True,
        )

        expected_set = set(word_tokenize(expected))
        actual_set = set(word_tokenize(actual))

        ret = f_measure(expected_set, actual_set)
        if ret is None:
            return 0.0
        return ret
