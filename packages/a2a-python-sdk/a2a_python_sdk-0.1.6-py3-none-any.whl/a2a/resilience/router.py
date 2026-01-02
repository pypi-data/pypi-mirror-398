from a2a.resilience.breaker import CircuitBreaker
from a2a.resilience.fallback import FallbackExecutor
from a2a.llm.factory import create_llm
from a2a.policy.presets import decision_to_llm_config

class LLMRouter:
    def __init__(self, policy_engine, secrets):
        self.policy_engine = policy_engine
        self.secrets = secrets
        self.breakers = {}

    def route(self, context):
        decision = self.policy_engine.evaluate(context)

        primary_cfg = decision_to_llm_config(decision)
        primary = create_llm(primary_cfg, self.secrets)

        if decision.fallback_provider:
            fallback_cfg = primary_cfg.copy(
                update={
                    "provider": decision.fallback_provider,
                    "model": decision.fallback_model
                }
            )
            fallback = create_llm(fallback_cfg, self.secrets)

            key = f"{primary_cfg.provider}:{primary_cfg.model}"
            breaker = self.breakers.setdefault(key, CircuitBreaker())

            return FallbackExecutor(primary, fallback, breaker)

        return primary
