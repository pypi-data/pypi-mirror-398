import requests
from a2a.schema.agent_card import AgentCard
from a2a.security.discovery_auth import auth_headers
from a2a.discovery.base import DiscoveryStrategy


class SecuredDiscovery(DiscoveryStrategy):
    """
    Discovery with authentication.
    """

    def __init__(self, token: str):
        self.token = token

    def discover(self, base_url: str) -> AgentCard:
        url = f"{base_url.rstrip('/')}/.well-known/agent-card.json"
        resp = requests.get(
            url,
            headers=auth_headers(self.token),
            timeout=5,
        )
        resp.raise_for_status()
        return AgentCard.model_validate(resp.json())
