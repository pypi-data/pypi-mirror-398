"""Unit tests for :class:`zoho_creator_sdk.client.HTTPClient`."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from unittest.mock import Mock

import httpx
import pytest

from zoho_creator_sdk.client import HTTPClient
from zoho_creator_sdk.exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    NetworkError,
    QuotaExceededError,
    RateLimitError,
    ResourceNotFoundError,
    ServerError,
    ZohoPermissionError,
    ZohoTimeoutError,
)
from zoho_creator_sdk.models import APIConfig, AuthConfig


class _StubResponse:
    def __init__(
        self,
        status_code: int,
        payload: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text if text is not None else ("{}" if payload is not None else "")
        self.headers = headers or {}

    def json(self) -> Dict[str, Any]:
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


@pytest.fixture
def http_client(api_config, auth_config) -> HTTPClient:  # type: ignore[override]
    auth = Mock()
    auth.get_auth_headers.return_value = {"Authorization": "token"}
    auth.refresh_auth = Mock()
    client = HTTPClient(auth, api_config)
    client.client = Mock()
    return client


def test_verbs_delegate_to_make_request(http_client: HTTPClient) -> None:
    http_client._make_request = Mock(return_value={})  # type: ignore[assignment]

    http_client.get("url")
    http_client.post("url")
    http_client.patch("url")
    http_client.delete("url")

    assert http_client._make_request.call_count == 4


def test_make_request_returns_processed_payload(http_client: HTTPClient) -> None:
    response = _StubResponse(200, {"ok": True})
    http_client._make_request_with_retry = Mock(  # type: ignore[assignment]
        return_value=response
    )

    result = http_client.get("https://example.com")

    assert result == {"ok": True}


def test_make_request_logs_params_and_body(http_client: HTTPClient) -> None:
    http_client._make_request_with_retry = Mock(  # type: ignore[assignment]
        return_value=_StubResponse(200, {})
    )
    http_client._process_response = Mock(return_value={})  # type: ignore[assignment]

    http_client.get("https://example.com", params={"q": "1"})
    http_client.post("https://example.com", json={"a": 1})

    assert http_client._process_response.call_count == 2


def test_make_request_retries_after_authentication_error(
    http_client: HTTPClient,
) -> None:
    response = _StubResponse(200, {"ok": True})
    http_client._make_request_with_retry = Mock(  # type: ignore[assignment]
        side_effect=[response, response]
    )
    http_client._process_response = Mock(  # type: ignore[assignment]
        side_effect=[AuthenticationError("auth"), {"ok": True}]
    )

    result = http_client.get("https://example.com")

    http_client.auth_handler.refresh_auth.assert_called_once()
    assert result == {"ok": True}


def test_make_request_refresh_failure(http_client: HTTPClient) -> None:
    http_client._make_request_with_retry = Mock(  # type: ignore[assignment]
        return_value=_StubResponse(200, {})
    )
    http_client._process_response = Mock(  # type: ignore[assignment]
        side_effect=AuthenticationError("auth")
    )
    http_client.auth_handler.refresh_auth = Mock(side_effect=AuthenticationError("bad"))

    with pytest.raises(AuthenticationError):
        http_client.get("https://example.com")


def test_make_request_refresh_updates_headers(http_client: HTTPClient) -> None:
    http_client.auth_handler.get_auth_headers.side_effect = [
        {"Authorization": "old"},
        {"Authorization": "new"},
    ]
    http_client._make_request_with_retry = Mock(  # type: ignore[assignment]
        side_effect=[
            _StubResponse(200, {}),
            _StubResponse(200, {"ok": True}),
        ]
    )
    http_client._process_response = Mock(  # type: ignore[assignment]
        side_effect=[AuthenticationError("auth"), {"ok": True}]
    )

    result = http_client.get("https://example.com")

    assert http_client._make_request_with_retry.call_args_list[-1].kwargs[
        "headers"
    ] == {"Authorization": "new"}
    assert result == {"ok": True}


def test_make_request_with_retry_handles_rate_limit(
    http_client: HTTPClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    http_client.client.request = Mock(
        side_effect=[
            _StubResponse(429, {"message": "slow"}, headers={"Retry-After": "0.01"}),
            _StubResponse(200, {"ok": True}),
        ]
    )
    monkeypatch.setattr("zoho_creator_sdk.client.time.sleep", lambda *_: None)

    response = http_client._make_request_with_retry("GET", "url")

    assert isinstance(response, _StubResponse)


def test_make_request_with_retry_raises_server_error(
    http_client: HTTPClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    http_client.client.request = Mock(
        side_effect=[
            _StubResponse(500, {"message": "down", "code": 10}),
            _StubResponse(500, text="no json"),
            _StubResponse(500, text="no json"),
        ]
    )
    monkeypatch.setattr("zoho_creator_sdk.client.time.sleep", lambda *_: None)

    with pytest.raises(ServerError) as exc:
        http_client._make_request_with_retry("GET", "url")

    assert exc.value.status_code == 500


def test_make_request_with_retry_wraps_timeouts(
    http_client: HTTPClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    http_client.client.request = Mock(side_effect=httpx.TimeoutException("slow"))
    monkeypatch.setattr("zoho_creator_sdk.client.time.sleep", lambda *_: None)

    with pytest.raises(TimeoutError):
        http_client._make_request_with_retry("GET", "url")


def test_make_request_with_retry_last_exception(http_client: HTTPClient) -> None:
    http_client.config.max_retries = -1

    with pytest.raises(APIError):
        http_client._make_request_with_retry("GET", "url")


def test_make_request_with_retry_rate_limit_failure(
    http_client: HTTPClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    http_client.client.request = Mock(
        side_effect=[
            _StubResponse(429, {"message": "slow"}, headers={"Retry-After": "0"})
        ]
        * (http_client.config.max_retries + 1)
    )
    monkeypatch.setattr("zoho_creator_sdk.client.time.sleep", lambda *_: None)

    with pytest.raises(RateLimitError):
        http_client._make_request_with_retry("GET", "url")


def test_make_request_with_retry_network_error(
    http_client: HTTPClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    http_client.client.request = Mock(side_effect=httpx.ConnectError("down"))
    monkeypatch.setattr("zoho_creator_sdk.client.time.sleep", lambda *_: None)

    with pytest.raises(NetworkError):
        http_client._make_request_with_retry("GET", "url")


def test_get_retry_after_parses_header(http_client: HTTPClient) -> None:
    response = _StubResponse(429, headers={"Retry-After": "2"})
    assert http_client._get_retry_after(response) == 2.0

    http_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    response.headers["Retry-After"] = http_date
    delay = http_client._get_retry_after(response)
    assert isinstance(delay, float)

    response.headers["Retry-After"] = "invalid"
    assert http_client._get_retry_after(response) == http_client.config.retry_delay


def test_process_response_handles_empty_body(http_client: HTTPClient) -> None:
    empty = _StubResponse(204, text="")
    assert http_client._process_response(empty) == {}

    with pytest.raises(APIError):
        http_client._process_response(_StubResponse(200, text="not json"))


@pytest.mark.parametrize(
    "status, exc",
    [
        (400, BadRequestError),
        (401, AuthenticationError),
        (403, ZohoPermissionError),
        (404, ResourceNotFoundError),
        (408, ZohoTimeoutError),
        (429, QuotaExceededError),
        (500, ServerError),
    ],
)
def test_handle_error_response_raises_expected_exception(
    status: int, exc: type[Exception], http_client: HTTPClient
) -> None:
    response = _StubResponse(status)

    with pytest.raises(exc):
        http_client._handle_error_response(response, {"message": "err", "code": 99})


def test_handle_error_response_defaults_to_api_error(http_client: HTTPClient) -> None:
    with pytest.raises(APIError):
        http_client._handle_error_response(_StubResponse(418), {"message": "teapot"})


def test_http_client_applies_environment_and_demo_headers(
    api_config: APIConfig, auth_config: AuthConfig
) -> None:
    """HTTPClient sets environment and demo_user_name headers from APIConfig."""

    from zoho_creator_sdk.auth import BaseAuthHandler

    class _DummyAuth(BaseAuthHandler):
        def get_auth_headers(self) -> Dict[str, str]:  # type: ignore[override]
            return {"Authorization": "token"}

        def refresh_auth(self) -> None:  # type: ignore[override]
            return None

    api_config.environment = "development"
    api_config.demo_user_name = "demouser_1"

    auth_handler = _DummyAuth()
    client = HTTPClient(auth_handler, api_config)

    assert client.client.headers["environment"] == "development"
    assert client.client.headers["demo_user_name"] == "demouser_1"
