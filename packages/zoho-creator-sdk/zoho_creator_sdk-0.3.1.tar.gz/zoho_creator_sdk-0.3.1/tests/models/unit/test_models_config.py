"""Unit tests for configuration models."""

from __future__ import annotations

import pytest

from zoho_creator_sdk.constants import Datacenter
from zoho_creator_sdk.models.config import APIConfig, AuthConfig


def test_api_config_default_values() -> None:
    """Test that APIConfig has correct default values."""
    config = APIConfig()

    assert config.datacenter == Datacenter.US
    assert config.timeout == 30
    assert config.max_retries == 3
    assert config.retry_delay == 1.0
    assert config.max_records_per_request == 200
    assert config.max_refresh_tokens_per_minute == 5
    assert config.max_refresh_tokens_per_user == 20
    assert config.environment is None
    assert config.demo_user_name is None


def test_api_config_custom_values() -> None:
    """Test that APIConfig accepts custom values."""
    config = APIConfig(
        datacenter=Datacenter.EU,
        timeout=60,
        max_retries=5,
        retry_delay=2.0,
        max_records_per_request=500,
        max_refresh_tokens_per_minute=10,
        max_refresh_tokens_per_user=30,
        environment="development",
        demo_user_name="test_user",
    )

    assert config.datacenter == Datacenter.EU
    assert config.timeout == 60
    assert config.max_retries == 5
    assert config.retry_delay == 2.0
    assert config.max_records_per_request == 500
    assert config.max_refresh_tokens_per_minute == 10
    assert config.max_refresh_tokens_per_user == 30
    assert config.environment == "development"
    assert config.demo_user_name == "test_user"


def test_api_config_validate_max_records_per_request() -> None:
    """Test validation of max_records_per_request field."""
    # Valid values should work
    for valid_value in [200, 500, 1000]:
        config = APIConfig(max_records_per_request=valid_value)
        assert config.max_records_per_request == valid_value

    # Invalid values should raise ValueError
    with pytest.raises(
        ValueError, match="max_records_per_request must be 200, 500, or 1000"
    ):
        APIConfig(max_records_per_request=100)

    with pytest.raises(ValueError, match="Input should be less than or equal to 1000"):
        APIConfig(max_records_per_request=1500)


def test_api_config_validate_max_refresh_tokens_per_minute() -> None:
    """Test validation of max_refresh_tokens_per_minute field."""
    # Valid values should work
    config = APIConfig(max_refresh_tokens_per_minute=10)
    assert config.max_refresh_tokens_per_minute == 10

    # Invalid values should raise ValueError
    with pytest.raises(
        ValueError, match="max_refresh_tokens_per_minute must be at least 1"
    ):
        APIConfig(max_refresh_tokens_per_minute=0)

    with pytest.raises(
        ValueError, match="max_refresh_tokens_per_minute must be at least 1"
    ):
        APIConfig(max_refresh_tokens_per_minute=-5)


def test_api_config_validate_max_refresh_tokens_per_user() -> None:
    """Test validation of max_refresh_tokens_per_user field."""
    # Valid values should work
    config = APIConfig(max_refresh_tokens_per_user=25)
    assert config.max_refresh_tokens_per_user == 25

    # Invalid values should raise ValueError
    with pytest.raises(
        ValueError, match="max_refresh_tokens_per_user must be at least 1"
    ):
        APIConfig(max_refresh_tokens_per_user=0)

    with pytest.raises(
        ValueError, match="max_refresh_tokens_per_user must be at least 1"
    ):
        APIConfig(max_refresh_tokens_per_user=-10)


def test_api_config_base_url() -> None:
    """Test base_url property for different datacenters."""
    us_config = APIConfig(datacenter=Datacenter.US)
    assert us_config.base_url == "https://www.zohoapis.com/creator/v2.1"

    eu_config = APIConfig(datacenter=Datacenter.EU)
    assert eu_config.base_url == "https://www.zohoapis.eu/creator/v2.1"

    in_config = APIConfig(datacenter=Datacenter.IN)
    assert in_config.base_url == "https://www.zohoapis.in/creator/v2.1"

    au_config = APIConfig(datacenter=Datacenter.AU)
    assert au_config.base_url == "https://www.zohoapis.com.au/creator/v2.1"

    ca_config = APIConfig(datacenter=Datacenter.CA)
    assert ca_config.base_url == "https://www.zohoapis.ca/creator/v2.1"


