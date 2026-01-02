from __future__ import annotations

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """
    First-class Task object as defined by A2A protocol.
    """

    task_id: UUID = Field(default_factory=uuid4)

    status: TaskStatus = TaskStatus.SUBMITTED

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Logical grouping (A2A Context / Conversation)
    context_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None

    # Optional metadata
    metadata: Optional[Dict[str, Any]] = None

    # Failure information
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def update_status(self, status: TaskStatus):
        self.status = status
        self.updated_at = datetime.utcnow()
