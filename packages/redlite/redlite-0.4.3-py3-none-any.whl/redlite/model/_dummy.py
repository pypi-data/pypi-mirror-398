from .._core import NamedModel, Message


class CannedModel(NamedModel):
    """
    Returns back the canned response, regardless of the input.

    - **response** (`str`): string to return (same for every request).

    """

    def __init__(self, response: str):
        self.response = response
        super().__init__("canned", self.__engine)

    def __engine(self, messages: list[Message]) -> str:
        return self.response


class ParrotModel(NamedModel):
    """
    Returns back last user message.
    """

    def __init__(self):
        super().__init__("parrot", self.__engine)

    def __engine(self, messages: list[Message]) -> str:
        return messages[-1]["content"]
