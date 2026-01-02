from typing import AsyncGenerator
from uuid import UUID


class TaskStatusPoller:
    """
    Poll task status until terminal.
    """

    def __init__(self, client, task_id: UUID, interval_s: float = 1.0):
        self.client = client
        self.task_id = task_id
        self.interval = interval_s

    async def stream(self) -> AsyncGenerator[str, None]:
        import asyncio

        while True:
            status = await self.client.get_task_status(self.task_id)
            yield status
            if status in ["completed", "failed", "cancelled"]:
                break
            await asyncio.sleep(self.interval)
