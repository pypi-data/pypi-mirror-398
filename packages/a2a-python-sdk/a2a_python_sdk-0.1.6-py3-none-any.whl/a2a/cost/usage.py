from pydantic import BaseModel
from typing import Optional

class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    cost_usd: Optional[float] = None
