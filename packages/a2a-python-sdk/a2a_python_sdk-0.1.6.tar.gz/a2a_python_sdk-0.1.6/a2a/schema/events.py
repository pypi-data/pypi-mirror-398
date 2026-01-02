from enum import Enum
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

class TaskEventType(str, Enum):
    STATUS_UPDATE = "status_update"
    ARTIFACT_UPDATE = "artifact_update"

class TaskStatusUpdateEvent(BaseModel):
    task_id: UUID
    old_status: str
    new_status: str
    timestamp: datetime

class TaskArtifactUpdateEvent(BaseModel):
    task_id: UUID
    artifact_id: UUID
    timestamp: datetime
