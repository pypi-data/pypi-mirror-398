from pydantic import BaseModel
from uuid import UUID

class Conversation(BaseModel):
    conversation_id: UUID
    parent_conversation_id: UUID | None = None
