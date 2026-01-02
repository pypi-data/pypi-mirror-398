import requests

class MCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def describe(self):
        return requests.get(
            f"{self.base_url}/.well-known/mcp-tool.json"
        ).json()

    def invoke(self, payload: dict):
        r = requests.post(
            f"{self.base_url}/invoke",
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        return r.json()
