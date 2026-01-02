from pydantic import BaseModel
from datetime import datetime

class ApprovalDecision(BaseModel):
    approval_id: str
    approved: bool
    reviewer: str
    comment: str | None = None
    timestamp: datetime = datetime.utcnow()
