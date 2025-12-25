from redlite import NamedDataset, DatasetItem
from redlite.metric.livecodebench import LiveCodeBenchMetric
from datasets import load_dataset
from typing import cast
import json
import os


__all__ = ["get_dataset", "get_metric"]

FORMATTING_MESSAGE_WITH_STARTER_CODE = ""
FORMATTING_WITHOUT_STARTER_CODE = ""


PROMPT_WITH_STARTER_CODE = """\
{question_content}

You will use the following starter code to write the solution to the problem and enclose your code within delimiters.
```python
{starter_code}
```

"""

PROMPT_WITHOUT_STARTER_CODE = """\
{question_content}

Read the inputs from stdin solve the problem and write the answer to stdout \
do not directly test on the sample inputs). Enclose your code within delimiters as follows. \
Ensure that when the python program runs, it reads the inputs, runs the algorithm and writes output to STDOUT.

```python
# YOUR CODE HERE
```

"""


def transform(item: dict) -> DatasetItem:
    question_content = item["question_content"].strip().replace("    ", "\t")
    starter_code = item["starter_code"].strip().replace("    ", "\t")
    if starter_code:
        content = PROMPT_WITH_STARTER_CODE.format(question_content=question_content, starter_code=starter_code)
    else:
        content = PROMPT_WITHOUT_STARTER_CODE.format(question_content=question_content)

    id_ = str(item["question_id"])
    public_test_cases = json.loads(item["public_test_cases"])
    testtypes = set(x["testtype"] for x in public_test_cases)
    assert len(testtypes) == 1, f"Expected only one testtype per question, but got {testtypes} for question_id {id_}"
    if list(testtypes)[0] == "functional":
        func_name = json.loads(item["metadata"])["func_name"]
        expected = {
            "type": "function",
            "name": func_name,
            "tests": public_test_cases,
        }
    elif list(testtypes)[0] == "stdin":
        expected = {
            "type": "stdin",
            "tests": public_test_cases,
        }

    messages = [{"role": "user", "content": content}]
    return cast(
        DatasetItem,
        {
            "id": id_,
            "messages": messages,
            "expected": json.dumps(expected),
        },
    )


DATASET_DIR = os.path.expanduser("~/.cache/redlite-datasets/livecodebench")
CONFIGS = {
    "test_v5_2407_2412": {
        "version_tag": "release_v5",
        "start_date": "2024-07",
        "end_date": "2024-12",
        "count": 315,
    },
    "test_v5_2408_2502": {
        "version_tag": "release_v5",
        "start_date": "2024-08",
        "end_date": "2025-02",
        "count": 279,
    },
    "test_v5_2410_2502": {
        "version_tag": "release_v5",
        "start_date": "2024-10",
        "end_date": "2025-02",
        "count": 166,
    },
    "test_v6_2408_2505": {
        "version_tag": "release_v6",
        "start_date": "2024-08",
        "end_date": "2025-05",
        "count": 454,
    },
}


def prepare_data(config, outfile):
    print(f"Preparing data for config: {config} as {outfile}")
    dataset = load_dataset(
        "lighteval/code_generation_lite",
        name=config["version_tag"],
        split="test",
    )
    start_date = config["start_date"]
    end_date = config["end_date"]

    os.makedirs(DATASET_DIR, exist_ok=True)
    with open(outfile, "w", encoding="utf-8") as f:
        count = 0
        for item in dataset:
            input_date = item["contest_date"][:7]
            if start_date <= input_date <= end_date:
                f.write(json.dumps(transform(item)) + "\n")
                count += 1
        if count != config["count"]:
            raise RuntimeError(f"Expected count {config['count']} but got {count} for config {config}")


class LiveCodeBenchDataset(NamedDataset):

    def __init__(self, config: str):
        if config not in CONFIGS:
            raise ValueError(f"Unknown config. Supported configs are: {list(CONFIGS.keys())}")
        c = CONFIGS[config]
        self._filename = f"{DATASET_DIR}/{config}.jsonl"
        self._len = cast(int, c["count"])
        if not os.path.isfile(self._filename):
            prepare_data(c, f"{DATASET_DIR}/{config}.jsonl")
        self.name = f"livecodebench/code_generation_lite:{config}"
        self.labels = {}
        self.split = "test"

    def __len__(self) -> int:
        return self._len

    def __iter__(self):
        with open(self._filename, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                yield item


def get_dataset(config="test_v5_2408_2502") -> NamedDataset:
    return LiveCodeBenchDataset(config)


def get_metric(endpoint: str = "http://localhost:8000") -> LiveCodeBenchMetric:
    return LiveCodeBenchMetric(endpoint)
