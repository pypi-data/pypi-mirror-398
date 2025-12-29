"""
Pydantic model for connections in the Zoho Creator SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Optional

from pydantic import Field

from .base import CreatorBaseModel


class Connection(CreatorBaseModel):
    """Represents a connection to an external service in Zoho Creator."""

    # Allow both field names (id, name, ...) and API aliases
    model_config = {
        **CreatorBaseModel.model_config,
        "populate_by_name": True,
        "extra": "forbid",
    }

    # The Zoho Creator settings API typically exposes connection_id and
    # connection_name fields. Use aliases so we can construct the model from
    # either API responses or explicit field names in tests.
    id: Optional[str] = Field(
        default=None,
        alias="connection_id",
        description="The unique identifier of the connection.",
    )
    name: Optional[str] = Field(
        default=None,
        alias="connection_name",
        description="The name of the connection.",
    )
    connection_type: Optional[str] = Field(
        default=None,
        description="The type of the connection (e.g., REST, OAuth).",
    )
    application_id: Optional[str] = Field(
        default=None,
        description="The ID of the application the connection belongs to.",
    )
    configuration: Mapping[str, Any] = Field(
        default_factory=dict,
        description="Connection-specific configuration parameters.",
    )
    is_active: bool = Field(
        default=True, description="Whether the connection is active."
    )
    is_encrypted: bool = Field(
        default=True, description="Whether the connection data is encrypted."
    )
    created_time: Optional[datetime] = Field(
        default=None, description="The time the connection was created."
    )
    modified_time: Optional[datetime] = Field(
        default=None, description="The time the connection was last modified."
    )
    description: Optional[str] = Field(
        default=None, description="A description of the connection."
    )
    owner: Optional[str] = Field(
        default=None, description="The owner of the connection."
    )

    # Backwards-compatible accessors for tests and callers that expect the
    # original API field names as attributes.

    @property
    def connection_id(self) -> Optional[str]:
        """Return the connection identifier (alias for ``id``)."""

        return self.id

    @property
    def connection_name(self) -> Optional[str]:
        """Return the connection name (alias for ``name``)."""

        return self.name
