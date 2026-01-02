from enum import Enum
from typing import List


class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    GUEST = "guest"


class Permission(str, Enum):
    EXECUTE = "execute"
    MODIFY = "modify"
    READ = "read"
    APPROVE = "approve"


ROLE_PERMISSIONS = {
    Role.ADMIN: [Permission.EXECUTE, Permission.MODIFY, Permission.READ, Permission.APPROVE],
    Role.OPERATOR: [Permission.EXECUTE, Permission.READ],
    Role.REVIEWER: [Permission.READ, Permission.APPROVE],
    Role.GUEST: [Permission.READ],
}


def check_permission(role: Role, permission: Permission) -> bool:
    """Check if a role allows a given permission."""
    return permission in ROLE_PERMISSIONS.get(role, [])
