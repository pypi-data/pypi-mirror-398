import pytest
from a2a.enterprise.rbac import check_permission, Role, Permission


def test_rbac_permissions():
    assert check_permission(Role.ADMIN, Permission.EXECUTE)
    assert not check_permission(Role.GUEST, Permission.MODIFY)
