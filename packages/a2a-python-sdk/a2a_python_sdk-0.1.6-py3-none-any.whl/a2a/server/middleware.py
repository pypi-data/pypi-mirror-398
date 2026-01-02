from a2a.security.replay_guard import check
from a2a.security.signer import verify_signature
from a2a.security.secrets import get_secret
from a2a.security.audit import audit
import json

async def security_middleware(request, call_next):
    body = await request.json()

    try:
        check(body["message_id"])

        secret = get_secret("A2A_SHARED_SECRET")

        if not verify_signature(
            json.dumps({k: v for k, v in body.items() if k != "signature"}),
            body.get("signature"),
            secret
        ):
            audit("INVALID_SIGNATURE", body)
            raise RuntimeError("Invalid signature")

    except Exception as e:
        audit("SECURITY_BLOCK", {"error": str(e)})
        raise

    return await call_next(request)
