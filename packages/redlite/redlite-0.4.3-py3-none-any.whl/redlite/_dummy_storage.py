from ._core import Storage, DatasetItem


class DummyStorage(Storage):
    def __init__(self):
        super().__init__("dummy")

    def save_meta(self, **kaw: dict) -> None:
        pass

    def save(self, item: DatasetItem, actual: str, score: float) -> None:
        pass
