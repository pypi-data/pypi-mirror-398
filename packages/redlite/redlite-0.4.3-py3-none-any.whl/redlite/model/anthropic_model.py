from .. import NamedModel, MissingDependencyError
from .._util import object_digest

try:
    from anthropic import Anthropic, NOT_GIVEN, NotGiven
except ImportError as err:
    raise MissingDependencyError("Please install anthropic library") from err


class AnthropicModel(NamedModel):
    """
    Model that calls Anthropic Completion API.

    - **model** (`str`): Name of the Anthropic model. Default is `"claude-3-opus-20240229"`
    - **max_tokens** (`int`): maximum number of tokens
    - **thinking** (`dict`): optional config for thinking, for example `{'type': 'enabled', 'budget_tokens': 2048}`.
        Not all Anthropic models support thinking.
    - **streaming**: (`bool`): whether to use streaming Anthropic API. Default is `False`. You may need to enable
        streaming if thinking is enabled and thinking budget is large. Non-streaming Anthropic API does not support
        long thinking times.
    - **api_key** (`str | None`): Anthropic API key
    - **args**: Keyword arguments to be passed as-is to the Anthropic client. \
        See https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/_client.py#L68
    """

    def __init__(
        self,
        model="claude-3-opus-20240229",
        max_tokens: int = 1024,
        thinking: dict | NotGiven = NOT_GIVEN,
        streaming=False,
        api_key: str | None = None,
        **args,
    ):
        self.model = model
        self.client = Anthropic(api_key=api_key, **args)
        self.max_tokens = max_tokens
        self._streaming = streaming

        name = "anthropic"
        if len(args) > 0 or thinking is not NOT_GIVEN:
            signature = {**args}
            if thinking is not NOT_GIVEN:
                signature["thinking"] = thinking
            name = f"anthropic-{object_digest(signature)[:6]}"
        self._thinking = thinking

        super().__init__(f"{name}-{model}", self.__chat)

    def __chat(self, messages: list) -> str:
        system = NOT_GIVEN
        if messages[0]["role"] == "system":
            system = messages[0]["content"]
            messages = messages[1:]

        if self._streaming:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=messages,
                system=system,  # type: ignore[arg-type]
                thinking=self._thinking,  # type: ignore[arg-type]
            ) as stream:
                for event in stream:
                    if event.type == "message_stop":
                        assert event.message.content[-1].type == "text"
                        return event.message.content[-1].text
        else:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=messages,
                system=system,
                thinking=self._thinking,  # type: ignore[arg-type]
            )

            assert response.type == "message"
            assert response.role == "assistant"

            if response.stop_reason == "refusal":
                return "I refuse to answer this question."

            assert len(response.content) > 0
            assert response.content[-1].type == "text"

            return response.content[-1].text

        return ""  # not reached
