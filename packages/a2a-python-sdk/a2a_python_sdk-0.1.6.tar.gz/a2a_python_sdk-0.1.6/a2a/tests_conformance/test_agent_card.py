import requests

def test_agent_card_fields():
    card = requests.get("http://localhost:8001/.well-known/agent-card.json").json()
    assert "agent_id" in card
    assert "capabilities" in card
    assert "protocol" in card
