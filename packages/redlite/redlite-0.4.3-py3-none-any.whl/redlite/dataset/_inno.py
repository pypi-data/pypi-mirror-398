from typing import Literal
from .._core import NamedDataset


def load_dataset(name: str, split: Literal["test", "train"]) -> NamedDataset:
    if not name.startswith("inno:"):
        raise ValueError(f"The method can only load from INNO dataset hub, but requested {name}")
    raise NotImplementedError("Innodata Dataset Hub")
