from a2a.cost.usage import TokenUsage
from a2a.cost.calculator import calculate_cost

class UsageTracker:
    def track(self, provider, model, raw_usage) -> TokenUsage:
        usage = TokenUsage(
            prompt_tokens=raw_usage.get("prompt_tokens", 0),
            completion_tokens=raw_usage.get("completion_tokens", 0),
            total_tokens=raw_usage.get("total_tokens", 0)
        )

        usage.cost_usd = calculate_cost(provider, model, usage)
        return usage
