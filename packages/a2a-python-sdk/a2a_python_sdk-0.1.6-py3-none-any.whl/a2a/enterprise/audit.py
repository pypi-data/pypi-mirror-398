from datetime import datetime
from a2a.schema.message import A2AMessage


class AuditEvent(BaseModel):
    timestamp: datetime
    message_id: str
    event_type: str
    actor: str
    details: dict


class AuditLog:
    def __init__(self):
        self._events: list[AuditEvent] = []

    def record(self, message: A2AMessage, event: str, extra: dict = {}):
        self._events.append(
            AuditEvent(
                timestamp=datetime.utcnow(),
                message_id=str(message.message_id),
                event_type=event,
                actor=message.sender.agent_id,
                details=extra,
            )
        )

    def export(self):
        return [e.dict() for e in self._events]
