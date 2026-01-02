from a2a.policy.context import PolicyContext

def requires_approval(ctx: PolicyContext, estimated_cost: float) -> bool:
    if ctx.risk_level == "high":
        return True

    if estimated_cost > 10.0:  # USD threshold
        return True

    if ctx.intent in ["infra_provision", "prod_change"]:
        return True

    return False
