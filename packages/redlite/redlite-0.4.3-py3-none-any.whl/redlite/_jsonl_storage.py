import os
import json
import contextlib
from collections.abc import Iterator
from ._core import Storage, DatasetItem


class JsonlStorage(Storage):
    def __init__(self, name: str, folder: str, fd):
        super().__init__(name)
        self.folder = folder
        self.fd = fd

    def save_meta(self, **kaw: dict) -> None:
        with open(f"{self.folder}/meta.json", "w", encoding="utf-8") as f:
            json.dump(kaw, f, ensure_ascii=False, indent=2)

    def save(self, item: DatasetItem, actual: str, score: float) -> None:
        self.fd.write(
            json.dumps(
                {
                    **item,
                    "actual": actual,
                    "score": score,
                },
                ensure_ascii=False,
            )
        )
        self.fd.write("\n")

    @classmethod
    @contextlib.contextmanager
    def open(cls, name: str, folder: str) -> Iterator[Storage]:
        os.makedirs(folder, exist_ok=True)
        with open(f"{folder}/data.jsonl", "w", encoding="utf-8") as f:
            yield cls(name, folder, f)
