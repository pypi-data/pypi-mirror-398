from a2a.schema.agent_card import AgentCard
from a2a.extensions.models import AgentExtension

def test_agent_card_extension_supported():
    ext = AgentExtension(uri="https://example.com/ext/foo/v1", description="foo")
    card = AgentCard(agent_id="a", agent_name="n", extensions=[ext])
    assert card.extensions[0].uri.startswith("https://")
