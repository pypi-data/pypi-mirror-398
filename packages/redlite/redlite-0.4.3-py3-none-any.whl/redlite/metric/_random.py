from .. import NamedMetric
import random


class RandomMetric(NamedMetric):
    """
    Useless metric that produces random score. May be handy for testing.
    """

    def __init__(self):
        super().__init__("random", lambda x, y: random.random())
