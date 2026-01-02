import requests
from a2a.schema.agent_card import AgentCard

def discover_agent(base_url: str) -> AgentCard:
    resp = requests.get(f"{base_url}/.well-known/agent-card.json")
    resp.raise_for_status()
    return AgentCard(**resp.json())
