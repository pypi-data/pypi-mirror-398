def serialize(toon):
    return toon.model_dump_json()

def deserialize(cls, raw: str):
    return cls.model_validate_json(raw)
