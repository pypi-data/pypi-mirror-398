from .._core import NamedMetric


class BestOfMetric(NamedMetric):
    """
    Computes several metrics and chooses the best score.

    Useful when we expect a rejection: we can use `MatchMetric` to detect rejection
    and if rejection is not expected, we compute semantic closeness with BLEU or ROUGE.

    - **metrics**
    """

    def __init__(self, *metrics: NamedMetric):
        if len(metrics) < 1:
            raise ValueError("Need at least one metric parameter")

        self.metrics = sorted(metrics, key=lambda m: m.name)
        name = "best-of-" + "-".join(m.name for m in self.metrics)
        super().__init__(name, self.__engine)

    def __engine(self, expected, actual) -> float:
        scores = [m(expected, actual) for m in self.metrics]
        return max(scores)
