from pydantic import BaseModel
from datetime import datetime

class AgentHealth(BaseModel):
    agent_id: str
    state: str
    version: str
    timestamp: datetime = datetime.utcnow()
