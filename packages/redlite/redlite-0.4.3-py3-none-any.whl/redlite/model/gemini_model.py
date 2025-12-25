from .. import NamedModel, MissingDependencyError
from .._util import object_digest
from typing import Optional

try:
    from google import genai
except ImportError as err:
    raise MissingDependencyError("Please install google-genai library") from err


class GeminiModel(NamedModel):
    """
    Model that talks to Google Gemini family of models.

    - **model** (`str`): Name of the Gemini model. Default is `"gemini-2.5-flash"`.
    - **api_key** (`str`): Google API key (see Google Cloud Console https://aistudio.google.com/u/1/apikey). This key is
        required to authenticate with the Gemini API. Alternatively, api key can be speciafied with environment variable
        `GEMINI_API_KEY`.
    - **vertexai** (`bool`): Set this to `True` if using Vertex AI. Alternative way to force use of Vertex AI is to set
        environment variable `GOOGLE_GEMINI_USE_VERTEXAI=true`.
    - **project**: (`str`): Only required for Vertex AI. The name of your Google Cloud project.
        Can alternatively be set as environment variable `GOOGLE_CLOUD_PROJECT`.
    - **location**: (`str`): Only required for Vertex AI. The location of the Vertex AI instance.
        Can alternatively be set as environment variable `GOOGLE_CLOUD_LOCATION`.
    - **thinking_budget** (`int`): Optional thinking budget in tokens. Not every model supports thinking.
        Set to 0 to disable thinking (if supported by the model).
        Set to -1 to enable dynamic thinking (if supported by the model).
        See https://ai.google.dev/gemini-api/docs/thinking for more details.
    """

    def __init__(
        self,
        *,
        model: str = "gemini-1.5-pro",
        api_key: Optional[str] = None,
        vertexai: Optional[bool] = None,
        project: Optional[str] = None,
        location: Optional[str] = None,
        thinking_budget: Optional[int] = None,
    ):
        self._model = model

        self._client = genai.Client(
            api_key=api_key,
            vertexai=vertexai,
            project=project,
            location=location,
        )

        name = "google"
        if thinking_budget is not None:
            name = f'google-{object_digest({"thinking_budget": thinking_budget})[:6]}'
        self._thinking_config = (
            None if thinking_budget is None else genai.types.ThinkingConfig(thinking_budget=thinking_budget)
        )

        super().__init__(f"{name}-{model}", self.__chat)

    def __chat(self, messages: list) -> str:
        system_instruction = None
        if messages[0]["role"] == "system":
            system_instruction = messages[0]["content"]
            messages = messages[1:]
        contents = [
            genai.types.Content(role=_ROLE_MAP[x["role"]], parts=[genai.types.Part.from_text(text=x["content"])])
            for x in messages
        ]
        config = None
        if self._thinking_config is not None or system_instruction is not None:
            config = genai.types.GenerateContentConfig(
                thinking_config=self._thinking_config,
                system_instruction=system_instruction,
            )
        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=config,
        )
        return response.text or ""


_ROLE_MAP = {
    "user": "user",
    "assistant": "model",
    "system": "system",
}
