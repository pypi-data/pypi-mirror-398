import httpx
from typing import AsyncGenerator
from a2a.streaming.models import StreamingPart

SSE_HEADERS = {
    "Accept": "text/event-stream",
}


async def sse_stream(
    url: str, headers: dict | None = None
) -> AsyncGenerator[StreamingPart, None]:
    headers = headers or {}
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url, headers={**SSE_HEADERS, **headers}) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    raw = line[len("data:") :].strip()
                    event = StreamingPart.parse_raw(raw)
                    yield event
