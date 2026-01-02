from a2a.extensions.negotiation import ExtensionNegotiator
from a2a.schema.agent_card import AgentCard
from a2a.extensions.models import AgentExtension

def test_extension_activation_basic():
    ext = AgentExtension(uri="https://example.com/ext/foo/v1")
    card = AgentCard(agent_id="a", agent_name="n", extensions=[ext])

    negotiated = ExtensionNegotiator.negotiate(
        card, ["https://example.com/ext/foo/v1", "https://example.com/ext/bar/v1"]
    )

    assert negotiated == ["https://example.com/ext/foo/v1"]
