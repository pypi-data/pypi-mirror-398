"""
Authentication handlers for the Zoho Creator SDK.
"""

import logging
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

import httpx

from .constants import Datacenter
from .exceptions import AuthenticationError, TokenRefreshError
from .models import AuthConfig

logger = logging.getLogger(__name__)


class BaseAuthHandler:
    """Base class for authentication handlers."""

    def __init__(self) -> None:
        # Prevent direct instantiation of the base class while allowing
        # subclasses to reuse this initializer.
        if self.__class__ is BaseAuthHandler:
            raise TypeError(
                "Can't instantiate abstract class BaseAuthHandler with abstract "
                "methods get_auth_headers, refresh_auth"
            )

    def get_auth_headers(self) -> "Mapping[str, str]":
        """Get the authentication headers for an API request."""
        raise NotImplementedError("get_auth_headers must be implemented by subclasses")

    def refresh_auth(self) -> None:
        """Refresh the authentication credentials."""
        raise NotImplementedError("refresh_auth must be implemented by subclasses")


class OAuth2AuthHandler(BaseAuthHandler):
    """Authentication handler for OAuth2 authentication."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        refresh_token: str,
        *,
        access_token: Optional[str] = None,
        token_expiry: Optional[datetime] = None,
        datacenter: Optional[Datacenter] = None,
        scopes: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        if not all([client_id, client_secret, redirect_uri, refresh_token]):
            raise AuthenticationError(
                "Client ID, client secret, redirect URI, and refresh token "
                "are required."
            )
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.token_expiry = token_expiry
        self.datacenter = datacenter or Datacenter.US
        self.scopes = scopes or []

    def get_auth_headers(self) -> Mapping[str, str]:
        """Get the authentication headers for an API request."""
        if not self.access_token or self.is_token_expired():
            logger.info("Access token is expired or missing, refreshing.")
            self.refresh_auth()
        if self.access_token is None:
            raise AuthenticationError("Access token is not available after refresh")
        return {"Authorization": f"Zoho-oauthtoken {self.access_token}"}

    def is_token_expired(self) -> bool:
        """Check if the access token has expired."""
        if not self.token_expiry:
            return True
        return datetime.now(timezone.utc) >= self.token_expiry - timedelta(seconds=60)

    def refresh_auth(self) -> None:
        """Refresh the access token using the refresh token."""
        logger.info("Attempting to refresh OAuth2 access token.")
        url = f"{self.datacenter.accounts_url}/oauth/v2/token"
        data = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }

        # Include scopes in the request if provided
        if self.scopes:
            data["scope"] = " ".join(self.scopes)
        try:
            with httpx.Client() as client:
                response = client.post(url, data=data, timeout=10)
                response.raise_for_status()
                token_data = response.json()

                if "access_token" not in token_data:
                    raise TokenRefreshError(
                        f"Failed to refresh access token: "
                        f"{token_data.get('error', 'Unknown error')}"
                    )

                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expiry = datetime.now(timezone.utc) + timedelta(
                    seconds=expires_in
                )
                logger.info("Successfully refreshed OAuth2 access token.")

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code if e.response else "Unknown"
            response_text = e.response.text if e.response else "No response body"
            logger.error(
                "Failed to refresh access token - Status: %s, Response: %s",
                status_code,
                response_text,
            )
            raise TokenRefreshError(
                "Failed to refresh OAuth2 token. "
                f"Status: {status_code}, Response: {response_text}"
            ) from e
        except httpx.RequestError as e:
            logger.error("Failed to refresh access token: %s", e)
            raise TokenRefreshError(f"Failed to refresh access token: {e}") from e


def get_auth_handler(
    config: AuthConfig, api_config: Optional[Any] = None
) -> BaseAuthHandler:
    """
    Get an authentication handler based on the provided configuration.
    """
    if (
        config.client_id
        and config.client_secret
        and config.redirect_uri
        and config.refresh_token
    ):
        datacenter = None
        if api_config:
            datacenter = api_config.datacenter

        return OAuth2AuthHandler(
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=config.redirect_uri,
            refresh_token=config.refresh_token,
            access_token=config.access_token,
            token_expiry=config.token_expiry,
            datacenter=datacenter,
        )

    raise AuthenticationError("No valid authentication method found in configuration.")
