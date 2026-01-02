class ApprovalStore:
    def __init__(self):
        self._approvals = {}

    def create(self, request):
        self._approvals[request.approval_id] = request

    def get(self, approval_id):
        return self._approvals.get(approval_id)

    def list_pending(self):
        return [
            a for a in self._approvals.values()
            if a.status == "pending"
        ]

    def update(self, approval_id, status):
        self._approvals[approval_id].status = status
