from pydantic import BaseModel

class A2AError(BaseModel):
    code: str                 # e.g. AGENT_TIMEOUT
    category: str             # TRANSIENT | PERMANENT | SECURITY | POLICY | HITL
    message: str
    retryable: bool = False

# Canonical error codes
ERROR_CODES = {
    "AGENT_TIMEOUT": "TRANSIENT",
    "AGENT_UNAVAILABLE": "TRANSIENT",
    "INVALID_SIGNATURE": "SECURITY",
    "REPLAY_DETECTED": "SECURITY",
    "POLICY_DENIED": "POLICY",
    "HITL_REQUIRED": "HITL"
}
