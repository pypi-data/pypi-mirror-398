from a2a.security.signer import sign_message, verify_signature

def test_signature_roundtrip():
    payload = "test"
    secret = "key"
    sig = sign_message(payload, secret)
    assert verify_signature(payload, sig, secret)
