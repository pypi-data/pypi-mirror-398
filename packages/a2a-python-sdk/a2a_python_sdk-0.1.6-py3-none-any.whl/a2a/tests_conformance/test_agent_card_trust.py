from a2a.schema.agent_card import TrustDeclaration


def test_trust_declaration():
    trust = TrustDeclaration(issuer="org", signed=True)
    assert trust.signed is True
