from typing import Callable, List


class PolicyRule:
    def __init__(self, name: str, condition: Callable):
        self.name = name
        self.condition = condition

    def evaluate(self, message):
        return self.condition(message)


class PolicyEngine:
    def __init__(self, rules: List[PolicyRule]):
        self.rules = rules

    def enforce(self, message):
        for rule in self.rules:
            if not rule.evaluate(message):
                raise PermissionError(f"PolicyRule failed: {rule.name}")
