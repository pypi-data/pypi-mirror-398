from .._core import NamedModel, Message, MissingDependencyError, log
from .._util import object_digest

try:
    from openai import OpenAI
except ImportError as err:
    raise MissingDependencyError("Please install openai library") from err

_DEFAULT_MODERATION_MODEL = "omni-moderation-latest"

_DEFAULT_REFUSAL_MESSAGE = "I refuse to answer this question."


class ModerationModel(NamedModel):
    """
    Wraps a model and filters conversation content using OpenAI Moderation API.

    https://platform.openai.com/docs/guides/safety-best-practices#use-our-free-moderation-api

    Before delegating to the inner model, all message contents are checked
    against OpenAI's moderation API. If any content is flagged as potentially
    harmful, the model returns a refusal message instead of processing the request.

    This avoids having OpenAI account flagged for Usage Policy Violation

    Requires OpenAI API key (via `api_key` parameter or OPENAI_API_KEY env var).

    - **model** (`NamedModel`): The model to wrap.
    - **api_key** (`str | None`): OpenAI API key. Optional, defaults to None
        (will use OPENAI_API_KEY environment variable).
    - **moderation_model** (`str`): Which OpenAI moderation model to use.
        Default is `"omni-moderation-latest"`.
    - **refusal_message** (`str`): Message to return when content is flagged.
        Default is `"I refuse to answer this question."`.
    - **threshold** (`float | dict[str, float]`): Score threshold(s) for flagging content.
        If a float is provided, it is used as the threshold for all categories.
        If a dict is provided, it should map category names to threshold floats. Missing categories will
        default to threshold of `1.0` (never flag).
        Default is `0.8`. For list of valid category names see
        [OpenAI Moderation API docs](https://platform.openai.com/docs/guides/moderation#content-classifications).

    Note: If the moderation API fails (network error, rate limit, etc.),
    the wrapper will fail closed (return refusal) to maintain safety guarantees.

    Example:
    ```python
    from redlite.model import ModerationModel
    from redlite.model.openai_model import OpenAIModel

    # Create base model
    base_model = OpenAIModel(model="gpt-4")

    # Wrap with moderation
    safe_model = ModerationModel(base_model)

    # Safe content passes through
    response = safe_model([{"role": "user", "content": "What is Python?"}])

    # Harmful content is blocked
    response = safe_model([{"role": "user", "content": "harmful request"}])
    # Returns: "I refuse to answer this question."
    ```

    Example of using custom thresholds:
    ```python
    safe_model = ModerationModel(base_model, threshold={
        "sexual": 0.7,
        "hate": 0.6,
    })
    ```

    The wrapped model `safe_model` above will flag content as harmful if
    the "sexual" score is >= 0.7 or the "hate" score is >= 0.6. All other categories will not be flagged
    regardless of their score.
    """

    def __init__(
        self,
        model: NamedModel,
        *,
        api_key: str | None = None,
        moderation_model: str = _DEFAULT_MODERATION_MODEL,
        refusal_message: str = _DEFAULT_REFUSAL_MESSAGE,
        threshold: float | dict[str, float] = 0.8,
    ):
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.moderation_model = moderation_model
        self.refusal_message = refusal_message

        if type(threshold) is float:
            self.threshold = {cat: threshold for cat in _MODERATION_CATEGORIES}
        elif type(threshold) is dict:
            categories = set(threshold.keys())
            if categories - _MODERATION_CATEGORIES:
                raise ValueError(
                    f"Threshold dict contains unknown moderation categories: {categories - _MODERATION_CATEGORIES}"
                )
            if not all(type(val) is float for val in threshold.values()):
                raise ValueError("All threshold values must be floats.")
            self.threshold = threshold

        if (
            threshold == 0.8
            and moderation_model == _DEFAULT_MODERATION_MODEL
            and refusal_message == _DEFAULT_REFUSAL_MESSAGE
        ):
            name = f"moderated-{model.name}"
        else:
            signature = {
                "moderation_model": moderation_model,
                "refusal_message": refusal_message,
                "threshold": self.threshold,
            }
            name = f"moderated-{model.name}-{object_digest(signature)[:6]}"
        super().__init__(name, self.__engine)

    def __engine(self, messages: list[Message]) -> str:
        # Extract content from all messages (remove roles)
        content_list = [msg["content"] for msg in messages]

        try:
            # Call OpenAI Moderation API
            moderation = self.client.moderations.create(
                model=self.moderation_model,
                input=content_list,
            )

            # Check if any content was flagged
            if any(
                _threshold_exceeded(result.category_scores.model_dump(), self.threshold)
                for result in moderation.results
            ):
                return self.refusal_message

            # Content is safe, delegate to inner model
            return self.model(messages)

        except Exception as e:
            # Fail closed: if moderation API fails, refuse to answer
            log.error(f"Moderation API error: {e}")
            return self.refusal_message


_MODERATION_CATEGORIES = {
    "sexual",
    "sexual/minors",
    "harassment",
    "harassment/threatening",
    "hate",
    "hate/threatening",
    "illicit",
    "illicit/violent",
    "self-harm",
    "self-harm/intent",
    "self-harm/instructions",
    "violence",
    "violence/graphic",
}


def _threshold_exceeded(scores: dict[str, float], thresholds: dict[str, float]) -> bool:
    for category, score in scores.items():
        if score >= thresholds.get(category, 1.0):
            return True
    return False
