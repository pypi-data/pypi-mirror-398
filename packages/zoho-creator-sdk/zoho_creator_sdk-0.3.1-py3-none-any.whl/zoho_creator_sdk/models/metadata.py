"""Metadata models for Zoho Creator SDK."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class AuditMetadata(BaseModel):
    """
    Model representing audit trail metadata for all models.
    """

    created_by: Optional[str] = Field(
        default=None,
        description="The user who created the record.",
        alias="createdBy",
    )
    modified_by: Optional[str] = Field(
        default=None,
        description="The user who last modified the record.",
        alias="modifiedBy",
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="The timestamp when the record was created.",
        alias="createdAt",
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="The timestamp when the record was last updated.",
        alias="updatedAt",
    )

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _parse_datetime_audit(cls, value: Any) -> Optional[datetime]:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        elif isinstance(value, datetime):
            return value
        else:
            return None


class SystemMetadata(BaseModel):
    """
    Model representing system-level metadata for all models.
    """

    version: Optional[str] = Field(
        default=None, description="The version of the record."
    )
    is_active: bool = Field(
        default=True, description="Whether the record is active.", alias="isActive"
    )
    is_deleted: bool = Field(
        default=False, description="Whether the record is deleted.", alias="isDeleted"
    )
    archived_at: Optional[datetime] = Field(
        default=None,
        description="The timestamp when the record was archived.",
        alias="archivedAt",
    )

    @field_validator("archived_at", mode="before")
    @classmethod
    def _parse_datetime_system(cls, value: Any) -> Optional[datetime]:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        elif isinstance(value, datetime):
            return value
        else:
            return None


class ExtendedMetadata(BaseModel):
    """
    Model representing extended metadata for all models.
    """

    tags: List[str] = Field(default_factory=list, description="A list of tags.")
    categories: List[str] = Field(
        default_factory=list, description="A list of categories."
    )
    custom_properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="A dictionary of custom properties.",
        alias="customProperties",
    )


class Metadata(AuditMetadata, SystemMetadata, ExtendedMetadata):
    """
    A comprehensive model that includes all metadata fields.
    """

    def update_tags(self, *tags: str) -> None:
        """
        Adds new tags to the existing list of tags.

        Args:
            *tags: A variable number of tags to add.
        """
        if isinstance(self.tags, list):
            self.tags.extend(tags)  # pylint: disable=no-member

    def remove_tags(self, *tags: str) -> None:
        """
        Removes specified tags from the list of tags.

        Args:
            *tags: A variable number of tags to remove.
        """
        if isinstance(self.tags, list):
            for tag in tags:
                if tag in self.tags:
                    self.tags.remove(tag)  # pylint: disable=no-member

    def set_property(self, key: str, value: Any) -> None:
        """
        Sets a custom property.

        Args:
            key: The key of the custom property.
            value: The value of the custom property.
        """
        if isinstance(self.custom_properties, dict):
            self.custom_properties[key] = value

    def get_property(self, key: str) -> Any:
        """
        Retrieves a custom property.

        Args:
            key: The key of the custom property.

        Returns:
            The value of the custom property, or None if not found.
        """
        if isinstance(self.custom_properties, dict):
            return self.custom_properties.get(key)  # pylint: disable=no-member
        return None
