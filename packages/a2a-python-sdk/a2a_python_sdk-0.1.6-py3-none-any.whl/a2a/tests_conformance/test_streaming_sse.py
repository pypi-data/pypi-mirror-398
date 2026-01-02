import pytest
from a2a.streaming.http_sse import sse_stream

@pytest.mark.asyncio
async def test_sse_stream_no_crash():
    # This test should not crash if agent is not available
    async for _ in sse_stream("http://localhost:8080/sse"):
        pass
