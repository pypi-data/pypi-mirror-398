import json
from pathlib import Path

def load_schema(path: str) -> dict:
    return json.loads(Path(path).read_text())
