"""Comprehensive unit tests for permissions models."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError as PydanticValidationError

from zoho_creator_sdk.models import (
    Permission,
    PermissionInheritance,
    Role,
    UserPermission,
)
from zoho_creator_sdk.models.enums import EntityType, PermissionType


class TestPermission:
    """Test cases for Permission model."""

    def test_permission_minimal_user_assignment(self) -> None:
        """Permission can be created with user assignment only."""
        now = datetime.utcnow()
        permission = Permission(
            id="perm_123",
            name="Read Access",
            entity_type=EntityType.APPLICATION,
            entity_id="app_456",
            permission_type=PermissionType.READ,
            granted_to_user_id="user_789",
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )

        assert permission.id == "perm_123"
        assert permission.granted_to_user_id == "user_789"
        assert permission.granted_to_role_id is None
        assert permission.get_target_id() == "user_789"
        assert permission.get_target_type() == "user"

    def test_permission_minimal_role_assignment(self) -> None:
        """Permission can be created with role assignment only."""
        now = datetime.utcnow()
        permission = Permission(
            id="perm_456",
            name="Write Access",
            entity_type=EntityType.FORM,
            entity_id="form_123",
            permission_type=PermissionType.WRITE,
            granted_to_role_id="role_789",
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )

        assert permission.id == "perm_456"
        assert permission.granted_to_user_id is None
        assert permission.granted_to_role_id == "role_789"
        assert permission.get_target_id() == "role_789"
        assert permission.get_target_type() == "role"

    def test_permission_complete_creation(self) -> None:
        """Permission can be created with all fields."""
        now = datetime.utcnow()
        expiry = now + timedelta(days=30)
        permission = Permission(
            id="perm_complete",
            name="Complete Permission",
            entity_type=EntityType.REPORT,
            entity_id="report_123",
            permission_type=PermissionType.EXPORT,
            granted_to_user_id="user_123",
            granted_by_user_id="admin_456",
            conditions={"field": "status", "values": ["active", "pending"]},
            is_active=True,
            expires_at=expiry,
            created_at=now,
            modified_at=now,
            description="Full permission for testing",
            scope="limited",
            priority=5,
            is_inherited=False,
            parent_permission_id=None,
        )

        assert permission.conditions == {
            "field": "status",
            "values": ["active", "pending"],
        }
        assert permission.is_active is True
        assert permission.expires_at == expiry
        assert permission.priority == 5
        assert permission.is_inherited is False

    def test_permission_validation_neither_user_nor_role(self) -> None:
        """Permission raises error when assigned to neither user nor role."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            Permission(
                id="perm_error",
                name="Error Permission",
                entity_type=EntityType.APPLICATION,
                entity_id="app_123",
                permission_type=PermissionType.READ,
                granted_by_user_id="admin_001",
                created_at=now,
                modified_at=now,
                # Missing both granted_to_user_id and granted_to_role_id
            )

        assert "Permission must be granted to either a user or role" in str(
            exc_info.value
        )

    def test_permission_validation_both_user_and_role(self) -> None:
        """Permission raises error when assigned to both user and role."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            Permission(
                id="perm_error",
                name="Error Permission",
                entity_type=EntityType.APPLICATION,
                entity_id="app_123",
                permission_type=PermissionType.READ,
                granted_to_user_id="user_123",
                granted_to_role_id="role_456",
                granted_by_user_id="admin_001",
                created_at=now,
                modified_at=now,
            )

        assert "Permission cannot be granted to both user and role" in str(
            exc_info.value
        )

    def test_permission_validation_expiry_in_past(self) -> None:
        """Permission raises error when expiry date is in the past."""
        now = datetime.utcnow()
        past_expiry = now - timedelta(days=1)

        with pytest.raises(PydanticValidationError) as exc_info:
            Permission(
                id="perm_expired",
                name="Expired Permission",
                entity_type=EntityType.APPLICATION,
                entity_id="app_123",
                permission_type=PermissionType.READ,
                granted_to_user_id="user_123",
                granted_by_user_id="admin_001",
                expires_at=past_expiry,
                created_at=now,
                modified_at=now,
            )

        assert "Permission expiry date must be in the future" in str(exc_info.value)

    def test_permission_validation_conditions_not_dict(self) -> None:
        """Permission raises error when conditions is not a dictionary."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            Permission(
                id="perm_error",
                name="Error Permission",
                entity_type=EntityType.APPLICATION,
                entity_id="app_123",
                permission_type=PermissionType.READ,
                granted_to_user_id="user_123",
                granted_by_user_id="admin_001",
                conditions="not_a_dict",  # Invalid type
                created_at=now,
                modified_at=now,
            )

        assert "Input should be a valid dictionary" in str(exc_info.value)

    def test_permission_is_expired_no_expiry(self) -> None:
        """Permission is_expired returns False when no expiry set."""
        now = datetime.utcnow()
        permission = Permission(
            id="perm_no_expiry",
            name="No Expiry",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_to_user_id="user_123",
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )

        assert permission.is_expired() is False

    def test_permission_is_expired_future_expiry(self) -> None:
        """Permission is_expired returns False when expiry is in future."""
        now = datetime.utcnow()
        future_expiry = now + timedelta(days=30)
        permission = Permission(
            id="perm_future",
            name="Future Expiry",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_to_user_id="user_123",
            granted_by_user_id="admin_001",
            expires_at=future_expiry,
            created_at=now,
            modified_at=now,
        )

        assert permission.is_expired() is False

    def test_permission_is_expired_past_expiry(self) -> None:
        """Permission is_expired returns True when expiry is in past."""
        now = datetime.utcnow()
        future_expiry = now + timedelta(
            days=1
        )  # Create with future expiry to pass validation
        permission = Permission(
            id="perm_past",
            name="Past Expiry",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_to_user_id="user_123",
            granted_by_user_id="admin_001",
            expires_at=future_expiry,
            created_at=now,
            modified_at=now,
        )
        # Manually set to past expiry to test is_expired method
        permission.expires_at = now - timedelta(days=1)

        assert permission.is_expired() is True

    def test_permission_is_effective_active_not_expired(self) -> None:
        """Permission is_effective returns True when active and not expired."""
        now = datetime.utcnow()
        permission = Permission(
            id="perm_effective",
            name="Effective Permission",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_to_user_id="user_123",
            granted_by_user_id="admin_001",
            is_active=True,
            created_at=now,
            modified_at=now,
        )

        assert permission.is_effective() is True

    def test_permission_is_effective_inactive(self) -> None:
        """Permission is_effective returns False when inactive."""
        now = datetime.utcnow()
        permission = Permission(
            id="perm_inactive",
            name="Inactive Permission",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_to_user_id="user_123",
            granted_by_user_id="admin_001",
            is_active=False,
            created_at=now,
            modified_at=now,
        )

        assert permission.is_effective() is False

    def test_permission_is_effective_expired(self) -> None:
        """Permission is_effective returns False when expired."""
        now = datetime.utcnow()
        future_expiry = now + timedelta(
            days=1
        )  # Create with future expiry to pass validation
        permission = Permission(
            id="perm_expired_effective",
            name="Expired Effective Permission",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_to_user_id="user_123",
            granted_by_user_id="admin_001",
            is_active=True,
            expires_at=future_expiry,
            created_at=now,
            modified_at=now,
        )
        # Manually set to past expiry to test is_effective method
        permission.expires_at = now - timedelta(days=1)

        assert permission.is_effective() is False

    def test_permission_get_target_id_no_assignment_error(self) -> None:
        """Permission get_target_id raises error when not assigned."""
        # Create a valid permission first, then manually clear to test error handling
        permission = Permission(
            id="perm_invalid",
            name="Invalid Permission",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_to_user_id="user_123",  # Provide valid user to pass validation
            granted_by_user_id="admin_001",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
        )

        # Manually clear both to test error handling
        permission.granted_to_user_id = None
        permission.granted_to_role_id = None

        with pytest.raises(ValueError) as exc_info:
            permission.get_target_id()

        assert "Permission is not assigned to any user or role" in str(exc_info.value)

    def test_permission_get_target_type_no_assignment_error(self) -> None:
        """Permission get_target_type raises error when not assigned."""
        # Create a valid permission first, then manually clear to test error handling
        permission = Permission(
            id="perm_invalid",
            name="Invalid Permission",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_to_user_id="user_123",  # Provide valid user to pass validation
            granted_by_user_id="admin_001",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
        )

        # Manually clear both to test error handling
        permission.granted_to_user_id = None
        permission.granted_to_role_id = None

        with pytest.raises(ValueError) as exc_info:
            permission.get_target_type()

        assert "Permission is not assigned to any user or role" in str(exc_info.value)

    def test_permission_validation_conditions_not_dict_field_validator(self) -> None:
        """Permission raises error when conditions is not a dictionary
        via field validator."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            Permission(
                id="perm_cond_invalid",
                name="Invalid Conditions",
                entity_type=EntityType.FORM,
                entity_id="form_123",
                permission_type=PermissionType.READ,
                granted_to_user_id="user_123",
                granted_by_user_id="admin_001",
                conditions="invalid_string",  # Not a dict
                created_at=now,
                modified_at=now,
            )

        # Pydantic's built-in type validation runs before our custom validator
        assert "Input should be a valid dictionary" in str(exc_info.value)

    def test_permission_validate_conditions_format_direct(self) -> None:
        """Test Permission.validate_conditions_format directly
        to trigger ValueError."""
        from zoho_creator_sdk.models.permissions import Permission

        # Call the validator directly to bypass Pydantic's type validation
        with pytest.raises(ValueError) as exc_info:
            Permission.validate_conditions_format("not_a_dict")

        assert "Conditions must be a dictionary" in str(exc_info.value)

    def test_user_permission_validation_conditions_not_dict_field_validator(
        self,
    ) -> None:
        """UserPermission raises error when conditions is not a dictionary
        via field validator."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            UserPermission(
                id="user_perm_cond_invalid",
                user_id="user_123",
                entity_type=EntityType.FORM,
                entity_id="form_123",
                permission_type=PermissionType.READ,
                granted_by_user_id="admin_001",
                conditions="invalid_string",  # Not a dict
                created_at=now,
                modified_at=now,
            )

        # Pydantic's built-in type validation runs before our custom validator
        assert "Input should be a valid dictionary" in str(exc_info.value)

    def test_user_permission_validate_conditions_format_direct(self) -> None:
        """Test UserPermission.validate_conditions_format directly
        to trigger ValueError."""
        from zoho_creator_sdk.models.permissions import UserPermission

        # Call the validator directly to bypass Pydantic's type validation
        with pytest.raises(ValueError) as exc_info:
            UserPermission.validate_conditions_format("not_a_dict")

        assert "Conditions must be a dictionary" in str(exc_info.value)


