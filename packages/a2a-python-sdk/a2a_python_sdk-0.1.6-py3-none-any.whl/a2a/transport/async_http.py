import httpx
from a2a.schema.message import A2AMessage
from a2a.schema.errors import TransportError

class AsyncHttpTransport:
    async def send(self, url: str, message: A2AMessage) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=message.model_dump())
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            raise TransportError(str(e))
