from a2a.cost.pricing import PRICING

def calculate_cost(provider: str, model: str, usage):
    key = f"{provider}:{model}"
    pricing = PRICING.get(key)

    if not pricing:
        return 0.0

    prompt_cost = (usage.prompt_tokens / 1000) * pricing["prompt"]
    completion_cost = (usage.completion_tokens / 1000) * pricing["completion"]

    return round(prompt_cost + completion_cost, 6)
