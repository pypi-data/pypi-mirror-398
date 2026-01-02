from a2a.extensions.models import AgentExtension
from a2a.schema.agent_card import AgentCard

def test_required_extension_field():
    ext = AgentExtension(uri="https://example.com/ext/foo/v1", required=True)
    card = AgentCard(agent_id="a", agent_name="n", extensions=[ext])

    assert any(e.required for e in card.extensions)
