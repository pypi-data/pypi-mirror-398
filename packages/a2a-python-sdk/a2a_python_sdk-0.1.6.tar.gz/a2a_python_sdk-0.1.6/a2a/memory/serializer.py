import json

def serialize_record(record):
    return record.model_dump_json()

def deserialize_record(cls, raw: str):
    return cls.model_validate_json(raw)
