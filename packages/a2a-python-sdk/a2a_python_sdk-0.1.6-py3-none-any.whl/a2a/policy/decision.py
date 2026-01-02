from pydantic import BaseModel
from typing import Optional, Dict, Any

class PolicyDecision(BaseModel):
    provider: str
    model: str
    allow_tools: bool = False
    require_json: bool = False
    max_tokens: Optional[int] = None
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None
    reason: str
