import random
import re
from redlite import DatasetItem, NamedMetric, load_dataset, NamedDataset
from redlite.dataset.json_dataset import JSONDataset
import os
import json


__all__ = ["get_dataset", "metric"]

OPTION_LABELS = "ABCD"  # at most 4 multiple-choice options in GPQA

NEMO_PROMPT_TEMPLATE = """\
Answer the following multiple choice question. \
The last line of your response should be in the following format: \
'Answer: \\boxed{{A/B/C/D}}' (e.g. 'Answer: \\boxed{{A}}').

{problem}"""


def normalize(text: str | None) -> str:
    if text is None:
        return ""
    text = text.strip().replace(" [title]", ". ")
    return re.sub(r"\s+", " ", text)


def transform(datum: dict) -> DatasetItem | dict:
    choices = [
        normalize(datum["Correct Answer"]),
        normalize(datum["Incorrect Answer 1"]),
        normalize(datum["Incorrect Answer 2"]),
        normalize(datum["Incorrect Answer 3"]),
    ]

    order = [0, 1, 2, 3]
    random.shuffle(order)

    expected = OPTION_LABELS[order.index(0)]
    options = "\n".join(f"{OPTION_LABELS[i]}) {choices[order[i]]}" for i in range(4))

    problem = datum["Question"].strip("\n") + "\n\n" + options

    content = NEMO_PROMPT_TEMPLATE.format(problem=problem)
    messages = [{"role": "user", "content": content}]
    id_ = datum["Record ID"]

    return {
        "id": id_,
        "messages": messages,
        "expected": expected,
        "raw": datum,
    }


DATASET_DIR = os.path.expanduser("~/.cache/redlite-datasets/gpqa")
CONFIGS = ["diamond", "main", "extended"]


def generate_local_data_if_not_there(config):
    if os.path.isfile(f"{DATASET_DIR}/{config}.jsonl"):
        return
    os.makedirs(DATASET_DIR, exist_ok=True)
    print(f"Generating local data for {config}...")
    dataset = load_dataset("hf:Idavidrein/gpqa", __name=f"gpqa_{config}", split="train", transform=transform)
    with open(f"{DATASET_DIR}/{config}.jsonl", "w", encoding="utf-8") as f:
        for x in dataset:
            f.write(json.dumps(x) + "\n")
    print(f"Done generating local data for {config}.")


class GPQADataset(NamedDataset):

    def __init__(self, config: str):
        if config not in CONFIGS:
            raise ValueError(f"Unknown config. Supported configs are: {CONFIGS}")
        generate_local_data_if_not_there(config)
        self._dataset = JSONDataset(path=f"{DATASET_DIR}/{config}.jsonl", name=f"gpqa_{config}", split="train")
        self.name = f"gpqa_{config}"
        self.labels = self._dataset.labels
        self.split = self._dataset.split

    def __len__(self) -> int:
        return len(self._dataset)

    def __iter__(self):
        yield from self._dataset


def get_dataset(config) -> NamedDataset:
    return GPQADataset(config)


_RE = re.compile(r"\\boxed\{([A-D])\}", flags=re.IGNORECASE)


def score(expected: str, actual: str) -> float:
    mtc = _RE.search(actual)
    if mtc and mtc.group(1) == expected:
        return 1.0
    return 0.0


metric = NamedMetric("gpqa-boxed", score)
