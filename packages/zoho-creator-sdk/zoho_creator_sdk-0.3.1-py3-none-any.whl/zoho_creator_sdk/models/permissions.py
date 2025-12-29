"""
Pydantic models for permissions in the Zoho Creator SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Mapping, Optional, Sequence

from pydantic import Field, field_validator, model_validator

from .base import CreatorBaseModel, validate_enum_value
from .enums import EntityType, PermissionType


class Permission(CreatorBaseModel):
    """Represents a permission assignment for access control."""

    id: str = Field(
        description="The unique identifier of the permission.",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
        examples=["perm_12345", "read_access_app1"],
    )
    name: str = Field(
        description="Human-readable name for the permission.",
        min_length=1,
        max_length=200,
    )
    entity_type: EntityType = Field(
        description="The type of entity this permission applies to."
    )
    entity_id: str = Field(
        description="The ID of the specific entity this permission applies to.",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    permission_type: PermissionType = Field(
        description="The type of permission granted."
    )
    granted_to_user_id: Optional[str] = Field(
        default=None,
        description="The user ID this permission is directly granted to.",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    granted_to_role_id: Optional[str] = Field(
        default=None,
        description="The role ID this permission is granted to.",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    granted_by_user_id: str = Field(
        description="The user ID who granted this permission.",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )

    @field_validator("entity_type", mode="before")
    @classmethod
    def validate_entity_type(cls, v: Any) -> Any:
        return validate_enum_value(EntityType)(v)

    @field_validator("permission_type", mode="before")
    @classmethod
    def validate_permission_type(cls, v: Any) -> Any:
        return validate_enum_value(PermissionType)(v)

    conditions: Optional[Mapping[str, Any]] = Field(
        default=None,
        description="Additional conditions that must be met for this permission.",
    )
    is_active: bool = Field(
        default=True, description="Whether this permission is currently active."
    )
    expires_at: Optional[datetime] = Field(
        default=None, description="Optional expiry time for this permission."
    )
    created_at: datetime = Field(description="The time this permission was created.")
    modified_at: datetime = Field(
        description="The time this permission was last modified."
    )
    description: Optional[str] = Field(
        default=None, description="Optional description of this permission."
    )
    scope: Optional[str] = Field(
        default=None, description="Optional scope limitation for this permission."
    )
    priority: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Priority level (1-10, higher number = higher priority).",
    )
    is_inherited: bool = Field(
        default=False,
        description="Whether this permission is inherited from a parent entity.",
    )
    parent_permission_id: Optional[str] = Field(
        default=None, description="ID of parent permission if this is inherited."
    )

    @model_validator(mode="after")
    def validate_permission_assignment(self) -> "Permission":
        """Validate that permission is assigned to either a user or role."""
        if not self.granted_to_user_id and not self.granted_to_role_id:
            raise ValueError(
                "Permission must be granted to either a user or role. "
                "Specify either granted_to_user_id or granted_to_role_id."
            )
        if self.granted_to_user_id and self.granted_to_role_id:
            raise ValueError(
                "Permission cannot be granted to both user and role simultaneously. "
                "Specify either granted_to_user_id or granted_to_role_id, but not both."
            )
        return self

    @model_validator(mode="after")
    def validate_expiry_date(self) -> "Permission":
        """Validate that expiry date is in the future if provided."""
        if self.expires_at and self.expires_at <= datetime.utcnow():
            raise ValueError(
                "Permission expiry date must be in the future. "
                f"Provided date: {self.expires_at}, current time: {datetime.utcnow()}"
            )
        return self

    @field_validator("conditions")
    @classmethod
    def validate_conditions_format(
        cls, v: Optional[Mapping[str, Any]]
    ) -> Optional[Mapping[str, Any]]:
        """Validate that conditions are properly formatted."""
        if v is not None:
            # Basic validation - ensure conditions is a dictionary
            if not isinstance(v, dict):
                raise ValueError("Conditions must be a dictionary")
        return v

    def is_expired(self) -> bool:
        """Check if the permission has expired."""
        if not self.expires_at:
            return False
        return self.expires_at <= datetime.utcnow()

    def is_effective(self) -> bool:
        """Check if the permission is currently effective (active and not expired)."""
        return self.is_active and not self.is_expired()

    def get_target_id(self) -> str:
        """Get the ID of the target (user or role) this permission is granted to."""
        if self.granted_to_user_id:
            return self.granted_to_user_id
        if self.granted_to_role_id:
            return self.granted_to_role_id
        raise ValueError("Permission is not assigned to any user or role")

    def get_target_type(self) -> str:
        """Get the type of target (user or role) this permission is granted to."""
        if self.granted_to_user_id:
            return "user"
        if self.granted_to_role_id:
            return "role"
        raise ValueError("Permission is not assigned to any user or role")


class Role(CreatorBaseModel):
    """Represents a role with associated permissions for access control."""

    id: str = Field(description="The unique identifier of the role.")
    name: str = Field(description="The name of the role.")
    display_name: str = Field(description="Human-readable display name for the role.")
    description: Optional[str] = Field(
        default=None,
        description="Description of the role's purpose and responsibilities.",
    )
    permission_ids: Sequence[str] = Field(
        default_factory=list,
        description="List of permission IDs associated with this role.",
    )
    is_active: bool = Field(
        default=True, description="Whether this role is currently active."
    )
    is_system_role: bool = Field(
        default=False, description="Whether this is a built-in system role."
    )
    parent_role_id: Optional[str] = Field(
        default=None, description="ID of parent role for inheritance."
    )
    child_role_ids: Sequence[str] = Field(
        default_factory=list,
        description="List of child role IDs that inherit from this role.",
    )
    created_at: datetime = Field(description="The time this role was created.")
    modified_at: datetime = Field(description="The time this role was last modified.")
    created_by_user_id: str = Field(description="The user ID who created this role.")
    color_code: Optional[str] = Field(
        default=None, description="Color code for UI representation of the role."
    )
    icon: Optional[str] = Field(
        default=None, description="Icon identifier for UI representation of the role."
    )
    priority: int = Field(
        default=1,
        ge=1,
        le=100,
        description="Priority level (1-100, higher number = higher priority).",
    )
    max_users: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of users that can be assigned this role.",
    )
    current_user_count: int = Field(
        default=0, ge=0, description="Current number of users assigned to this role."
    )
    tags: Sequence[str] = Field(
        default_factory=list, description="Tags for categorizing and searching roles."
    )

    @field_validator("permission_ids")
    @classmethod
    def validate_permission_ids_not_empty(cls, v: Sequence[str]) -> Sequence[str]:
        """Validate role permissions if provided."""
        if v is not None and len(v) == 0:
            # Allow empty permission list for flexibility
            pass
        return v

    @field_validator("child_role_ids")
    @classmethod
    def validate_child_role_ids_not_empty(cls, v: Sequence[str]) -> Sequence[str]:
        """Validate that child role IDs are properly formatted."""
        if v is not None and len(v) == 0:
            # Allow empty child role list for flexibility
            pass
        return v

    @model_validator(mode="after")
    def validate_role_hierarchy(self) -> "Role":
        """Validate role hierarchy to prevent circular references."""
        if self.parent_role_id and self.parent_role_id == self.id:
            raise ValueError("Role cannot be its own parent")
        return self

    @model_validator(mode="after")
    def validate_user_capacity(self) -> "Role":
        """Validate user capacity constraints."""
        if self.max_users is not None and self.current_user_count > self.max_users:
            raise ValueError("Current user count cannot exceed maximum users")
        return self

    def has_permission(self, permission_id: str) -> bool:
        """Check if this role has a specific permission."""
        return permission_id in self.permission_ids

    def has_any_permission(self, permission_ids: Sequence[str]) -> bool:
        """Check if this role has any of the specified permissions."""
        return any(
            permission_id in self.permission_ids for permission_id in permission_ids
        )

    def has_all_permissions(self, permission_ids: Sequence[str]) -> bool:
        """Check if this role has all of the specified permissions."""
        return all(
            permission_id in self.permission_ids for permission_id in permission_ids
        )

    def add_permission(self, permission_id: str) -> None:
        """Add a permission to this role."""
        if permission_id not in self.permission_ids:
            self.permission_ids = list(self.permission_ids) + [permission_id]

    def remove_permission(self, permission_id: str) -> None:
        """Remove a permission from this role."""
        if permission_id in self.permission_ids:
            permission_list = list(self.permission_ids)
            permission_list.remove(permission_id)
            self.permission_ids = permission_list

    def get_permission_count(self) -> int:
        """Get the number of permissions associated with this role."""
        return len(self.permission_ids)

    def is_parent_of(self, role_id: str) -> bool:
        """Check if this role is a parent of the specified role."""
        return role_id in self.child_role_ids

    def can_accommodate_users(self, additional_users: int) -> bool:
        """Check if this role can accommodate additional users."""
        if self.max_users is None:
            return True
        return (self.current_user_count + additional_users) <= self.max_users

    def get_available_slots(self) -> Optional[int]:
        """Get the number of available user slots for this role."""
        if self.max_users is None:
            return None
        return self.max_users - self.current_user_count


class UserPermission(CreatorBaseModel):
    """Direct user permission assignment (not role-based) for access control."""

    id: str = Field(
        description="The unique identifier of the user permission.",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    user_id: str = Field(
        description="The user ID this permission is granted to.",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    entity_type: EntityType = Field(
        description="The type of entity this permission applies to."
    )
    entity_id: str = Field(
        description="The ID of the specific entity this permission applies to.",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    permission_type: PermissionType = Field(
        description="The type of permission granted."
    )
    granted_by_user_id: str = Field(
        description="The user ID who granted this permission.",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )

    @field_validator("entity_type", mode="before")
    @classmethod
    def validate_entity_type(cls, v: Any) -> Any:
        return validate_enum_value(EntityType)(v)

    @field_validator("permission_type", mode="before")
    @classmethod
    def validate_permission_type(cls, v: Any) -> Any:
        return validate_enum_value(PermissionType)(v)

    conditions: Optional[Mapping[str, Any]] = Field(
        default=None,
        description="Additional conditions that must be met for this permission.",
    )
    is_active: bool = Field(
        default=True, description="Whether this permission is currently active."
    )
    expires_at: Optional[datetime] = Field(
        default=None, description="Optional expiry time for this permission."
    )
    created_at: datetime = Field(description="The time this permission was created.")
    modified_at: datetime = Field(
        description="The time this permission was last modified."
    )
    description: Optional[str] = Field(
        default=None, description="Optional description of this permission."
    )
    scope: Optional[str] = Field(
        default=None, description="Optional scope limitation for this permission."
    )
    priority: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Priority level (1-10, higher number = higher priority).",
    )
    is_temporary: bool = Field(
        default=False, description="Whether this is a temporary permission."
    )
    reason: Optional[str] = Field(
        default=None, description="Reason for granting this permission."
    )

    @model_validator(mode="after")
    def validate_expiry_date(self) -> "UserPermission":
        """Validate that expiry date is in the future if provided."""
        if self.expires_at and self.expires_at <= datetime.utcnow():
            raise ValueError("Permission expiry date must be in the future")
        return self

    @field_validator("conditions")
    @classmethod
    def validate_conditions_format(
        cls, v: Optional[Mapping[str, Any]]
    ) -> Optional[Mapping[str, Any]]:
        """Validate that conditions are properly formatted."""
        if v is not None:
            # Basic validation - ensure conditions is a dictionary
            if not isinstance(v, dict):
                raise ValueError("Conditions must be a dictionary")
        return v

    @model_validator(mode="after")
    def validate_temporary_permission_logic(self) -> "UserPermission":
        """Validate temporary permission logic."""
        if self.is_temporary and not self.expires_at:
            raise ValueError("Temporary permissions must have an expiry date")
        if not self.is_temporary and self.expires_at:
            # Allow expiry dates for non-temporary permissions for flexibility
            pass
        return self

    def is_expired(self) -> bool:
        """Check if the permission has expired."""
        if not self.expires_at:
            return False
        return self.expires_at <= datetime.utcnow()

    def is_effective(self) -> bool:
        """Check if the permission is currently effective (active and not expired)."""
        return self.is_active and not self.is_expired()

    def get_permission_key(self) -> str:
        """Get a unique key representing this user permission."""
        # Use model_dump to get the actual enum values
        model_data = self.model_dump()
        entity_type_val = model_data.get("entity_type", "")
        permission_type_val = model_data.get("permission_type", "")

        # Extract the string value from enum objects if they are enums
        if hasattr(entity_type_val, "value"):
            entity_type_val = entity_type_val.value
        if hasattr(permission_type_val, "value"):
            permission_type_val = permission_type_val.value

        return (
            f"{self.user_id}:{entity_type_val}:{self.entity_id}:{permission_type_val}"
        )

    def conflicts_with(self, other: "UserPermission") -> bool:
        """Check if this permission conflicts with another user permission."""
        return (
            self.user_id == other.user_id
            and self.entity_type == other.entity_type
            and self.entity_id == other.entity_id
            and self.permission_type == other.permission_type
            and self.id != other.id
        )

    def can_be_combined_with(self, other: "UserPermission") -> bool:
        """Check if this permission can be combined with another."""
        return (
            self.user_id == other.user_id
            and self.entity_type == other.entity_type
            and self.entity_id == other.entity_id
            and self.permission_type != other.permission_type
        )

    def extend_expiry(self, new_expiry: datetime) -> None:
        """Extend the permission expiry date."""
        if new_expiry <= datetime.utcnow():
            raise ValueError("New expiry date must be in the future")
        self.expires_at = new_expiry

    def revoke(self) -> None:
        """Revoke this permission."""
        self.is_active = False


class PermissionInheritance(CreatorBaseModel):
    """Represents a permission inheritance relationship for access control."""

    id: str = Field(
        description="The unique identifier of the inheritance relationship."
    )
    source_permission_id: str = Field(
        description="The ID of the source permission being inherited from."
    )
    target_permission_id: str = Field(
        description="The ID of the target permission that inherits the source."
    )
    inheritance_type: str = Field(
        description="Inheritance type (role_hierarchy, entity_hierarchy, direct)."
    )
    inheritance_path: Sequence[str] = Field(
        description="The chain of IDs showing the complete inheritance path."
    )
    is_active: bool = Field(
        default=True,
        description="Whether this inheritance relationship is currently active.",
    )
    created_at: datetime = Field(description="The time this inheritance was created.")
    modified_at: datetime = Field(
        description="The time this inheritance was last modified."
    )
    created_by_user_id: str = Field(
        description="The user ID who created this inheritance."
    )
    depth: int = Field(
        ge=1, description="The depth level in the inheritance hierarchy."
    )
    conditions: Optional[Mapping[str, Any]] = Field(
        default=None,
        description="Conditions that affect this inheritance relationship.",
    )

    @field_validator("inheritance_path")
    @classmethod
    def validate_inheritance_path(cls, v: Sequence[str]) -> Sequence[str]:
        """Validate that inheritance path is not empty and contains valid IDs."""
        if not v:
            raise ValueError("Inheritance path cannot be empty")
        if len(v) < 2:
            raise ValueError("Inheritance path must contain at least source and target")
        return v

    @model_validator(mode="after")
    def validate_inheritance_logic(self) -> "PermissionInheritance":
        """Validate inheritance relationship logic."""
        if self.source_permission_id == self.target_permission_id:
            raise ValueError("Source and target permissions cannot be the same")

        # Ensure the path starts with source and ends with target
        if (
            self.inheritance_path
            and len(self.inheritance_path) >= 2
            and self.inheritance_path[0] != self.source_permission_id
        ):
            raise ValueError("Inheritance path must start with source permission ID")

        if (
            self.inheritance_path
            and len(self.inheritance_path) >= 2
            and self.inheritance_path[-1] != self.target_permission_id
        ):
            raise ValueError("Inheritance path must end with target permission ID")

        return self

    @field_validator("conditions")
    @classmethod
    def validate_conditions_format(
        cls, v: Optional[Mapping[str, Any]]
    ) -> Optional[Mapping[str, Any]]:
        """Validate that conditions are properly formatted."""
        if v is not None:
            # Basic validation - ensure conditions is a dictionary
            if not isinstance(v, dict):
                raise ValueError("Conditions must be a dictionary")
        return v

    def get_inheritance_chain(self) -> List[str]:
        """Get the complete inheritance chain from source to target."""
        return list(self.inheritance_path)

    def get_direct_parent(self) -> str:
        """Get the direct parent in the inheritance chain."""
        path_list = list(self.inheritance_path)
        if len(path_list) >= 2:
            return path_list[-2]
        return self.source_permission_id

    def get_inheritance_distance(self) -> int:
        """Get the distance (number of hops) in the inheritance chain."""
        return len(self.inheritance_path) - 1

    def is_direct_inheritance(self) -> bool:
        """Check if this is a direct inheritance (only one hop)."""
        return self.get_inheritance_distance() == 1

    def is_multi_level_inheritance(self) -> bool:
        """Check if this is a multi-level inheritance (multiple hops)."""
        return self.get_inheritance_distance() > 1

    def affects_permission(self, permission_id: str) -> bool:
        """Check if this inheritance relationship affects a specific permission."""
        path_list = list(self.inheritance_path)
        return permission_id in path_list

    def get_affected_permissions(self) -> List[str]:
        """Get all permissions affected by this inheritance relationship."""
        return list(self.inheritance_path)

    def break_inheritance(self) -> None:
        """Break this inheritance relationship."""
        self.is_active = False

    def reactivate_inheritance(self) -> None:
        """Reactivate this inheritance relationship."""
        self.is_active = True
