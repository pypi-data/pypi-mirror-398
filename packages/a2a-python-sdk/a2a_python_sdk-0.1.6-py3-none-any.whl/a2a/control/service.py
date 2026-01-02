class ControlService:
    def __init__(self, memory_store):
        self.memory = memory_store

    def list_executions(self):
        return self.memory.list()

    def get_execution(self, execution_id):
        return self.memory.get(execution_id)
