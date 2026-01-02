from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
import uuid

class ApprovalRequest(BaseModel):
    approval_id: str = uuid.uuid4().hex
    execution_id: str
    agent_id: str
    intent: str

    reason: str
    risk_level: str
    estimated_cost: float

    payload: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()

    status: str = "pending"   # pending | approved | rejected
