"""
Pydantic models for sections and components in the Zoho Creator SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from pydantic import Field

from .base import CreatorBaseModel


class Component(CreatorBaseModel):
    """Represents a component within a Zoho Creator section."""

    id: str = Field(description="The unique identifier of the component.")
    name: str = Field(description="The name of the component.")
    link_name: str = Field(description="The link name of the component (URL-friendly).")
    component_type: int = Field(description="The type of the component.")
    section_id: str = Field(
        description="The ID of the section this component belongs to."
    )
    page_type: Optional[int] = Field(
        default=None, description="The type of page this component is associated with."
    )
    view_type: Optional[int] = Field(
        default=None, description="The view type of the component."
    )
    display_order: Optional[int] = Field(
        default=None,
        ge=0,
        description="Order in which the component should be displayed.",
    )
    is_visible: bool = Field(
        default=True, description="Whether the component is visible."
    )
    created_time: Optional[datetime] = Field(
        default=None, description="The time the component was created."
    )
    modified_time: Optional[datetime] = Field(
        default=None, description="The time the component was last modified."
    )


class Section(CreatorBaseModel):
    """Represents a section within a Zoho Creator application."""

    id: str = Field(description="The unique identifier of the section.")
    name: str = Field(description="The name of the section.")
    link_name: str = Field(description="The link name of the section (URL-friendly).")
    application_id: str = Field(
        description="The ID of the application the section belongs to."
    )
    page_id: str = Field(description="The ID of the page this section belongs to.")
    description: Optional[str] = Field(
        default=None, description="A description of the section."
    )
    display_order: Optional[int] = Field(
        default=None,
        ge=0,
        description="Order in which the section should be displayed.",
    )
    is_active: bool = Field(default=True, description="Whether the section is active.")
    components: Sequence[Component] = Field(
        default=[], description="List of components within this section."
    )
    created_time: Optional[datetime] = Field(
        default=None, description="The time the section was created."
    )
    modified_time: Optional[datetime] = Field(
        default=None, description="The time the section was last modified."
    )
