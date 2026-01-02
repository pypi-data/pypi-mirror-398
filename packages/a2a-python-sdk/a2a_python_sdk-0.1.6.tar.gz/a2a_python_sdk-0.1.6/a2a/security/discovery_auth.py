from typing import Dict


def auth_headers(token: str | None = None) -> Dict[str, str]:
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}
