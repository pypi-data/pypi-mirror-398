import requests
from typing import List
from a2a.schema.agent_card import AgentCard


class AgentRegistryClient:
    """
    Catalog-based agent discovery.
    """

    def __init__(self, registry_url: str):
        self.registry_url = registry_url.rstrip("/")

    def list_agents(self) -> List[AgentCard]:
        resp = requests.get(f"{self.registry_url}/agents")
        resp.raise_for_status()
        return [AgentCard.model_validate(a) for a in resp.json()]

    def find_by_capability(self, capability: str) -> List[AgentCard]:
        resp = requests.get(
            f"{self.registry_url}/agents",
            params={"capability": capability},
        )
        resp.raise_for_status()
        return [AgentCard.model_validate(a) for a in resp.json()]
