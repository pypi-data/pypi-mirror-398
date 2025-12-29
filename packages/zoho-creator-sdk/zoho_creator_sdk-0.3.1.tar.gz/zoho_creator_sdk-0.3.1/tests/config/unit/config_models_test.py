"""Unit tests for configuration models."""

from __future__ import annotations

import pytest

from zoho_creator_sdk.constants import Datacenter
from zoho_creator_sdk.models import APIConfig, AuthConfig


def test_api_config_base_and_accounts_urls() -> None:
    config = APIConfig(datacenter=Datacenter.EU)

    assert config.base_url == "https://www.zohoapis.eu/creator/v2.1"
    assert config.accounts_url == "https://accounts.zoho.eu"


@pytest.mark.parametrize("value", [199, 1500])
def test_api_config_max_records_validation(value: int) -> None:
    with pytest.raises(ValueError):
        APIConfig(max_records_per_request=value)


def test_api_config_refresh_limits() -> None:
    with pytest.raises(ValueError):
        APIConfig(max_refresh_tokens_per_minute=0)

    with pytest.raises(ValueError):
        APIConfig(max_refresh_tokens_per_user=0)


def test_auth_config_requires_complete_oauth_set() -> None:
    with pytest.raises(ValueError):
        AuthConfig(client_id="id", client_secret="secret")

    config = AuthConfig(
        client_id="id",
        client_secret="secret",
        redirect_uri="https://example.com",
        refresh_token="refresh",
        scopes=["scope"],
    )

    assert config.scopes == ["scope"]
