from a2a.config.llm_config import LLMConfig
from a2a.policy.decision import PolicyDecision

def decision_to_llm_config(decision: PolicyDecision) -> LLMConfig:
    return LLMConfig(
        provider=decision.provider,
        model=decision.model,
        max_tokens=decision.max_tokens,
        response_format={"type": "json_object"} if decision.require_json else None
    )
