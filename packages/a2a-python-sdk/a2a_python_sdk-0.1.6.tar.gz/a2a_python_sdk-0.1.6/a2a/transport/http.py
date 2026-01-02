import requests
from a2a.schema.message import A2AMessage
from a2a.schema.errors import TransportError

class HttpTransport:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def send(self, url: str, message: A2AMessage) -> dict:
        try:
            resp = requests.post(
                url,
                json=message.model_dump(),
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise TransportError(str(e))
