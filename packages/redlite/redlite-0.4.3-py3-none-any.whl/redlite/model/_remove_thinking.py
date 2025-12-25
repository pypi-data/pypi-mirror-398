import re
from .._core import NamedModel, Message, log


class RemoveThinking(NamedModel):
    """
    Wraps a model and removes thinking text block from the model output (if any).
    Useful if underlying model uses "reasoning" and includes "thinking trace"
    into its answer.

    - **model** (`NamedModel`): the model to wrap.
    """

    def __init__(self, model: NamedModel):
        self.model = model
        super().__init__(f"remove-thinking-{model.name}", self.__engine)

    def __engine(self, messages: list[Message]) -> str:
        return _remove_thinking_trace(self.model(messages))


_RE_THINKING_TRACE = {
    "<answer>": r"<answer>(.*)</answer>",
    "openai-oss": r"<\|start\|>assistant<\|channel\|>final<\|message\|>(.*)<\|return\|>$",
    "<thinking>": r"</thinking>(.*)$",
    "<think>": r"</think>(.*)$",
}


def _remove_thinking_trace(content: str) -> str:
    for pattern in _RE_THINKING_TRACE.values():
        mtc = re.search(pattern, content, flags=re.DOTALL | re.IGNORECASE)
        if mtc is not None:
            return mtc.group(1).strip()
    log.warning(f"Warning: could not remove thinking trace from content: {content}")
    return content
