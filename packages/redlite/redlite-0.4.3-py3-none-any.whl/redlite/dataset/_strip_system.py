from collections.abc import Iterator
from .._core import NamedDataset, DatasetItem


class StripSystemDataset(NamedDataset):
    """
    Wraps dataset and removes System messages.
    """

    def __init__(self, dataset: NamedDataset):
        self.__dataset = dataset

        self.labels = dataset.labels
        self.split = dataset.split
        self.name = f"{dataset.name}-strip-system"

    def __len__(self) -> int:
        return len(self.__dataset)

    def __iter__(self) -> Iterator[DatasetItem]:
        for item in self.__dataset:
            messages = item["messages"]
            if messages[0]["role"] == "system":
                messages = messages[1:]
                item["messages"] = messages  # WARN: updates in-place
            yield item
