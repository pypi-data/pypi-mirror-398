from pydantic import BaseModel
from typing import List

class TrustPolicy(BaseModel):
    trust_domain: str
    allowed_peers: List[str]
