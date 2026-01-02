from a2a.streaming.models import StreamingPart, StreamingEventType
from uuid import uuid4

def test_streaming_part_fields():
    sp = StreamingPart(
        event_id=uuid4(),
        task_id=uuid4(),
        type=StreamingEventType.TOKEN,
        data="partial"
    )
    assert sp.is_final is False
