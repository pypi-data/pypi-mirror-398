from typing import Literal
from .. import NamedMetric
from .util import normalize_string


class MatchMetric(NamedMetric):
    """
    Metric that checks that the actual response matches expected string.

    For example, the expected response could be "Correct", but model answers
    "Correct, because blah blah blah...". To give model full marks for longer and
    verbose answer, use this metric.

    This metric matches words, not strings. This means that, for example, when `strategy="prefix"`
    and `expected="correct"` and `actual="correctness is when things work right"`, this metric
    will score `0.0`.

    This metric normalizes whitespace in both `expected` and `actual`, and strips any leading or trailing
    space there.

    - **ignore_case** (`bool`, optional) - when set to `True` will ignore text case. Deafult is `False`.

    - **ignore_punct** (`bool`, optional) - when set to `True` punctuation symbols will be ignored.
            Default is `False`.

    - **strategy** (`Literal["exact", "prefix", "contains"]`, optional) - determines how strings are matched.

        * `"exact"`: matches if expected and actual responses are the same
        * `"prefix"`: matches if actual response starts with the expected words
        * `"contains"`: matches if expected sequence of words is found found anywhere in the actual response

        Default is `"exact"`.
    """

    def __init__(
        self,
        ignore_case=False,
        ignore_punct=False,
        strategy: Literal["exact", "contains", "prefix"] = "exact",
    ):
        if strategy not in ("prefix", "contains", "exact"):
            raise ValueError(
                f"Invalid value of strategy parameter. Expect one of ('exact', 'prefix', 'contains'), got '{strategy}'"
            )
        name = f"match-{strategy}"
        if ignore_case:
            name = name + "-ignore-case"
        if ignore_punct:
            name = name + "-ignore-punct"

        self.ignore_case = ignore_case
        self.ignore_punct = ignore_punct
        self.match = strategy

        super().__init__(name, self.__engine)

    def __engine(self, expected: str, actual: str) -> float:
        expected = normalize_string(
            expected,
            to_lower=self.ignore_case,
            strip_punct=self.ignore_punct,
            normalize_whitespace=True,
        )
        actual = normalize_string(
            actual,
            to_lower=self.ignore_case,
            strip_punct=self.ignore_punct,
            normalize_whitespace=True,
        )

        guarded_expected = _to_string_with_word_guards(expected)
        guarded_actual = _to_string_with_word_guards(actual)
        if self.match == "contains":
            return 1.0 if guarded_expected in guarded_actual else 0.0
        elif self.match == "prefix":
            return 1.0 if guarded_actual.startswith(guarded_expected) else 0.0
        elif self.match == "exact":
            return 1.0 if guarded_actual == guarded_expected else 0.0
        else:
            assert False  # not reached


def _to_string_with_word_guards(string):
    wg = "\x01"  # word guard (something that should never happen in the input string)
    assert wg not in string

    return wg + wg.join(string.split()) + wg
