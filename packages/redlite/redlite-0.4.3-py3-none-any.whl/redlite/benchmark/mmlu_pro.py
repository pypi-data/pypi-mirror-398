from redlite import load_dataset, NamedMetric
from .._core import DatasetItem, Message
from typing import Any
import re

__all__ = ["dataset", "metric"]


NEMOTRON_PROMPT_TEMPLATE = """Answer the following multiple choice question. \
The last line of your response should be in the following format: \
'Answer: \\boxed{{A/B/C/D/E/F/G/H/I/J}}' (e.g. 'Answer: \\boxed{{A}}').

{problem}"""

OPTION_LABELS = "ABCDEFGHIJ"  # at most 10 multiple-choice options in MMLU Pro


class MMLUProTransform:

    def __init__(self, *, prompt_template: str):
        self.prompt_template = prompt_template

    def __call__(self, x: dict[str, Any]) -> DatasetItem | dict:
        id_ = f"{x['question_id']:07d}"
        options = x["options"]
        problem = x["question"] + "\n\n" + "\n".join([f"{OPTION_LABELS[i]}) {opt}" for i, opt in enumerate(options)])
        content = self.prompt_template.format(problem=problem)
        messages: list[Message] = [{"role": "user", "content": content}]
        return {
            "id": id_,
            "messages": messages,
            "expected": x["answer"],
            "raw": x,
        }


transform = MMLUProTransform(prompt_template=NEMOTRON_PROMPT_TEMPLATE)
dataset = load_dataset("hf:TIGER-Lab/MMLU-Pro", split="test", transform=transform)


class MMLUMetric(NamedMetric):
    def __init__(self):
        self.re = re.compile(r"answer:\s*\\boxed\{([A-J])\}", re.IGNORECASE)
        super().__init__(name="mmlu", engine=self.__engine)

    def __engine(self, expected: str, actual: str) -> float:
        mtc = re.search(self.re, actual)
        if mtc is None:
            return 0.0
        actual = mtc.group(1)
        if actual == expected:
            return 1.0
        else:
            return 0.0


metric = MMLUMetric()
