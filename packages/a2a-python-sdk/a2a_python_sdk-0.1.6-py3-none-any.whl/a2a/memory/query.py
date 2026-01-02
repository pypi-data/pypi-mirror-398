def filter_by_agent(records, agent_id: str):
    return [r for r in records if r.agent_id == agent_id]

def filter_by_intent(records, intent: str):
    return [r for r in records if r.intent == intent]
