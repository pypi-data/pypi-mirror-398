ROLES = {
    "agent": {"invoke_agent"},
    "tool": {"execute_tool"},
    "admin": {"inspect", "replay"}
}

def authorize(role: str, action: str):
    allowed = ROLES.get(role, set())
    if action not in allowed:
        raise PermissionError(f"RBAC denied: {role} → {action}")
