import websockets
import json
from typing import AsyncGenerator
from a2a.streaming.models import StreamingPart

async def websocket_stream(
    uri: str
) -> AsyncGenerator[StreamingPart, None]:
    async with websockets.connect(uri) as ws:
        async for msg in ws:
            part = StreamingPart.parse_raw(msg)
            yield part
