import abc
from collections.abc import Callable, Iterable, Sized
from typing import TypedDict, Literal
import logging


log = logging.getLogger("redlite")
"""Logger for the redlite package."""


class Message(TypedDict):
    """
    Message.

    A plain dict with two keys:

    - **role** (`str`): one of `"system"`, `"user"`, or `"assistant"`.
    - **content** (`str`): message content.
    """

    role: Literal["system", "user", "assistant"]
    content: str


def system_message(content: str) -> Message:
    """
    Returns message with `role="system"` from the `content` string.
    """
    return {"role": "system", "content": content}


def user_message(content: str) -> Message:
    """
    Returns message with `role="user"` from the `content` string.
    """
    return {"role": "user", "content": content}


def assistant_message(content: str) -> Message:
    """
    Returns message with `role="assistant"` from the `content` string.
    """
    return {"role": "assistant", "content": content}


class DatasetItem(TypedDict):
    """
    Dataset item.

    A plain dict with three required keys:

    - **id** (`str`): Uniqie id of this item. Uniqueness is across all splits of the dataset.
    - **messages** (`list[Message]`): Conversation messages. Last message is expected to have `role="user"`.
    - **expected** (`str`): Expected response.
    """

    id: str
    messages: list[Message]
    expected: str


class NamedDataset(Sized, Iterable[DatasetItem]):
    """
    Dataset abstraction.

    Dataset is an `Iterable[DatasetItem]`, and has the following attributes:

    - **name** (str): Dataset name
    - **split** (str): Data split ("test" or "train")
    - **labels** (dict): Dictionary of dataset labels
    """

    name: str
    split: Literal["test", "train"]
    labels: dict[str, str]


class NamedMetric:
    """
    Metric abstraction.

    Metric is a `Callable` that have `name` attribute.

    - **name** (str): Metric name
    - **engine**: Function that will be called to compute the score.

    Sample usage:
    ```python

    def engine(expected: str, actual: str) -> float:
        if expected == actual:
            return 1.0
        return 0.0

    hit_metric = NamedMetric('hit_metric', engine)
    ```
    """

    name: str

    def __init__(self, name: str, engine: Callable[[str, str], float]):
        self.name = name
        self._engine = engine

    def __call__(self, expected: str, actual: str) -> float:
        return self._engine(expected, actual)


class NamedModel:
    """
    Model abstraction.

    Model is a `Callable` object that has `name` attribute.
    Given an input `Messages` it should return the response string.

    - **name** (`str`): Name of the model.
    - **engine** (`Callable[[list[Messages]], str]`): A function that computes model prediction from messages.

    Sample usage:

    ```python
    def parrot_engine(messages: list[Message]) -> str:
        return messages[-1]['content']

    parrot_model = NamedModel('parrot', parrot_engine)
    ```
    """

    name: str

    def __init__(self, name: str, engine: Callable[[list[Message]], str]):
        self.name = name
        self._engine = engine

    def __call__(self, conversation: list[Message]) -> str:
        return self._engine(conversation)


class Storage(abc.ABC):
    def __init__(self, name: str):
        self.name = name

    @abc.abstractmethod
    def save(self, item: DatasetItem, response: str, score: float):
        pass

    @abc.abstractmethod
    def save_meta(self, **kw):
        pass


class MissingDependencyError(RuntimeError):
    """
    Raised when a missing optional dependency is detected.
    """


class ScoreSummary(TypedDict):
    """
    Score summary.
    """

    count: int
    mean: float
    min: float
    max: float


class Run(TypedDict):
    """
    Run metadata
    """

    run: str
    """Name of the run"""

    dataset: str
    """Dataset name"""

    split: str
    """Dataset split"""

    dataset_labels: dict[str, str]
    """Labels"""

    data_digest: str
    """SHA digest of all records that were served in this run"""

    metric: str
    """Name of the metric"""

    model: str
    """Model name"""

    max_samples: int
    """Samples limit"""

    started: str
    """ISO UTC timestamp when run was started"""

    completed: str
    """ISO UTC timestamp when run was completed"""

    duration: float
    """Run duration in seconds"""

    score_summary: ScoreSummary
    """Score aggregate"""
