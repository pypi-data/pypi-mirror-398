"""
Pydantic models for reports in the Zoho Creator SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Optional

from pydantic import Field

from .base import CreatorBaseModel
from .enums import ReportType


class Report(CreatorBaseModel):
    """Represents a report within a Zoho Creator application."""

    id: str = Field(description="The unique identifier of the report.")
    name: str = Field(description="The name of the report.")
    link_name: str = Field(description="The link name of the report.")
    application_id: str = Field(
        description="The ID of the application the report belongs to."
    )
    form_id: str = Field(description="The ID of the form the report is based on.")
    report_type: ReportType = Field(description="The type of the report.")
    created_time: datetime = Field(description="The time the report was created.")
    modified_time: datetime = Field(
        description="The time the report was last modified."
    )
    owner: str = Field(description="The owner of the report.")
    active: bool = Field(description="Whether the report is active.")
    description: Optional[str] = Field(
        default=None, description="A description of the report."
    )
    is_public: bool = Field(
        default=False, description="Whether the report is publicly accessible."
    )
    criteria: Optional[str] = Field(
        default=None, description="The criteria for the report."
    )
    sort_order: Optional[str] = Field(
        default=None, description="The sort order of the report."
    )


class ReportColumn(CreatorBaseModel):
    """Represents a column definition within a Zoho Creator report."""

    id: str = Field(description="The unique identifier of the report column.")
    name: str = Field(description="The name of the column.")
    link_name: str = Field(description="The link name of the column.")
    field_id: str = Field(description="The ID of the field this column represents.")
    report_id: str = Field(description="The ID of the report this column belongs to.")
    display_order: int = Field(
        description="The display order of the column in the report."
    )
    width: Optional[int] = Field(
        default=None, description="The width of the column in pixels."
    )
    sortable: bool = Field(default=True, description="Whether the column is sortable.")
    filterable: bool = Field(
        default=True, description="Whether the column is filterable."
    )
    hidden: bool = Field(default=False, description="Whether the column is hidden.")


class ReportFilter(CreatorBaseModel):
    """Represents a saved filter within a Zoho Creator report."""

    id: str = Field(description="The unique identifier of the report filter.")
    name: str = Field(description="The name of the filter.")
    report_id: str = Field(description="The ID of the report this filter belongs to.")
    criteria: Mapping[str, Any] = Field(
        description="The filter criteria as a dictionary of field conditions."
    )
    created_time: datetime = Field(description="The time the filter was created.")
    modified_time: datetime = Field(
        description="The time the filter was last modified."
    )
    is_default: bool = Field(
        default=False, description="Whether this is the default filter for the report."
    )
    is_public: bool = Field(
        default=False, description="Whether the filter is publicly accessible."
    )
