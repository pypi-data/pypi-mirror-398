from typing import Any, Dict, Optional
from pydantic import BaseModel

class AgentExtension(BaseModel):
    """
    Represents extension support declared in the AgentCard.
    The 'uri' identifies the extension.
    """
    uri: str
    description: Optional[str] = None
    required: bool = False
    params: Dict[str, Any] = {}
