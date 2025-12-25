from .. import NamedModel, MissingDependencyError
from .._util import object_digest

try:
    from openai import OpenAI
except ImportError as err:
    raise MissingDependencyError("Please install openai library") from err


class OpenAIModel(NamedModel):
    """
    Model that calls OpenAI Completion API.

    - **base_url** (`str`): Alternative API endpoint. Can be used to access services that
                            are compatible with OpenAI (e.g. NVIDIA research).
    - **model** (`str`): Name of the OpenAI model. Default is `"gpt-3.5-turbo"`.
    - **api_key** (`str`): OpenAI API key
    - **max_retries** (`int`): How many times to retry a failed request. Default is `2`.
    - **params**: (`dict[str,Any]`): Other parameters that will be passed on to the `OpenAI` as-is.
    """

    def __init__(
        self,
        *,
        model="gpt-3.5-turbo",
        base_url=None,
        api_key=None,
        max_retries=2,
        **params,
    ):
        self.base_url = base_url
        self.model = model
        self.params = params
        self.client = OpenAI(api_key=api_key, max_retries=max_retries, base_url=base_url)

        signature = {**params}
        if base_url is not None:
            signature["base_url"] = base_url

        name = "openai"
        if len(signature) > 0:
            name = f"openai-{object_digest(signature)[:6]}"

        super().__init__(f"{name}-{model}", self.__chat)

    def __chat(self, messages: list) -> str:
        chat_completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **self.params,
        )

        return chat_completion.choices[0].message.content
