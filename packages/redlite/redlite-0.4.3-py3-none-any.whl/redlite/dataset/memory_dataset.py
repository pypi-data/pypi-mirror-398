from typing import Literal
from collections.abc import Iterator
from .._core import NamedDataset, DatasetItem
from ._load import ValidatingDataset


class MemoryDataset(ValidatingDataset):
    """
    Dataset from an iterator returning `DatasetItem`s.

    Data iterator will be greedily executed and all items held in an array.

    - **data** (Iterator[DatasetItem]): Iterator returning data points.
    - **name** (`str`): Dataset name.
    - **split** (`str`): Dataset split. Defaults to `"test"`.
    - **labels** (`dict[str, str]`): Labels. Defaults to empty dict.
    """

    def __init__(
        self,
        *,
        data: Iterator[DatasetItem],
        name: str,
        split: Literal["test", "train"] = "test",
        labels: dict[str, str] | None = None,
    ):
        super().__init__(_MemoryDataset(data=data, name=name, split=split, labels=labels))


class _MemoryDataset(NamedDataset):
    def __init__(
        self,
        *,
        data: Iterator[DatasetItem],
        name: str,
        split: Literal["test", "train"] = "test",
        labels: dict[str, str] | None = None,
    ):
        self.name = name
        self.split = split
        self.labels = labels if labels is not None else {}

        self._data = [item for item in data]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[DatasetItem]:
        yield from self._data
