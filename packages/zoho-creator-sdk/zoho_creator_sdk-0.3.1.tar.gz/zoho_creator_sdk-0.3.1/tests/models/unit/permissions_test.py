"""Unit tests for permission-related models."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from zoho_creator_sdk.models.enums import EntityType, PermissionType
from zoho_creator_sdk.models.permissions import (
    Permission,
    PermissionInheritance,
    Role,
    UserPermission,
)


def _future(seconds: int = 60) -> datetime:
    return datetime.utcnow() + timedelta(seconds=seconds)


def _permission_payload(**overrides):
    payload = {
        "id": "perm",
        "name": "Read",
        "entity_type": EntityType.FORM,
        "entity_id": "form",
        "permission_type": PermissionType.READ,
        "granted_to_user_id": "user",
        "granted_by_user_id": "admin",
        "created_at": datetime.utcnow(),
        "modified_at": datetime.utcnow(),
    }
    payload.update(overrides)
    return payload


def test_permission_requires_target_assignment() -> None:
    with pytest.raises(ValueError):
        Permission(**_permission_payload(granted_to_user_id=None))

    with pytest.raises(ValueError):
        Permission(**_permission_payload(granted_to_role_id="role"))

    with pytest.raises(ValueError):
        Permission(
            **_permission_payload(granted_to_user_id="user", granted_to_role_id="role")
        )

    with pytest.raises(ValueError):
        Permission(**_permission_payload(conditions="invalid"))

    perm = Permission(**_permission_payload(expires_at=_future()))
    assert perm.is_effective() is True
    assert perm.get_target_id() == "user"
    assert perm.get_target_type() == "user"

    perm.is_active = False
    assert perm.is_effective() is False

    orphan = Permission(
        **_permission_payload(granted_to_user_id=None, granted_to_role_id="role")
    )
    orphan.granted_to_role_id = None
    with pytest.raises(ValueError):
        orphan.get_target_id()

    role_target = Permission(
        **_permission_payload(granted_to_user_id=None, granted_to_role_id="role")
    )
    assert role_target.get_target_id() == "role"
    assert role_target.get_target_type() == "role"


def test_permission_expiration_logic() -> None:
    with pytest.raises(ValueError):
        Permission(**_permission_payload(expires_at=_future(-10)))

    perm = Permission(**_permission_payload(expires_at=_future()))
    perm.expires_at = datetime.utcnow() - timedelta(seconds=1)
    assert perm.is_expired() is True
    perm.expires_at = None
    assert perm.is_expired() is False


def test_role_permission_management() -> None:
    with pytest.raises(ValueError):
        Role(
            id="role",
            name="Role",
            display_name="Role",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            created_by_user_id="admin",
            parent_role_id="role",
            permission_ids=["perm1"],
            child_role_ids=[],
            current_user_count=0,
        )

    with pytest.raises(ValueError):
        Role(
            id="role",
            name="Role",
            display_name="Role",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            created_by_user_id="admin",
            permission_ids=["perm1"],
            child_role_ids=[],
            current_user_count=5,
            max_users=2,
        )

    role = Role(
        id="role",
        name="Role",
        display_name="Role",
        created_at=datetime.utcnow(),
        modified_at=datetime.utcnow(),
        created_by_user_id="admin",
        permission_ids=["perm1"],
        child_role_ids=["child"],
        current_user_count=1,
        max_users=2,
    )

    assert role.has_permission("perm1")
    assert role.has_any_permission(["perm1", "perm2"]) is True
    assert role.has_all_permissions(["perm1"]) is True

    role.add_permission("perm2")
    role.remove_permission("perm1")
    assert role.get_permission_count() == 1
    assert role.is_parent_of("child") is True
    assert role.can_accommodate_users(1) is True
    assert role.get_available_slots() == 1

    role_unbounded = Role(
        id="role2",
        name="Role",
        display_name="Role",
        created_at=datetime.utcnow(),
        modified_at=datetime.utcnow(),
        created_by_user_id="admin",
        permission_ids=[],
        child_role_ids=[],
        current_user_count=0,
    )
    assert role_unbounded.can_accommodate_users(5) is True
    assert role_unbounded.get_available_slots() is None


def _user_permission_payload(**overrides):
    payload = {
        "id": "up",
        "user_id": "user",
        "entity_type": EntityType.FORM,
        "entity_id": "form",
        "permission_type": PermissionType.READ,
        "granted_by_user_id": "admin",
        "created_at": datetime.utcnow(),
        "modified_at": datetime.utcnow(),
    }
    payload.update(overrides)
    return payload


def test_user_permission_validations() -> None:
    with pytest.raises(ValueError):
        UserPermission(
            **_user_permission_payload(
                expires_at=datetime.utcnow() - timedelta(seconds=1)
            )
        )

    with pytest.raises(ValueError):
        UserPermission(**_user_permission_payload(is_temporary=True, expires_at=None))

    with pytest.raises(ValueError):
        UserPermission(
            **_user_permission_payload(conditions="invalid", expires_at=_future())
        )

    perm = UserPermission(
        **_user_permission_payload(is_temporary=True, expires_at=_future())
    )
    key = perm.get_permission_key()
    assert "user" in key

    other = UserPermission(
        **_user_permission_payload(
            id="other", permission_type=PermissionType.WRITE, expires_at=_future()
        )
    )
    assert perm.can_be_combined_with(other) is True
    assert (
        perm.conflicts_with(
            UserPermission(
                **_user_permission_payload(id="different", expires_at=_future())
            )
        )
        is True
    )

    dict_conditions = UserPermission(
        **_user_permission_payload(
            conditions={"status": "active"}, expires_at=_future()
        )
    )
    assert dict_conditions.conditions == {"status": "active"}

    new_expiry = _future(120)
    perm.extend_expiry(new_expiry)
    assert perm.expires_at == new_expiry
    perm.revoke()
    assert perm.is_active is False

    with pytest.raises(ValueError):
        perm.extend_expiry(datetime.utcnow() - timedelta(seconds=1))


def test_permission_inheritance_validations() -> None:
    with pytest.raises(ValueError):
        PermissionInheritance(
            id="inh",
            source_permission_id="p1",
            target_permission_id="p1",
            inheritance_type="direct",
            inheritance_path=["p1", "p1"],
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            created_by_user_id="admin",
            depth=1,
        )

    with pytest.raises(ValueError):
        PermissionInheritance(
            id="inh",
            source_permission_id="p1",
            target_permission_id="p2",
            inheritance_type="direct",
            inheritance_path=["p2"],
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            created_by_user_id="admin",
            depth=1,
        )

    inheritance = PermissionInheritance(
        id="inh",
        source_permission_id="p1",
        target_permission_id="p2",
        inheritance_type="direct",
        inheritance_path=["p1", "p2"],
        created_at=datetime.utcnow(),
        modified_at=datetime.utcnow(),
        created_by_user_id="admin",
        depth=1,
    )

    assert inheritance.get_direct_parent() == "p1"
    assert inheritance.is_direct_inheritance() is True
    assert inheritance.affects_permission("p2") is True
    inheritance.break_inheritance()
    assert inheritance.is_active is False
    inheritance.reactivate_inheritance()
    assert inheritance.is_active is True
    assert inheritance.get_inheritance_chain() == ["p1", "p2"]

    inheritance.conditions = {"active": True}
    assert inheritance.conditions == {"active": True}
