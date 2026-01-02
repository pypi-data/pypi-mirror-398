from fastapi import FastAPI
from a2a.control.service import ControlService
from a2a.memory.store import MemoryStore

memory = MemoryStore()
service = ControlService(memory)

app = FastAPI(title="A2A Control Plane")

@app.get("/executions")
def list_executions():
    return service.list_executions()

@app.get("/executions/{execution_id}")
def get_execution(execution_id: str):
    return service.get_execution(execution_id)
