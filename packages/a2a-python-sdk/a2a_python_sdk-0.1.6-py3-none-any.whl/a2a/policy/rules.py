from a2a.policy.context import PolicyContext
from a2a.policy.decision import PolicyDecision

def apply_rules(ctx: PolicyContext) -> PolicyDecision:
    # ---- HIGH RISK → BEST MODEL ----
    if ctx.risk_level == "high":
        return PolicyDecision(
            provider="openai",
            model="gpt-4.1",
            allow_tools=True,
            require_json=True,
            fallback_provider="groq",
            fallback_model="llama-3.1-70b",
            reason="High risk execution"
        )

    # ---- LOW COST ROUTING ----
    if ctx.user_tier == "free":
        return PolicyDecision(
            provider="ollama",
            model="llama3.2",
            allow_tools=False,
            reason="Free tier local inference"
        )

    # ---- TOOL HEAVY WORK ----
    if ctx.requires_tools:
        return PolicyDecision(
            provider="openai",
            model="gpt-4o-mini",
            allow_tools=True,
            reason="Tool calling required"
        )

    # ---- DEFAULT ----
    return PolicyDecision(
        provider="groq",
        model="llama-3.1-8b-instant",
        reason="Default fast path"
    )
