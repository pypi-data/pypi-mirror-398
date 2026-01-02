import hmac
import hashlib

def sign_message(payload: str, secret: str) -> str:
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

def verify_signature(payload: str, signature: str, secret: str) -> bool:
    expected = sign_message(payload, secret)
    return hmac.compare_digest(expected, signature)
