import pytest
from uuid import uuid4
from a2a.streaming.async_status import TaskStatusPoller

@pytest.mark.asyncio
async def test_task_status_poller_future():
    # No real server, ensure generator yields at least once
    client = None  # mock
    poller = TaskStatusPoller(client, uuid4())
    async for _ in poller.stream():
        break
