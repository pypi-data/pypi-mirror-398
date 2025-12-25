import time
from .._core import NamedModel, Message


class ThrottleModel(NamedModel):
    """
    Wraps a model and throttles model calls to the specified inteval.

    - **model** (`NamedModel`): the model to wrap.
    - **calls_per_minute** (`float`): how many calls per minute are allowed.
        Decimal is allowed (0.5 calls per minute means 1 call every 2 minutes). Default is `60`.
    """

    def __init__(self, model: NamedModel, *, calls_per_minute=60):
        self.model = model
        self.calls_per_minute = calls_per_minute
        self._lastast_call_time = 0.0
        super().__init__(model.name, self.__engine)

    def __engine(self, messages: list[Message]) -> str:
        now = time.time()
        delta = 60 / self.calls_per_minute
        if self._lastast_call_time is not None and now - self._lastast_call_time < delta:
            time.sleep(delta - (now - self._lastast_call_time))

        self._lastast_call_time = now
        return self.model(messages)
