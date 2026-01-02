class MemoryStore:
    def __init__(self):
        self._store = {}

    def save(self, record):
        self._store[record.execution_id] = record

    def get(self, execution_id: str):
        return self._store.get(execution_id)

    def list(self):
        return list(self._store.values())
