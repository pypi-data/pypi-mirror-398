from __future__ import annotations

from uuid import UUID, uuid4
from typing import List
from datetime import datetime

from pydantic import BaseModel, Field

from a2a.schema.parts import MessagePart


class Artifact(BaseModel):
    """
    A2A Artifact – Output produced by a Task.
    Artifacts are NOT messages.
    """

    artifact_id: UUID = Field(default_factory=uuid4)

    # REQUIRED BY A2A
    task_id: UUID

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Content units (streamable)
    parts: List[MessagePart]

    # Streaming semantics
    is_final: bool = False
