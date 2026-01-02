from a2a.protocol.versioning import negotiate_version

def test_version_negotiation():
    assert negotiate_version(["1.0"]) == "1.0"
