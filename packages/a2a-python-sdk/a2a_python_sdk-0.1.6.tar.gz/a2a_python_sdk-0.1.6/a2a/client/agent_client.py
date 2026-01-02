from a2a.transport.http import HttpTransport
from a2a.transport.retry import retry
from a2a.schema.message import A2AMessage
from a2a.security.signer import sign_message
from a2a.security.secrets import get_secret
import json
from uuid import UUID
from typing import AsyncGenerator

class AgentClient:
    def __init__(self, base_url: str, transport=None):
        self.base_url = base_url.rstrip("/")
        self.transport = transport or HttpTransport()

    def send(self, msg):
        secret = get_secret("A2A_SHARED_SECRET")

        msg.signature = sign_message(
            json.dumps(msg.model_dump(exclude={"signature"})),
            secret
        )

        return self.transport.send(self.url, msg)

    async def get_task_status(self, task_id: UUID) -> str:
        # client poll to server endpoint /a2a/task/status/{task_id}
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/task/status/{task_id}")
            resp.raise_for_status()
            return resp.json()["status"] 

    async def stream_sse(
        self, url: str, headers: dict | None = None
    ) -> AsyncGenerator:
        from a2a.streaming.http_sse import sse_stream

        async for part in sse_stream(url, headers):
            yield part

    async def stream_ws(self, uri: str) -> AsyncGenerator:
        from a2a.streaming.websocket import websocket_stream

        async for part in websocket_stream(uri):
            yield part