class TestRole:
    """Test cases for Role model."""

    def test_role_minimal_creation(self) -> None:
        """Role can be created with minimal required fields."""
        now = datetime.utcnow()
        role = Role(
            id="role_123",
            name="Basic Role",
            display_name="Basic User Role",
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
        )

        assert role.id == "role_123"
        assert role.name == "Basic Role"
        assert role.display_name == "Basic User Role"
        assert role.permission_ids == []
        assert role.is_active is True
        assert role.is_system_role is False

    def test_role_complete_creation(self) -> None:
        """Role can be created with all fields."""
        now = datetime.utcnow()
        role = Role(
            id="role_complete",
            name="Complete Role",
            display_name="Complete User Role",
            description="A comprehensive role with full permissions",
            permission_ids=["perm_1", "perm_2", "perm_3"],
            is_active=True,
            is_system_role=False,
            parent_role_id="parent_123",
            child_role_ids=["child_1", "child_2"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            color_code="#FF5733",
            icon="shield",
            priority=50,
            max_users=100,
            current_user_count=25,
            tags=["admin", "power_user", "full_access"],
        )

        assert len(role.permission_ids) == 3
        assert role.parent_role_id == "parent_123"
        assert len(role.child_role_ids) == 2
        assert role.color_code == "#FF5733"
        assert role.icon == "shield"
        assert role.priority == 50
        assert role.max_users == 100
        assert role.current_user_count == 25
        assert role.tags == ["admin", "power_user", "full_access"]

    def test_role_validation_parent_is_self(self) -> None:
        """Role raises error when trying to be its own parent."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            Role(
                id="role_self_parent",
                name="Self Parent Role",
                display_name="Invalid Role",
                parent_role_id="role_self_parent",  # Same as id
                created_at=now,
                modified_at=now,
                created_by_user_id="admin_001",
            )

        assert "Role cannot be its own parent" in str(exc_info.value)

    def test_role_validation_user_capacity_exceeded(self) -> None:
        """Role raises error when current users exceed maximum."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            Role(
                id="role_capacity",
                name="Capacity Error Role",
                display_name="Over Capacity Role",
                max_users=10,
                current_user_count=15,  # Exceeds max_users
                created_at=now,
                modified_at=now,
                created_by_user_id="admin_001",
            )

        assert "Current user count cannot exceed maximum users" in str(exc_info.value)

    def test_role_has_permission(self) -> None:
        """Role has_permission checks for specific permission ID."""
        now = datetime.utcnow()
        role = Role(
            id="role_check",
            name="Check Role",
            display_name="Permission Check Role",
            permission_ids=["perm_read", "perm_write", "perm_delete"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
        )

        assert role.has_permission("perm_read") is True
        assert role.has_permission("perm_write") is True
        assert role.has_permission("perm_admin") is False

    def test_role_has_any_permission(self) -> None:
        """Role has_any_permission checks for any of multiple permissions."""
        now = datetime.utcnow()
        role = Role(
            id="role_any",
            name="Any Role",
            display_name="Any Permission Role",
            permission_ids=["perm_read", "perm_write", "perm_delete"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
        )

        assert role.has_any_permission(["perm_read", "perm_admin"]) is True
        assert role.has_any_permission(["perm_admin", "perm_super"]) is False

    def test_role_has_all_permissions(self) -> None:
        """Role has_all_permissions checks for all specified permissions."""
        now = datetime.utcnow()
        role = Role(
            id="role_all",
            name="All Role",
            display_name="All Permissions Role",
            permission_ids=["perm_read", "perm_write", "perm_delete"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
        )

        assert role.has_all_permissions(["perm_read", "perm_write"]) is True
        assert (
            role.has_all_permissions(
                ["perm_read", "perm_write", "perm_delete", "perm_admin"]
            )
            is False
        )

    def test_role_add_permission(self) -> None:
        """Role add_permission adds permission if not already present."""
        now = datetime.utcnow()
        role = Role(
            id="role_add",
            name="Add Role",
            display_name="Add Permission Role",
            permission_ids=["perm_read", "perm_write"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
        )

        # Add new permission
        role.add_permission("perm_delete")
        assert "perm_delete" in role.permission_ids
        assert len(role.permission_ids) == 3

        # Add existing permission (no change)
        role.add_permission("perm_read")
        assert len(role.permission_ids) == 3

    def test_role_remove_permission(self) -> None:
        """Role remove_permission removes permission if present."""
        now = datetime.utcnow()
        role = Role(
            id="role_remove",
            name="Remove Role",
            display_name="Remove Permission Role",
            permission_ids=["perm_read", "perm_write", "perm_delete"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
        )

        # Remove existing permission
        role.remove_permission("perm_write")
        assert "perm_write" not in role.permission_ids
        assert len(role.permission_ids) == 2

        # Remove non-existing permission (no change)
        role.remove_permission("perm_admin")
        assert len(role.permission_ids) == 2

    def test_role_get_permission_count(self) -> None:
        """Role get_permission_count returns number of permissions."""
        now = datetime.utcnow()
        role = Role(
            id="role_count",
            name="Count Role",
            display_name="Permission Count Role",
            permission_ids=["perm_1", "perm_2", "perm_3", "perm_4", "perm_5"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
        )

        assert role.get_permission_count() == 5

    def test_role_is_parent_of(self) -> None:
        """Role is_parent_of checks if role is parent of specified role."""
        now = datetime.utcnow()
        role = Role(
            id="role_parent",
            name="Parent Role",
            display_name="Parent Role",
            child_role_ids=["child_1", "child_2", "child_3"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
        )

        assert role.is_parent_of("child_1") is True
        assert role.is_parent_of("child_4") is False

    def test_role_can_accommodate_users_unlimited(self) -> None:
        """Role can_accommodate_users returns True when no max_users limit."""
        now = datetime.utcnow()
        role = Role(
            id="role_unlimited",
            name="Unlimited Role",
            display_name="Unlimited Role",
            current_user_count=50,
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
        )

        assert role.can_accommodate_users(100) is True
        assert role.can_accommodate_users(1000) is True

    def test_role_can_accommodate_users_limited(self) -> None:
        """Role can_accommodate_users checks against max_users limit."""
        now = datetime.utcnow()
        role = Role(
            id="role_limited",
            name="Limited Role",
            display_name="Limited Role",
            max_users=100,
            current_user_count=80,
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
        )

        assert role.can_accommodate_users(15) is True  # 80 + 15 = 95 <= 100
        assert role.can_accommodate_users(25) is False  # 80 + 25 = 105 > 100

    def test_role_get_available_slots_none_when_unlimited(self) -> None:
        """Role get_available_slots returns None when no max_users limit."""
        now = datetime.utcnow()
        role = Role(
            id="role_slots_none",
            name="No Slots Role",
            display_name="No Slots Role",
            max_users=None,
            current_user_count=50,
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
        )

        assert role.get_available_slots() is None

    def test_role_get_available_slots_when_limited(self) -> None:
        """Role get_available_slots returns available slots when limited."""
        now = datetime.utcnow()
        role = Role(
            id="role_slots_limited",
            name="Limited Slots Role",
            display_name="Limited Slots Role",
            max_users=100,
            current_user_count=30,
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
        )

        assert role.get_available_slots() == 70  # 100 - 30 = 70


class TestUserPermission:
    """Test cases for UserPermission model."""

    def test_user_permission_minimal_creation(self) -> None:
        """UserPermission can be created with minimal required fields."""
        now = datetime.utcnow()
        permission = UserPermission(
            id="user_perm_123",
            user_id="user_456",
            entity_type=EntityType.APPLICATION,
            entity_id="app_789",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )

        assert permission.id == "user_perm_123"
        assert permission.user_id == "user_456"
        assert permission.is_temporary is False
        assert permission.reason is None

    def test_user_permission_complete_creation(self) -> None:
        """UserPermission can be created with all fields."""
        now = datetime.utcnow()
        expiry = now + timedelta(days=7)
        permission = UserPermission(
            id="user_perm_complete",
            user_id="user_789",
            entity_type=EntityType.FORM,
            entity_id="form_123",
            permission_type=PermissionType.WRITE,
            granted_by_user_id="admin_001",
            conditions={"field": "status", "required": True},
            is_active=True,
            expires_at=expiry,
            created_at=now,
            modified_at=now,
            description="Temporary write access",
            scope="form_specific",
            priority=3,
            is_temporary=True,
            reason="Temporary project access request",
        )

        assert permission.conditions == {"field": "status", "required": True}
        assert permission.is_temporary is True
        assert permission.reason == "Temporary project access request"

    def test_user_permission_validation_expiry_in_past(self) -> None:
        """UserPermission raises error when expiry date is in past."""
        now = datetime.utcnow()
        past_expiry = now - timedelta(hours=1)

        with pytest.raises(PydanticValidationError) as exc_info:
            UserPermission(
                id="user_perm_expired",
                user_id="user_123",
                entity_type=EntityType.APPLICATION,
                entity_id="app_123",
                permission_type=PermissionType.READ,
                granted_by_user_id="admin_001",
                expires_at=past_expiry,
                created_at=now,
                modified_at=now,
            )

        assert "Permission expiry date must be in the future" in str(exc_info.value)

    def test_user_permission_validation_temporary_no_expiry(self) -> None:
        """UserPermission raises error when temporary permission has no expiry."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            UserPermission(
                id="user_perm_temp_no_expiry",
                user_id="user_123",
                entity_type=EntityType.APPLICATION,
                entity_id="app_123",
                permission_type=PermissionType.READ,
                granted_by_user_id="admin_001",
                is_temporary=True,
                # Missing expires_at
                created_at=now,
                modified_at=now,
            )

        assert "Temporary permissions must have an expiry date" in str(exc_info.value)

    def test_user_permission_get_permission_key(self) -> None:
        """UserPermission get_permission_key returns unique permission key."""
        now = datetime.utcnow()
        permission = UserPermission(
            id="user_perm_key",
            user_id="user_123",
            entity_type=EntityType.FORM,
            entity_id="form_456",
            permission_type=PermissionType.WRITE,
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )

        key = permission.get_permission_key()
        assert "user_123:form:form_456:write" == key

    def test_user_permission_conflicts_with_same_permission(self) -> None:
        """UserPermission conflicts_with returns True for identical permissions."""
        now = datetime.utcnow()
        permission1 = UserPermission(
            id="user_perm_1",
            user_id="user_123",
            entity_type=EntityType.FORM,
            entity_id="form_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )
        permission2 = UserPermission(
            id="user_perm_2",
            user_id="user_123",
            entity_type=EntityType.FORM,
            entity_id="form_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )

        assert permission1.conflicts_with(permission2) is True
        assert permission2.conflicts_with(permission1) is True

    def test_user_permission_conflicts_with_different_permission(self) -> None:
        """UserPermission conflicts_with returns False for different
        permission types."""
        now = datetime.utcnow()
        permission1 = UserPermission(
            id="user_perm_read",
            user_id="user_123",
            entity_type=EntityType.FORM,
            entity_id="form_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )
        permission2 = UserPermission(
            id="user_perm_write",
            user_id="user_123",
            entity_type=EntityType.FORM,
            entity_id="form_123",
            permission_type=PermissionType.WRITE,
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )

        assert permission1.conflicts_with(permission2) is False
        assert permission2.conflicts_with(permission1) is False

    def test_user_permission_can_be_combined_with_different_type(self) -> None:
        """UserPermission can_be_combined_with returns True for different
        permission types."""
        now = datetime.utcnow()
        permission1 = UserPermission(
            id="user_perm_read",
            user_id="user_123",
            entity_type=EntityType.FORM,
            entity_id="form_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )
        permission2 = UserPermission(
            id="user_perm_write",
            user_id="user_123",
            entity_type=EntityType.FORM,
            entity_id="form_123",
            permission_type=PermissionType.WRITE,
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )

        assert permission1.can_be_combined_with(permission2) is True
        assert permission2.can_be_combined_with(permission1) is True

    def test_user_permission_can_be_combined_with_same_type(self) -> None:
        """UserPermission can_be_combined_with returns False for same
        permission type."""
        now = datetime.utcnow()
        permission1 = UserPermission(
            id="user_perm_1",
            user_id="user_123",
            entity_type=EntityType.FORM,
            entity_id="form_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )
        permission2 = UserPermission(
            id="user_perm_2",
            user_id="user_123",
            entity_type=EntityType.FORM,
            entity_id="form_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )

        assert permission1.can_be_combined_with(permission2) is False
        assert permission2.can_be_combined_with(permission1) is False

    def test_user_permission_extend_expiry_future_date(self) -> None:
        """UserPermission extend_expiry extends expiry to future date."""
        now = datetime.utcnow()
        new_expiry = now + timedelta(days=14)
        permission = UserPermission(
            id="user_perm_extend",
            user_id="user_123",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            expires_at=now + timedelta(days=1),
            created_at=now,
            modified_at=now,
        )

        permission.extend_expiry(new_expiry)
        assert permission.expires_at == new_expiry

    def test_user_permission_extend_expiry_past_date(self) -> None:
        """UserPermission extend_expiry raises error for past date."""
        now = datetime.utcnow()
        past_date = now - timedelta(days=1)
        permission = UserPermission(
            id="user_perm_extend",
            user_id="user_123",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            created_at=now,
            modified_at=now,
        )

        with pytest.raises(ValueError) as exc_info:
            permission.extend_expiry(past_date)

        assert "New expiry date must be in the future" in str(exc_info.value)

    def test_user_permission_revoke(self) -> None:
        """UserPermission revoke deactivates the permission."""
        now = datetime.utcnow()
        permission = UserPermission(
            id="user_perm_revoke",
            user_id="user_123",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            is_active=True,
            created_at=now,
            modified_at=now,
        )

        assert permission.is_active is True
        permission.revoke()
        assert permission.is_active is False

    def test_user_permission_is_expired_no_expiry(self) -> None:
        """UserPermission is_expired returns False when no expiry is set."""
        now = datetime.utcnow()
        permission = UserPermission(
            id="user_perm_no_expiry",
            user_id="user_123",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            # No expires_at specified
            created_at=now,
            modified_at=now,
        )

        assert permission.is_expired() is False

    def test_user_permission_is_expired_with_expiry(self) -> None:
        """UserPermission is_expired returns True when expiry is in past."""
        now = datetime.utcnow()
        # Create permission with future expiry first, then modify it to past
        permission = UserPermission(
            id="user_perm_expired",
            user_id="user_123",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            expires_at=now + timedelta(days=1),  # Future date to pass validation
            created_at=now,
            modified_at=now,
        )

        # Manually set to past expiry for testing
        past_expiry = now - timedelta(days=1)
        permission.expires_at = past_expiry

        assert permission.is_expired() is True

    def test_user_permission_is_effective(self) -> None:
        """UserPermission is_effective returns True when active and not expired."""
        now = datetime.utcnow()
        future_expiry = now + timedelta(days=1)
        permission = UserPermission(
            id="user_perm_effective",
            user_id="user_123",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            is_active=True,
            expires_at=future_expiry,
            created_at=now,
            modified_at=now,
        )

        assert permission.is_effective() is True

    def test_user_permission_is_effective_inactive(self) -> None:
        """UserPermission is_effective returns False when inactive."""
        now = datetime.utcnow()
        permission = UserPermission(
            id="user_perm_inactive",
            user_id="user_123",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            is_active=False,
            created_at=now,
            modified_at=now,
        )

        assert permission.is_effective() is False

    def test_user_permission_is_effective_expired(self) -> None:
        """UserPermission is_effective returns False when expired."""
        now = datetime.utcnow()
        # Create permission with future expiry first, then modify it to past
        permission = UserPermission(
            id="user_perm_expired_effective",
            user_id="user_123",
            entity_type=EntityType.APPLICATION,
            entity_id="app_123",
            permission_type=PermissionType.READ,
            granted_by_user_id="admin_001",
            is_active=True,
            expires_at=now + timedelta(days=1),  # Future date to pass validation
            created_at=now,
            modified_at=now,
        )

        # Manually set to past expiry for testing
        past_expiry = now - timedelta(days=1)
        permission.expires_at = past_expiry

        assert permission.is_effective() is False


class TestPermissionInheritance:
    """Test cases for PermissionInheritance model."""

    def test_permission_inheritance_minimal_creation(self) -> None:
        """PermissionInheritance can be created with minimal required fields."""
        now = datetime.utcnow()
        inheritance = PermissionInheritance(
            id="inherit_123",
            source_permission_id="perm_source_456",
            target_permission_id="perm_target_789",
            inheritance_type="direct",
            inheritance_path=["perm_source_456", "perm_target_789"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=1,
        )

        assert inheritance.id == "inherit_123"
        assert inheritance.source_permission_id == "perm_source_456"
        assert inheritance.target_permission_id == "perm_target_789"
        assert inheritance.inheritance_type == "direct"
        assert inheritance.depth == 1
        assert inheritance.is_active is True

    def test_permission_inheritance_complete_creation(self) -> None:
        """PermissionInheritance can be created with all fields."""
        now = datetime.utcnow()
        inheritance = PermissionInheritance(
            id="inherit_complete",
            source_permission_id="perm_source_complete",
            target_permission_id="perm_target_complete",
            inheritance_type="role_hierarchy",
            inheritance_path=[
                "perm_source_complete",
                "middle",
                "parent",
                "perm_target_complete",
            ],
            is_active=True,
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=3,
            conditions={"propagation": "enabled", "level": "full"},
        )

        assert len(inheritance.inheritance_path) == 4
        assert inheritance.depth == 3
        assert inheritance.conditions == {"propagation": "enabled", "level": "full"}

    def test_permission_inheritance_validation_empty_path(self) -> None:
        """PermissionInheritance raises error when inheritance path is empty."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            PermissionInheritance(
                id="inherit_empty_path",
                source_permission_id="perm_source",
                target_permission_id="perm_target",
                inheritance_type="direct",
                inheritance_path=[],  # Empty path
                created_at=now,
                modified_at=now,
                created_by_user_id="admin_001",
            )

        assert "Inheritance path cannot be empty" in str(exc_info.value)

    def test_permission_inheritance_validation_too_short_path(self) -> None:
        """PermissionInheritance raises error when path has only one element."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            PermissionInheritance(
                id="inherit_short_path",
                source_permission_id="perm_source",
                target_permission_id="perm_target",
                inheritance_type="direct",
                inheritance_path=["only_one"],  # Only one element
                created_at=now,
                modified_at=now,
                created_by_user_id="admin_001",
            )

        assert "Inheritance path must contain at least source and target" in str(
            exc_info.value
        )

    def test_permission_inheritance_validation_same_source_target(self) -> None:
        """PermissionInheritance raises error when source and target are the same."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            PermissionInheritance(
                id="inherit_same",
                source_permission_id="perm_same",
                target_permission_id="perm_same",
                inheritance_type="direct",
                inheritance_path=["perm_same", "perm_same"],
                created_at=now,
                modified_at=now,
                created_by_user_id="admin_001",
                depth=1,
            )

        assert "Source and target permissions cannot be the same" in str(exc_info.value)

    def test_permission_inheritance_get_inheritance_chain(self) -> None:
        """PermissionInheritance get_inheritance_chain returns the
        inheritance path as list."""
        path = ["source", "intermediate1", "intermediate2", "target"]
        now = datetime.utcnow()
        inheritance = PermissionInheritance(
            id="inherit_chain",
            source_permission_id="source",
            target_permission_id="target",
            inheritance_type="multi_level",
            inheritance_path=path,
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=3,
        )

        chain = inheritance.get_inheritance_chain()
        assert chain == path
        assert inheritance.get_inheritance_distance() == 3

    def test_permission_inheritance_get_direct_parent(self) -> None:
        """PermissionInheritance get_direct_parent returns immediate parent."""
        path = ["source", "parent", "target"]
        now = datetime.utcnow()
        inheritance = PermissionInheritance(
            id="inherit_direct",
            source_permission_id="source",
            target_permission_id="target",
            inheritance_type="multi_level",
            inheritance_path=path,
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=2,
        )

        parent = inheritance.get_direct_parent()
        assert parent == "parent"

    def test_permission_inheritance_get_direct_parent_direct_inheritance(self) -> None:
        """PermissionInheritance get_direct_parent returns source for
        direct inheritance."""
        now = datetime.utcnow()
        inheritance = PermissionInheritance(
            id="inherit_direct_only",
            source_permission_id="source",
            target_permission_id="target",
            inheritance_type="direct",
            inheritance_path=["source", "target"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=1,
        )

        parent = inheritance.get_direct_parent()
        assert parent == "source"

    def test_permission_inheritance_is_direct_inheritance(self) -> None:
        """PermissionInheritance is_direct_inheritance checks for single hop."""
        now = datetime.utcnow()
        direct_inheritance = PermissionInheritance(
            id="inherit_direct",
            source_permission_id="source",
            target_permission_id="target",
            inheritance_type="direct",
            inheritance_path=["source", "target"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=1,
        )
        multi_level_inheritance = PermissionInheritance(
            id="inherit_multi",
            source_permission_id="source",
            target_permission_id="target",
            inheritance_type="multi_level",
            inheritance_path=["source", "intermediate", "target"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=2,
        )

        assert direct_inheritance.is_direct_inheritance() is True
        assert multi_level_inheritance.is_direct_inheritance() is False

    def test_permission_inheritance_affects_permission(self) -> None:
        """PermissionInheritance affects_permission checks if permission
        is in inheritance chain."""
        path = ["source", "intermediate", "target"]
        now = datetime.utcnow()
        inheritance = PermissionInheritance(
            id="inherit_affects",
            source_permission_id="source",
            target_permission_id="target",
            inheritance_type="chain",
            inheritance_path=path,
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=3,
        )

        assert inheritance.affects_permission("source") is True
        assert inheritance.affects_permission("intermediate") is True
        assert inheritance.affects_permission("target") is True
        assert inheritance.affects_permission("not_in_chain") is False

    def test_permission_inheritance_break_inheritance(self) -> None:
        """PermissionInheritance break_inheritance deactivates the inheritance."""
        now = datetime.utcnow()
        inheritance = PermissionInheritance(
            id="inherit_break",
            source_permission_id="source",
            target_permission_id="target",
            inheritance_type="direct",
            inheritance_path=["source", "target"],
            is_active=True,
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=1,
        )

        assert inheritance.is_active is True
        inheritance.break_inheritance()
        assert inheritance.is_active is False

    def test_permission_inheritance_reactivate_inheritance(self) -> None:
        """PermissionInheritance reactivate_inheritance reactivates the inheritance."""
        now = datetime.utcnow()
        inheritance = PermissionInheritance(
            id="inherit_reactivate",
            source_permission_id="source",
            target_permission_id="target",
            inheritance_type="direct",
            inheritance_path=["source", "target"],
            is_active=False,
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=1,
        )

        assert inheritance.is_active is False
        inheritance.reactivate_inheritance()
        assert inheritance.is_active is True

    def test_permission_inheritance_is_multi_level_inheritance(self) -> None:
        """PermissionInheritance is_multi_level_inheritance checks for multiple hops."""
        now = datetime.utcnow()
        direct_inheritance = PermissionInheritance(
            id="inherit_direct_check",
            source_permission_id="source",
            target_permission_id="target",
            inheritance_type="direct",
            inheritance_path=["source", "target"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=1,
        )
        multi_level_inheritance = PermissionInheritance(
            id="inherit_multi_check",
            source_permission_id="source",
            target_permission_id="target",
            inheritance_type="multi_level",
            inheritance_path=["source", "intermediate1", "intermediate2", "target"],
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=3,
        )

        assert direct_inheritance.is_multi_level_inheritance() is False
        assert multi_level_inheritance.is_multi_level_inheritance() is True

    def test_permission_inheritance_get_affected_permissions(self) -> None:
        """PermissionInheritance get_affected_permissions returns list
        of all permissions in path."""
        path = ["source", "intermediate1", "intermediate2", "target"]
        now = datetime.utcnow()
        inheritance = PermissionInheritance(
            id="inherit_affected",
            source_permission_id="source",
            target_permission_id="target",
            inheritance_type="chain",
            inheritance_path=path,
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=3,
        )

        affected = inheritance.get_affected_permissions()
        assert affected == path
        assert len(affected) == 4

    def test_permission_inheritance_validation_path_wrong_start(self) -> None:
        """PermissionInheritance raises error when path doesn't start
        with source permission."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            PermissionInheritance(
                id="inherit_wrong_start",
                source_permission_id="source_perm",
                target_permission_id="target_perm",
                inheritance_type="chain",
                inheritance_path=["wrong_start", "middle", "target_perm"],
                created_at=now,
                modified_at=now,
                created_by_user_id="admin_001",
                depth=2,
            )

        assert "Inheritance path must start with source permission ID" in str(
            exc_info.value
        )

    def test_permission_inheritance_validation_path_wrong_end(self) -> None:
        """PermissionInheritance raises error when path doesn't end with
        target permission."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            PermissionInheritance(
                id="inherit_wrong_end",
                source_permission_id="source_perm",
                target_permission_id="target_perm",
                inheritance_type="chain",
                inheritance_path=["source_perm", "middle", "wrong_end"],
                created_at=now,
                modified_at=now,
                created_by_user_id="admin_001",
                depth=2,
            )

        assert "Inheritance path must end with target permission ID" in str(
            exc_info.value
        )

    def test_permission_inheritance_validation_conditions_not_dict_field_validator(
        self,
    ) -> None:
        """PermissionInheritance raises error when conditions is not a
        dictionary via field validator."""
        now = datetime.utcnow()

        with pytest.raises(PydanticValidationError) as exc_info:
            PermissionInheritance(
                id="inherit_cond_invalid",
                source_permission_id="source_perm",
                target_permission_id="target_perm",
                inheritance_type="direct",
                inheritance_path=["source_perm", "target_perm"],
                conditions="invalid_string",  # Not a dict
                created_at=now,
                modified_at=now,
                created_by_user_id="admin_001",
                depth=1,
            )

        # Pydantic's built-in type validation runs before our custom validator
        assert "Input should be a valid dictionary" in str(exc_info.value)

    def test_permission_inheritance_validate_conditions_format_direct(self) -> None:
        """Test PermissionInheritance.validate_conditions_format
        directly to trigger ValueError."""
        from zoho_creator_sdk.models.permissions import PermissionInheritance

        # Call the validator directly to bypass Pydantic's type validation
        with pytest.raises(ValueError) as exc_info:
            PermissionInheritance.validate_conditions_format("not_a_dict")

        assert "Conditions must be a dictionary" in str(exc_info.value)

    def test_permission_inheritance_get_direct_parent_minimal_path(self) -> None:
        """PermissionInheritance get_direct_parent returns source when
        path has minimal items."""
        now = datetime.utcnow()
        inheritance = PermissionInheritance(
            id="inherit_minimal_parent",
            source_permission_id="source",
            target_permission_id="target",
            inheritance_type="direct",
            inheritance_path=["source", "target"],  # Minimal path (2 items)
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=1,
        )

        parent = inheritance.get_direct_parent()
        assert (
            parent == "source"
        )  # With 2 items, returns the second-to-last (which is "source")

    def test_permission_inheritance_get_direct_parent_fallback(self) -> None:
        """PermissionInheritance get_direct_parent returns source when
        path is too short."""
        now = datetime.utcnow()
        inheritance = PermissionInheritance(
            id="inherit_fallback_parent",
            source_permission_id="source",
            target_permission_id="target",
            inheritance_type="direct",
            inheritance_path=["source", "target"],  # Path with exactly 2 items
            created_at=now,
            modified_at=now,
            created_by_user_id="admin_001",
            depth=1,
        )

        # Manually set a shorter path to trigger the fallback condition
        inheritance.inheritance_path = ["source"]  # Only 1 item

        parent = inheritance.get_direct_parent()
        assert parent == "source"  # Falls back to source_permission_id
