from a2a.hitl.request import ApprovalRequest
from a2a.hitl.store import ApprovalStore

class HITLEngine:
    def __init__(self, store: ApprovalStore):
        self.store = store

    def create_request(self, execution_id, ctx, cost, payload):
        request = ApprovalRequest(
            execution_id=execution_id,
            agent_id=ctx.agent_id,
            intent=ctx.intent,
            reason="High risk or cost action",
            risk_level=ctx.risk_level,
            estimated_cost=cost,
            payload=payload
        )
        self.store.create(request)
        return request

    def wait_for_decision(self, approval_id):
        """
        Blocking or polling – async in real systems
        """
        approval = self.store.get(approval_id)
        if approval.status == "approved":
            return True
        if approval.status == "rejected":
            raise RuntimeError("Action rejected by human")
        raise RuntimeError("Approval pending")
