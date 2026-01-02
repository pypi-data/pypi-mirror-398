from pydantic import BaseModel
from typing import Any, Dict, List
from datetime import datetime
import uuid

class AgentExecutionRecord(BaseModel):
    execution_id: str = uuid.uuid4().hex
    agent_id: str
    intent: str

    policy_context: Dict[str, Any]
    llm_config: Dict[str, Any]

    inputs: List[Dict[str, Any]]
    outputs: Any

    tools_used: List[str] = []
    toon_objects: List[Dict[str, Any]] = []

    timestamp: datetime = datetime.utcnow()
    status: str = "success"   # success | failed
    error: str | None = None
