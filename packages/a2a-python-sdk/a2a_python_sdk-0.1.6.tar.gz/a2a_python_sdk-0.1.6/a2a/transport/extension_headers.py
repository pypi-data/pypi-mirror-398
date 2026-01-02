from typing import List, Dict

HEADER_NAME = "A2A-Extensions"


def encode_extensions(requested: List[str]) -> Dict[str, str]:
    """
    Add extension URIs to the HTTP request.
    """
    if not requested:
        return {}
    return {HEADER_NAME: ",".join(requested)}


def decode_extensions_from_response(headers: Dict[str, str]) -> List[str]:
    value = headers.get(HEADER_NAME, "")
    return [v.strip() for v in value.split(",") if v.strip()]
