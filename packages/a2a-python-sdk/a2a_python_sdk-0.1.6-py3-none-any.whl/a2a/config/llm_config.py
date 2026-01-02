from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class LLMConfig(BaseModel):
    provider: str
    model: str

    # generation
    temperature: Optional[float] = 0.3
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    stop: Optional[List[str]] = None

    # advanced
    seed: Optional[int] = None
    response_format: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Any] = None

    # runtime
    stream: bool = False
    timeout: int = 60
    retries: int = 2

    # provider passthrough
    extra: Dict[str, Any] = Field(default_factory=dict)