def test_api_config_accounts_url() -> None:
    """Test accounts_url property for different datacenters."""
    us_config = APIConfig(datacenter=Datacenter.US)
    assert us_config.accounts_url == "https://accounts.zoho.com"

    eu_config = APIConfig(datacenter=Datacenter.EU)
    assert eu_config.accounts_url == "https://accounts.zoho.eu"

    in_config = APIConfig(datacenter=Datacenter.IN)
    assert in_config.accounts_url == "https://accounts.zoho.in"

    au_config = APIConfig(datacenter=Datacenter.AU)
    assert au_config.accounts_url == "https://accounts.zoho.au"

    ca_config = APIConfig(datacenter=Datacenter.CA)
    assert ca_config.accounts_url == "https://accounts.zoho.ca"


def test_auth_config_default_values() -> None:
    """Test that AuthConfig has correct default values."""
    config = AuthConfig()

    assert config.client_id is None
    assert config.client_secret is None
    assert config.redirect_uri is None
    assert config.refresh_token is None
    assert config.access_token is None
    assert config.token_expiry is None
    assert config.scopes == ["ZohoCreator.dashboard.READ"]


def test_auth_config_custom_values() -> None:
    """Test that AuthConfig accepts custom values."""
    config = AuthConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="https://example.com/callback",
        refresh_token="test_refresh_token",
        access_token="test_access_token",
        scopes=["ZohoCreator.dashboard.READ", "ZohoCreator.dashboard.WRITE"],
    )

    assert config.client_id == "test_client_id"
    assert config.client_secret == "test_client_secret"
    assert config.redirect_uri == "https://example.com/callback"
    assert config.refresh_token == "test_refresh_token"
    assert config.access_token == "test_access_token"
    assert config.scopes == [
        "ZohoCreator.dashboard.READ",
        "ZohoCreator.dashboard.WRITE",
    ]


def test_auth_config_validate_oauth2_credentials_complete() -> None:
    """Test that complete OAuth2 credentials are accepted."""
    config = AuthConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="https://example.com/callback",
        refresh_token="test_refresh_token",
    )

    assert config.client_id == "test_client_id"
    assert config.client_secret == "test_client_secret"
    assert config.redirect_uri == "https://example.com/callback"
    assert config.refresh_token == "test_refresh_token"


def test_auth_config_validate_oauth2_credentials_incomplete() -> None:
    """Test that incomplete OAuth2 credentials raise ValueError."""
    # Missing client_id
    with pytest.raises(ValueError, match="OAuth2 configuration is incomplete"):
        AuthConfig(
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            refresh_token="test_refresh_token",
        )

    # Missing client_secret
    with pytest.raises(ValueError, match="OAuth2 configuration is incomplete"):
        AuthConfig(
            client_id="test_client_id",
            redirect_uri="https://example.com/callback",
            refresh_token="test_refresh_token",
        )

    # Missing redirect_uri
    with pytest.raises(ValueError, match="OAuth2 configuration is incomplete"):
        AuthConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
        )

    # Missing refresh_token
    with pytest.raises(ValueError, match="OAuth2 configuration is incomplete"):
        AuthConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
        )

    # Multiple missing fields
    with pytest.raises(ValueError, match="OAuth2 configuration is incomplete"):
        AuthConfig(client_id="test_client_id", client_secret="test_client_secret")


def test_auth_config_validate_oauth2_credentials_none() -> None:
    """Test that no OAuth2 credentials are accepted."""
    config = AuthConfig()

    assert config.client_id is None
    assert config.client_secret is None
    assert config.redirect_uri is None
    assert config.refresh_token is None


def test_auth_config_validate_oauth2_credentials_partial() -> None:
    """Test that partial OAuth2 credentials raise ValueError."""
    # Only one field provided
    with pytest.raises(ValueError, match="OAuth2 configuration is incomplete"):
        AuthConfig(client_id="test_client_id")

    # Two fields provided
    with pytest.raises(ValueError, match="OAuth2 configuration is incomplete"):
        AuthConfig(client_id="test_client_id", client_secret="test_client_secret")

    # Three fields provided
    with pytest.raises(ValueError, match="OAuth2 configuration is incomplete"):
        AuthConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
        )
