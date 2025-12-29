"""
Pydantic model for custom actions in the Zoho Creator SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Optional

from pydantic import Field

from .base import CreatorBaseModel


class CustomAction(CreatorBaseModel):
    """Represents a custom action in Zoho Creator."""

    model_config = {
        **CreatorBaseModel.model_config,
        "populate_by_name": True,
        "extra": "forbid",
    }

    id: Optional[str] = Field(
        default=None,
        alias="action_id",
        description="The unique identifier of the custom action.",
    )
    name: Optional[str] = Field(
        default=None,
        alias="action_name",
        description="The name of the custom action.",
    )
    link_name: Optional[str] = Field(
        default=None, description="The link name of the custom action (URL-friendly)."
    )
    application_id: Optional[str] = Field(
        default=None,
        description="The ID of the application the custom action belongs to.",
    )
    form_id: Optional[str] = Field(
        default=None,
        description="The ID of the form this custom action is associated with.",
    )
    action_type: Optional[str] = Field(
        default=None,
        description="The type of custom action (e.g., script, workflow, API call).",
    )
    configuration: Mapping[str, Any] = Field(
        default_factory=dict,
        description="Custom action-specific configuration parameters.",
    )
    is_active: bool = Field(
        default=True, description="Whether the custom action is active."
    )
    created_time: Optional[datetime] = Field(
        default=None, description="The time the custom action was created."
    )
    modified_time: Optional[datetime] = Field(
        default=None, description="The time the custom action was last modified."
    )
    description: Optional[str] = Field(
        default=None, description="A description of the custom action."
    )
    owner: Optional[str] = Field(
        default=None, description="The owner of the custom action."
    )

    @property
    def action_id(self) -> Optional[str]:
        return self.id

    @property
    def action_name(self) -> Optional[str]:
        return self.name
