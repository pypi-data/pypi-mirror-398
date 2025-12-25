from .._core import NamedModel, Message
from .._util import sha_digest


class IgnoreSystemModel(NamedModel):
    """
    Wraps a model and removes system message from the model input (if any).
    Useful if underlying model was not trained with system message.

    - **model** (`NamedModel`): the model to wrap.
    """

    def __init__(self, model: NamedModel):
        self.model = model
        super().__init__(f"ignore-system-{model.name}", self.__engine)

    def __engine(self, messages: list[Message]) -> str:
        if messages[0]["role"] == "system":
            return self.model(messages[1:])
        else:
            return self.model(messages)


class MakeSystemModel(NamedModel):
    """
    Wraps a model and inserts (or replaces existing) system message.
    Useful to set system message when underlying dataset has none.

    - **model** (`NamedModel`): the model to wrap.
    """

    def __init__(self, model: NamedModel, system_prompt: str):
        self.model = model
        self.system_prompt = system_prompt
        name = f"make-system-{model.name}@{sha_digest(system_prompt)[:6]}"
        super().__init__(name, self.__engine)

    def __engine(self, messages: list[Message]) -> str:
        system_messages: list[Message] = [{"role": "system", "content": self.system_prompt}]
        if messages[0]["role"] == "system":
            messages = messages[1:]
        return self.model(system_messages + messages)


class ConvertSystemToUserModel(NamedModel):
    """
    Wraps a model and replaces system message with the user one.
    Useful if underlying model was not trained with system message.

    - **model** (`NamedModel`): the model to wrap.
    - **assistant_confirmation** (`str`): assistant message to use as a response
        to the generated user one. Optional, default is `"OK"`.

    As an example, the following code:

    ```python
    engine_model = ...  # a model that does not accept "system" message

    model = ConvertSystemToUserModel(engine_model, "Aye aye, Sir!")
    ```

    and the following input:

    ```json
    [
        { "role": "system", "content": "You are useful and safe model" },
        { "role": "user", "content": "How to kill a process?" },
    ]
    ```

    will make `engine_model` to receive the following converted prompt:

    ```json
    [
        { "role": "user", "content": "You are useful and safe model" },
        { "role": "assistant", "content": "Aye aye, Sir!" },
        { "role": "user", "content": "How to kill a process?" },
    ]
    ```
    """

    def __init__(self, model: NamedModel, assistant_confirmation: str = "OK"):
        self.model = model
        name = f"convert-system-{model.name}"
        if assistant_confirmation != "OK":
            name += "@" + sha_digest(assistant_confirmation)[:6]
        self.assistant_confirmation = assistant_confirmation
        super().__init__(name, self.__engine)

    def __engine(self, messages: list[Message]) -> str:
        if messages[0]["role"] == "system":
            prefix: list[Message] = [
                {"role": "user", "content": messages[0]["content"]},
                {"role": "assistant", "content": self.assistant_confirmation},
            ]
            messages = prefix + messages[1:]
        return self.model(messages)
