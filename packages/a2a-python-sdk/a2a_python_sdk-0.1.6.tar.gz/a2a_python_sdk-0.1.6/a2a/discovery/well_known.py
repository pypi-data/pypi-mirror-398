import requests
from a2a.schema.agent_card import AgentCard
from a2a.discovery.base import DiscoveryStrategy


class WellKnownDiscovery(DiscoveryStrategy):
    """
    Discovers agent via /.well-known/agent-card.json
    """

    def discover(self, base_url: str) -> AgentCard:
        url = f"{base_url.rstrip('/')}/.well-known/agent-card.json"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return AgentCard.model_validate(resp.json())
