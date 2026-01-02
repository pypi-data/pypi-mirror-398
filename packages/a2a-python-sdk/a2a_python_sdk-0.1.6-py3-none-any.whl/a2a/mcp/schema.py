from pydantic import BaseModel
from typing import Dict, Any

class MCPTool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]   # JSON schema (from ZOD)
