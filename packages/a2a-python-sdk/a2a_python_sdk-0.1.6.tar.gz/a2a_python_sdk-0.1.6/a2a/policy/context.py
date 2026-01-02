from pydantic import BaseModel
from typing import Optional, Dict, Any

class PolicyContext(BaseModel):
    agent_id: str
    intent: str                    # e.g. "infra_provision"
    risk_level: str = "medium"     # low | medium | high
    user_tier: str = "standard"    # free | pro | enterprise
    requires_tools: bool = False
    requires_json: bool = False
    estimated_tokens: Optional[int] = None
    metadata: Dict[str, Any] = {}
