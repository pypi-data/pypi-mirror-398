from jsonschema import validate

def validate_payload(schema: dict, payload: dict):
    validate(instance=payload, schema=schema)
