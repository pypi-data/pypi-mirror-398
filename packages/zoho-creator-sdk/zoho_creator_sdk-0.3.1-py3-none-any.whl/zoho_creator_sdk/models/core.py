"""
Pydantic models for core entities in the Zoho Creator SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import EmailStr, Field

from .base import CreatorBaseModel


class Application(CreatorBaseModel):
    """Represents a Zoho Creator application."""

    application_name: str = Field(..., alias="application_name")
    date_format: str = Field(..., alias="date_format")
    creation_date: str = Field(..., alias="creation_date")
    link_name: str = Field(..., alias="link_name")
    category: int
    time_zone: str = Field(..., alias="time_zone")
    created_by: str = Field(..., alias="created_by")
    workspace_name: str = Field(..., alias="workspace_name")


class Record(CreatorBaseModel):
    """Represents a record within a Zoho Creator form."""

    # Optional metadata fields that may be present in some API responses
    id: Optional[str] = Field(
        default=None, description="The unique identifier of the record."
    )
    form_id: Optional[str] = Field(
        default=None, description="The ID of the form the record belongs to."
    )
    created_time: Optional[datetime] = Field(
        default=None, description="The time the record was created."
    )
    modified_time: Optional[datetime] = Field(
        default=None, description="The time the record was last modified."
    )
    owner: Optional[str] = Field(default=None, description="The owner of the record.")

    # The actual form field data - this is what the API primarily returns
    # Using extra="allow" to allow any additional fields from the form
    model_config = {"extra": "allow"}

    def get_form_data(self) -> Dict[str, Any]:
        """Get the form field data as a dictionary, excluding metadata fields."""
        return {
            key: value
            for key, value in self.dict(exclude_none=True).items()
            if key not in ["id", "form_id", "created_time", "modified_time", "owner"]
        }


class User(CreatorBaseModel):
    """Represents a Zoho Creator user."""

    id: str = Field(description="The unique identifier of the user.")
    email: EmailStr = Field(description="The email address of the user.")
    first_name: str = Field(description="The first name of the user.")
    last_name: str = Field(description="The last name of the user.")
    role: str = Field(description="The role of the user.")
    active: bool = Field(description="Whether the user is active.")
    status: Optional[str] = Field(default=None, description="The status of the user.")
    added_time: Optional[datetime] = Field(
        default=None, description="The time the user was added."
    )
    profile: Optional[str] = Field(default=None, description="The profile of the user.")
