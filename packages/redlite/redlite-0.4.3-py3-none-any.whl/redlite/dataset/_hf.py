from collections.abc import Iterator
from typing import Literal
from .._core import NamedDataset, DatasetItem, MissingDependencyError


try:
    from datasets import load_dataset
    from huggingface_hub import DatasetCard
except ImportError as err:
    raise MissingDependencyError("Please install datasets library") from err


class HFDataset(NamedDataset):
    """
    Dataset hosted on HuggingFace hub.

    - **hf_name** (`str`): HuggingFace name of the dataset.
            For example, `"innodatalabs/rt-factcc"`.
    - **split** (`str`): Which split to load.
    - **extra** (dict[str,str]): Extra parameters passed to `datasets.load_dataset`.

    """

    def __init__(self, hf_name: str, split: Literal["test", "train"] = "test", **extra):
        super().__init__()
        self.name = "hf:" + hf_name
        self._dataset = load_dataset(hf_name, **extra)
        self._card = DatasetCard.load(hf_name)
        self.labels = getattr(self._card.data, "labels", {})
        self.split = split

    def __iter__(self) -> Iterator[DatasetItem]:
        yield from self._dataset[self.split]

    def __len__(self):
        return self._dataset[self.split].info.splits[self.split].num_examples

    @classmethod
    def load(cls, name: str, split: Literal["test", "train"] = "test", **extra) -> "NamedDataset":
        if not name.startswith("hf:"):
            raise ValueError(f"This method can only load from HF dataset hub, but requested {name}")
        extra = {k[2:] if k.startswith("__") else k: v for k, v in extra.items()}
        return cls(name[3:], split, **extra)
