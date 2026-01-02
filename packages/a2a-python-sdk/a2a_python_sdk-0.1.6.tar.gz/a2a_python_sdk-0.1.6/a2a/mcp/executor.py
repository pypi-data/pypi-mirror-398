from a2a.zod.validator import validate_payload
from a2a.toon.runtime import TOONRuntime

runtime = TOONRuntime()

class MCPExecutor:
    def __init__(self, schema: dict, toon_cls, handler):
        self.schema = schema
        self.toon_cls = toon_cls
        self.handler = handler

    def execute(self, payload: dict):
        validate_payload(self.schema, payload)

        toon = self.toon_cls(**payload)
        return runtime.execute(toon, self.handler)
