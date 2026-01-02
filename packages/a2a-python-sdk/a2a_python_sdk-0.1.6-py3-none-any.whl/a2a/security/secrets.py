import os

def get_secret(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing secret: {key}")
    return value
