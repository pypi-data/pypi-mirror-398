"""
Pydantic models for configuration in the Zoho Creator SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Sequence, cast

from pydantic import Field, field_validator, model_validator

from ..constants import Datacenter
from .base import CreatorBaseModel


class APIConfig(CreatorBaseModel):
    """Configuration for the API client."""

    datacenter: Datacenter = Field(
        default=Datacenter.US,
        description="The Zoho datacenter to use for API calls.",
    )
    timeout: int = Field(
        default=30, description="The timeout for API requests, in seconds."
    )
    max_retries: int = Field(
        default=3,
        description="The maximum number of times to retry a failed API request.",
    )
    retry_delay: float = Field(
        default=1.0, description="The delay between retries, in seconds."
    )
    max_records_per_request: int = Field(
        default=200,
        ge=1,
        le=1000,
        description="Maximum records per request (200, 500, or 1000)",
    )
    max_refresh_tokens_per_minute: int = Field(
        default=5, description="Rate limit for token refresh"
    )
    max_refresh_tokens_per_user: int = Field(
        default=20, description="Maximum refresh tokens per user"
    )
    environment: Optional[str] = Field(
        default=None,
        description=(
            "Optional environment header value, such as 'development' or 'stage'."
        ),
    )
    demo_user_name: Optional[str] = Field(
        default=None,
        description=("Optional demo user name header used together with environment."),
    )

    @field_validator("max_records_per_request")
    @classmethod
    def validate_max_records_per_request(cls, v: int) -> int:
        """Validate that max_records_per_request is one of [200, 500, 1000]."""
        if v not in [200, 500, 1000]:
            raise ValueError("max_records_per_request must be 200, 500, or 1000")
        return v

    @field_validator("max_refresh_tokens_per_minute")
    @classmethod
    def validate_max_refresh_tokens_per_minute(cls, v: int) -> int:
        """Validate that max_refresh_tokens_per_minute is at least 1."""
        if v < 1:
            raise ValueError("max_refresh_tokens_per_minute must be at least 1")
        return v

    @field_validator("max_refresh_tokens_per_user")
    @classmethod
    def validate_max_refresh_tokens_per_user(cls, v: int) -> int:
        """Validate that max_refresh_tokens_per_user is at least 1."""
        if v < 1:
            raise ValueError("max_refresh_tokens_per_user must be at least 1")
        return v

    @property
    def base_url(self) -> str:
        """Get the base URL for the Zoho Creator API."""
        # Use model_dump to get the actual field values
        model_data = self.model_dump()
        datacenter_value = cast(Datacenter, model_data.get("datacenter", Datacenter.US))
        return datacenter_value.api_url + "/creator/v2.1"

    @property
    def accounts_url(self) -> str:
        """Get the accounts URL for the selected datacenter."""
        # Use model_dump to get the actual field values
        model_data = self.model_dump()
        datacenter_value = cast(Datacenter, model_data.get("datacenter", Datacenter.US))
        return datacenter_value.accounts_url


class AuthConfig(CreatorBaseModel):
    """Configuration for authentication."""

    client_id: Optional[str] = Field(
        default=None, description="The client ID for OAuth2 authentication."
    )
    client_secret: Optional[str] = Field(
        default=None, description="The client secret for OAuth2 authentication."
    )
    redirect_uri: Optional[str] = Field(
        default=None, description="The redirect URI for OAuth2 authentication."
    )
    refresh_token: Optional[str] = Field(
        default=None, description="The refresh token for OAuth2 authentication."
    )
    access_token: Optional[str] = Field(
        default=None, description="The access token for OAuth2 authentication."
    )
    token_expiry: Optional[datetime] = Field(
        default=None, description="The expiry time of the access token."
    )
    scopes: Sequence[str] = Field(
        default=["ZohoCreator.dashboard.READ"],
        description="OAuth2 scopes for API access",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_oauth2_credentials(cls, values: Any) -> Any:
        """
        Validate that OAuth2 credential fields are provided together or not at all.
        """
        if isinstance(values, dict):
            oauth2_fields = [
                "client_id",
                "client_secret",
                "redirect_uri",
                "refresh_token",
            ]
            provided_fields = [
                field for field in oauth2_fields if values.get(field) is not None
            ]
            missing_fields = [
                field for field in oauth2_fields if values.get(field) is None
            ]

            # If any OAuth2 fields are provided, all must be provided
            if provided_fields and missing_fields:
                missing_str = ", ".join(missing_fields)
                fields_str = ", ".join(oauth2_fields)
                raise ValueError(
                    f"OAuth2 configuration is incomplete. "
                    f"Missing required fields: {missing_str}. "
                    f"When using OAuth2 authentication, all of: "
                    f"{fields_str} must be provided together."
                )

        return values
