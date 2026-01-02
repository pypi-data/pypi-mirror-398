from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

class ExecutionSummary(BaseModel):
    execution_id: str
    agent_id: str
    intent: str
    status: str
    cost_usd: Optional[float]
    model: str
    timestamp: datetime

class ExecutionDetail(BaseModel):
    execution_id: str
    policy_context: Dict[str, Any]
    llm_config: Dict[str, Any]
    inputs: Any
    outputs: Any
    tools_used: List[str]
    toon_objects: List[Dict[str, Any]]
    token_usage: Dict[str, Any]
