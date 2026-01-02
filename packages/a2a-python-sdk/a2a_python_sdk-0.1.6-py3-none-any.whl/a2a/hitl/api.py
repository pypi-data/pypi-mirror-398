from fastapi import FastAPI
from a2a.hitl.store import ApprovalStore

store = ApprovalStore()
app = FastAPI(title="HITL Approval API")

@app.get("/approvals")
def list_pending():
    return store.list_pending()

@app.post("/approvals/{approval_id}/approve")
def approve(approval_id: str):
    store.update(approval_id, "approved")
    return {"status": "approved"}

@app.post("/approvals/{approval_id}/reject")
def reject(approval_id: str):
    store.update(approval_id, "rejected")
    return {"status": "rejected"}
