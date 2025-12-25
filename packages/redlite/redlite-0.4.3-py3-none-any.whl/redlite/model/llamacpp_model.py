from .._core import NamedModel, Message, MissingDependencyError
from .._util import sha_digest

try:
    import llama_cpp
except ImportError as err:
    raise MissingDependencyError("Please install llama-cpp-python library") from err


class LlamaCppModel(NamedModel):
    """
    Chat model using Llama CPP engine.

    - **model_path** (`str`): path to model file in GGUF format
    - **params** (`dict[str,Any]`): Other keyword params, will be passed as-is to the llama_cpp.
    """

    def __init__(
        self,
        model_path: str,
        **params,
    ):
        self.llama = llama_cpp.Llama(model_path=model_path, **params)

        name = "llama-cpp.." + model_path[-25:] + "@" + sha_digest({"model_path": model_path, **params})[:6]

        super().__init__(name, self.__predict)

    def __predict(self, messages: list[Message]) -> str:
        response = self.llama.create_chat_completion(messages)  # type: ignore[arg-type]
        return response["choices"][0]["message"]["content"]  # type: ignore[index,return-value]
