from pydantic import BaseModel

class Identity(BaseModel):
    id: str                  # agent-id / tool-id
    type: str                # agent | tool | admin
    role: str                # rbac role
