from a2a.discovery.registry import AgentRegistryClient


def test_registry_client_creation():
    client = AgentRegistryClient("https://registry.example.com")
    assert client.registry_url.endswith("example.com")
