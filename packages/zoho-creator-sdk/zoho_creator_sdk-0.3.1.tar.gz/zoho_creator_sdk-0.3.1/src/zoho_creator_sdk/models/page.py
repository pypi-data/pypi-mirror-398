"""
Pydantic model for pages in the Zoho Creator SDK.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from pydantic import Field

from .base import CreatorBaseModel


class Page(CreatorBaseModel):
    """Represents a page within a Zoho Creator application."""

    # Allow construction from either internal field names or API-style names
    # (page_id, page_name, is_published) while rejecting unknown fields that are
    # not part of the documented/expected page structure.
    model_config = {
        **CreatorBaseModel.model_config,
        "populate_by_name": True,
        "extra": "forbid",
    }

    id: Optional[str] = Field(
        default=None,
        alias="page_id",
        description="The unique identifier of the page.",
    )
    name: Optional[str] = Field(
        default=None,
        alias="page_name",
        description="The name of the page.",
    )
    link_name: Optional[str] = Field(
        default=None,
        description="The link name of the page (URL-friendly).",
    )
    application_id: Optional[str] = Field(
        default=None,
        description="The ID of the application the page belongs to.",
    )
    description: Optional[str] = Field(
        default=None,
        description="A description of the page.",
    )
    is_active: bool = Field(
        default=True,
        alias="is_published",
        description="Whether the page is active.",
    )
    created_time: Optional[str] = Field(
        default=None,
        description="The time the page was created.",
    )
    modified_time: Optional[str] = Field(
        default=None,
        description="The time the page was last modified.",
    )

    # Additional optional fields used by the tests to represent complex pages.
    layout: Optional[str] = Field(
        default=None,
        description="Layout configuration for the page (e.g., grid, single-column).",
    )
    components: Optional[Sequence[Dict[str, Any]]] = Field(
        default=None,
        description="List of component definitions that make up the page.",
    )
    seo_settings: Optional[Dict[str, Any]] = Field(
        default=None,
        description="SEO-related configuration for the page.",
    )
    access_permissions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Access control configuration for the page.",
    )

    @property
    def page_id(self) -> Optional[str]:
        """Alias for the page identifier matching API field name."""

        return self.id

    @property
    def page_name(self) -> Optional[str]:
        """Alias for the page name matching API field name."""

        return self.name
