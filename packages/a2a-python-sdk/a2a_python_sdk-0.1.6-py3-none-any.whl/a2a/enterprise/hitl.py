from typing import Callable


class HITLRequest(BaseModel):
    task_id: str
    reason: str
    requested_by: str


class HITLEngine:
    def __init__(self):
        self._callbacks: list[Callable] = []

    def register(self, callback: Callable):
        self._callbacks.append(callback)

    def request_approval(self, request: HITLRequest):
        # synchronous callback
        for callback in self._callbacks:
            callback(request)
