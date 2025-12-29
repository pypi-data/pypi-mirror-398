"""Unit tests for :class:`zoho_creator_sdk.auth.OAuth2AuthHandler`."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from unittest.mock import Mock

import httpx
import pytest

from zoho_creator_sdk.auth import OAuth2AuthHandler, get_auth_handler
from zoho_creator_sdk.constants import Datacenter
from zoho_creator_sdk.exceptions import AuthenticationError, TokenRefreshError
from zoho_creator_sdk.models import APIConfig, AuthConfig


class _DummyResponse:
    """Simple stand-in for :class:`httpx.Response`."""

    def __init__(self, payload: Dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = "payload"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=Mock(), response=self)

    def json(self) -> Dict[str, Any]:
        return self._payload


def _patch_httpx(monkeypatch: pytest.MonkeyPatch, response: _DummyResponse) -> Mock:
    client = Mock(spec=httpx.Client)
    client.post.return_value = response
    cm = Mock()
    cm.__enter__ = Mock(return_value=client)
    cm.__exit__ = Mock(return_value=None)
    monkeypatch.setattr(httpx, "Client", Mock(return_value=cm))
    return client


def test_initialization_requires_core_credentials(auth_config: AuthConfig) -> None:
    """Creation should fail when required credentials are missing."""

    with pytest.raises(AuthenticationError):
        OAuth2AuthHandler(
            client_id="", client_secret="", redirect_uri="", refresh_token=""
        )

    handler = OAuth2AuthHandler(
        client_id=auth_config.client_id,
        client_secret=auth_config.client_secret,
        redirect_uri=auth_config.redirect_uri,
        refresh_token=auth_config.refresh_token,
        datacenter=Datacenter.EU,
    )
    assert handler.datacenter is Datacenter.EU


def test_get_auth_headers_refreshes_when_expired(auth_config: AuthConfig) -> None:
    """Expired tokens trigger a refresh before returning headers."""

    handler = OAuth2AuthHandler(
        client_id=auth_config.client_id,
        client_secret=auth_config.client_secret,
        redirect_uri=auth_config.redirect_uri,
        refresh_token=auth_config.refresh_token,
        access_token="stale",
        token_expiry=datetime.now(timezone.utc) - timedelta(seconds=5),
    )
    handler.refresh_auth = Mock()  # type: ignore[assignment]
    handler.refresh_auth.side_effect = lambda: setattr(handler, "access_token", "fresh")

    headers = handler.get_auth_headers()

    handler.refresh_auth.assert_called_once()
    assert headers["Authorization"] == "Zoho-oauthtoken fresh"


def test_get_auth_headers_raises_when_refresh_not_successful(
    auth_config: AuthConfig,
) -> None:
    handler = OAuth2AuthHandler(
        client_id=auth_config.client_id,
        client_secret=auth_config.client_secret,
        redirect_uri=auth_config.redirect_uri,
        refresh_token=auth_config.refresh_token,
    )
    handler.refresh_auth = Mock(return_value=None)  # type: ignore[assignment]

    with pytest.raises(AuthenticationError):
        handler.get_auth_headers()


@pytest.mark.parametrize(
    "expiry, expected",
    [
        (None, True),
        (datetime.now(timezone.utc) + timedelta(seconds=120), False),
        (datetime.now(timezone.utc) + timedelta(seconds=30), True),
        (datetime.now(timezone.utc) - timedelta(seconds=1), True),
    ],
)
def test_is_token_expired(expiry: Optional[datetime], expected: bool) -> None:
    handler = OAuth2AuthHandler(
        client_id="c",
        client_secret="s",
        redirect_uri="https://example.com",
        refresh_token="r",
        token_expiry=expiry,
    )
    assert handler.is_token_expired() is expected


def test_refresh_auth_updates_token(
    monkeypatch: pytest.MonkeyPatch, auth_config: AuthConfig
) -> None:
    """Successful refresh stores the new token and expiry."""

    response = _DummyResponse({"access_token": "fresh", "expires_in": 120})
    client = _patch_httpx(monkeypatch, response)

    handler = OAuth2AuthHandler(
        client_id=auth_config.client_id,
        client_secret=auth_config.client_secret,
        redirect_uri=auth_config.redirect_uri,
        refresh_token=auth_config.refresh_token,
    )

    handler.refresh_auth()

    client.post.assert_called_once()
    assert handler.access_token == "fresh"
    assert handler.token_expiry and handler.token_expiry > datetime.now(timezone.utc)


def test_refresh_auth_without_token_raises(
    monkeypatch: pytest.MonkeyPatch, auth_config: AuthConfig
) -> None:
    """Missing access token in the payload raises :class:`TokenRefreshError`."""

    response = _DummyResponse({"error": "invalid"})
    _patch_httpx(monkeypatch, response)

    handler = OAuth2AuthHandler(
        client_id=auth_config.client_id,
        client_secret=auth_config.client_secret,
        redirect_uri=auth_config.redirect_uri,
        refresh_token=auth_config.refresh_token,
    )

    with pytest.raises(TokenRefreshError):
        handler.refresh_auth()


def test_refresh_auth_http_error(
    monkeypatch: pytest.MonkeyPatch, auth_config: AuthConfig
) -> None:
    """HTTP errors are converted into :class:`TokenRefreshError`."""

    response = _DummyResponse({"error": "boom"}, status_code=500)
    _patch_httpx(monkeypatch, response)

    handler = OAuth2AuthHandler(
        client_id=auth_config.client_id,
        client_secret=auth_config.client_secret,
        redirect_uri=auth_config.redirect_uri,
        refresh_token=auth_config.refresh_token,
    )

    with pytest.raises(TokenRefreshError):
        handler.refresh_auth()


def test_refresh_auth_request_error(
    monkeypatch: pytest.MonkeyPatch, auth_config: AuthConfig
) -> None:
    """Network failures surface as :class:`TokenRefreshError`."""

    client = Mock(spec=httpx.Client)
    client.post.side_effect = httpx.RequestError("offline", request=Mock())
    cm = Mock()
    cm.__enter__ = Mock(return_value=client)
    cm.__exit__ = Mock(return_value=None)
    monkeypatch.setattr(httpx, "Client", Mock(return_value=cm))

    handler = OAuth2AuthHandler(
        client_id=auth_config.client_id,
        client_secret=auth_config.client_secret,
        redirect_uri=auth_config.redirect_uri,
        refresh_token=auth_config.refresh_token,
    )

    with pytest.raises(TokenRefreshError):
        handler.refresh_auth()


def test_get_auth_handler_builds_oauth_handler(
    auth_config: AuthConfig, api_config: APIConfig
) -> None:
    """`get_auth_handler` converts configuration objects into handlers."""

    handler = get_auth_handler(auth_config, api_config)
    assert isinstance(handler, OAuth2AuthHandler)
    assert handler.datacenter == api_config.datacenter


def test_refresh_auth_includes_scopes_in_request(
    monkeypatch: pytest.MonkeyPatch, auth_config: AuthConfig
) -> None:
    """Scopes are included in the refresh request when provided."""

    response = _DummyResponse({"access_token": "fresh", "expires_in": 120})
    client = _patch_httpx(monkeypatch, response)

    # Create handler with scopes
    handler = OAuth2AuthHandler(
        client_id=auth_config.client_id,
        client_secret=auth_config.client_secret,
        redirect_uri=auth_config.redirect_uri,
        refresh_token=auth_config.refresh_token,
        scopes=["ZohoCreator.fullaccess.all", "ZohoCRM.fullaccess.all"],
    )

    handler.refresh_auth()

    # Verify the request includes scopes
    client.post.assert_called_once()
    call_args = client.post.call_args
    assert call_args is not None
    assert "data" in call_args.kwargs
    assert "scope" in call_args.kwargs["data"]
    assert (
        call_args.kwargs["data"]["scope"]
        == "ZohoCreator.fullaccess.all ZohoCRM.fullaccess.all"
    )
    assert handler.access_token == "fresh"
    assert handler.token_expiry and handler.token_expiry > datetime.now(timezone.utc)


def test_get_auth_handler_without_credentials() -> None:
    """Missing credentials raises :class:`AuthenticationError`."""

    config = AuthConfig(
        client_id=None, client_secret=None, redirect_uri=None, refresh_token=None
    )

    with pytest.raises(AuthenticationError):
        get_auth_handler(config)
