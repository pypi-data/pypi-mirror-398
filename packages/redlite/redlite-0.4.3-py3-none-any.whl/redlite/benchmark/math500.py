from redlite import load_dataset, DatasetItem, NamedDataset
from redlite.metric.math import BoxedMathMetric
from typing import cast

__all__ = ["dataset", "metric"]

PROMPT = "Solve the following math problem. Make sure to put the answer (and only answer) inside \\boxed{}."


def transform(item: dict) -> DatasetItem:
    id_ = item["unique_id"]
    expected = item["answer"]
    content = PROMPT + "\n\n" + item["problem"]
    messages = [{"role": "user", "content": content}]
    return cast(
        DatasetItem,
        {
            "id": id_,
            "messages": messages,
            "expected": expected,
            "raw": item,
        },
    )


class Math500Dataset(NamedDataset):

    def __init__(self):
        self._dataset = load_dataset("hf:HuggingFaceH4/MATH-500", split="test", transform=transform)
        self.name = "math500"
        self.labels = self._dataset.labels
        self.split = self._dataset.split

    def __len__(self) -> int:
        return len(self._dataset)

    def __iter__(self):
        yield from self._dataset


dataset = Math500Dataset()

metric = BoxedMathMetric()
