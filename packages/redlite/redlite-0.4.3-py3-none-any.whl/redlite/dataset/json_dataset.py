import json
from typing import Literal
from collections.abc import Iterator
from .memory_dataset import MemoryDataset, DatasetItem


class JSONDataset(MemoryDataset):
    """
    Dataset from a local JSONL file.

    Each line of the dataset file must be a `DatasetItem` serialized to JSON representation.
    File must use UTF-8 encoding. There should be no BOM-markers (some Microsoft tools produce those).

    - **path** (`str`): Location of JSONL file.
    - **name** (`str`): Dataset name.
    - **split** (`str`): Dataset split.
    - **labels** (`dict[str, str]`): Labels.
    """

    def __init__(self, *, path: str, name: str, split: Literal["test", "train"], labels: dict[str, str] | None = None):
        super().__init__(
            data=_read_jsonl(path),
            name=name,
            split=split,
            labels=labels,
        )


def _read_jsonl(path) -> Iterator[DatasetItem]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)
