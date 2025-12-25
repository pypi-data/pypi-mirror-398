from redlite import load_dataset, DatasetItem, NamedDataset
from redlite.metric import MatchMetric
from typing import cast

__all__ = ["dataset", "metric"]

PROMPT = "Solve the following math problem. Make sure to put the answer (and only answer) inside \\boxed{}."


def transform(item: dict) -> DatasetItem:
    expected = str(item["answer"])
    content = PROMPT + "\n\n" + item["problem"]
    id_ = f"{item['id']}"
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


class AimeDataset(NamedDataset):

    def __init__(self):
        self._dataset = load_dataset("hf:HuggingFaceH4/aime_2024", split="train", transform=transform)
        self.name = "aime24"
        self.labels = self._dataset.labels
        self.split = self._dataset.split

    def __len__(self) -> int:
        return len(self._dataset)

    def __iter__(self):
        yield from self._dataset


dataset = AimeDataset()

metric = MatchMetric()
