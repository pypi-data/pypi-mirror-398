from __future__ import annotations
from uuid import UUID
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class StreamingEventType(str, Enum):
    TOKEN = "token"
    STATUS = "status"
    ARTIFACT_PART = "artifact_part"
    COMPLETION = "completion"


class StreamingPart(BaseModel):
    event_id: UUID
    task_id: UUID
    type: StreamingEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # actual payload
    data: str | dict | None = None

    # finality semantics
    is_final: bool = False
