from a2a.policy.context import PolicyContext
from a2a.policy.rules import apply_rules

class PolicyEngine:
    def evaluate(self, context: PolicyContext):
        return apply_rules(context)
