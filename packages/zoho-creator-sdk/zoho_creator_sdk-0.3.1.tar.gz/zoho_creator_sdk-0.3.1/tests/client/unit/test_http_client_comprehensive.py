"""Comprehensive unit tests for HTTPClient."""

from __future__ import annotations

from typing import Dict
from unittest.mock import Mock, patch

import httpx
import pytest

from zoho_creator_sdk.auth import BaseAuthHandler
from zoho_creator_sdk.client import HTTPClient
from zoho_creator_sdk.exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    NetworkError,
    RateLimitError,
    ResourceNotFoundError,
    ServerError,
    ZohoPermissionError,
)
from zoho_creator_sdk.models import APIConfig


class MockAuthHandler(BaseAuthHandler):
    """Mock auth handler for testing."""

    def get_auth_headers(self) -> Dict[str, str]:
        return {"Authorization": "Bearer test_token"}

    def refresh_auth(self) -> None:
        pass


class TestHTTPClient:
    """Test cases for HTTPClient class."""

    def test_initialization(self) -> None:
        """HTTPClient initializes correctly with auth handler and config."""
        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key", timeout=30.0)

        http_client = HTTPClient(auth_handler, config)

        assert http_client.auth_handler == auth_handler
        assert http_client.config == config
        assert http_client.client.timeout == httpx.Timeout(30.0)
        assert "User-Agent" in http_client.client.headers
        assert http_client.client.headers["User-Agent"] == "zoho-creator-sdk/0.1.0"
        assert http_client.client.headers["Content-Type"] == "application/json"

    def test_initialization_with_environment(self) -> None:
        """HTTPClient includes environment header when provided."""
        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key", environment="development")

        http_client = HTTPClient(auth_handler, config)

        assert http_client.client.headers["environment"] == "development"

    def test_initialization_with_demo_user(self) -> None:
        """HTTPClient includes demo_user_name header when provided."""
        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key", demo_user_name="test_user")

        http_client = HTTPClient(auth_handler, config)

        assert http_client.client.headers["demo_user_name"] == "test_user"

    @patch("httpx.Client.request")
    def test_get_success(self, mock_request: Mock) -> None:
        """HTTPClient GET request succeeds."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test", "status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        result = http_client.get("https://api.example.com/test")

        assert result == {"data": "test", "status": "success"}
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "https://api.example.com/test"
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"

    @patch("httpx.Client.request")
    def test_get_with_params_and_headers(self, mock_request: Mock) -> None:
        """HTTPClient GET request includes params and custom headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        params = {"param1": "value1", "param2": "value2"}
        headers = {"Custom-Header": "custom_value"}
        result = http_client.get("https://api.example.com/test", params, headers)

        assert result == {"data": "test"}
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "https://api.example.com/test"
        assert call_args[1]["params"] == params
        assert call_args[1]["headers"]["Custom-Header"] == "custom_value"
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"

    @patch("httpx.Client.request")
    def test_post_success(self, mock_request: Mock) -> None:
        """HTTPClient POST request succeeds."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123", "status": "created"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        data = {"name": "test", "value": 100}
        result = http_client.post("https://api.example.com/test", data)

        assert result == {"id": "123", "status": "created"}
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "https://api.example.com/test"
        assert call_args[1]["json"] == data
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"

    @patch("httpx.Client.request")
    def test_patch_success(self, mock_request: Mock) -> None:
        """HTTPClient PATCH request succeeds."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "status": "updated"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        data = {"name": "updated", "value": 200}
        result = http_client.patch("https://api.example.com/test/123", data)

        assert result == {"id": "123", "status": "updated"}
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "PATCH"
        assert call_args[0][1] == "https://api.example.com/test/123"
        assert call_args[1]["json"] == data
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"

    @patch("httpx.Client.request")
    def test_delete_success(self, mock_request: Mock) -> None:
        """HTTPClient DELETE request succeeds."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.text = ""
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        result = http_client.delete("https://api.example.com/test/123")

        assert result == {}
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1] == "https://api.example.com/test/123"
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"

    @patch("httpx.Client.request")
    def test_authentication_error(self, mock_request: Mock) -> None:
        """HTTPClient handles authentication errors."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=Mock(), response=mock_response
        )
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(AuthenticationError):
            http_client.get("https://api.example.com/test")

    @patch("httpx.Client.request")
    def test_rate_limit_error(self, mock_request: Mock) -> None:
        """HTTPClient handles rate limit errors."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"retry-after": "1"}
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests", request=Mock(), response=mock_response
        )
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(RateLimitError):
            http_client.get("https://api.example.com/test")

        # Should retry multiple times before giving up
        assert mock_request.call_count >= 4

    @patch("httpx.Client.request")
    def test_permission_error(self, mock_request: Mock) -> None:
        """HTTPClient handles permission errors."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": "Permission denied"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 Forbidden", request=Mock(), response=mock_response
        )
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(ZohoPermissionError):
            http_client.get("https://api.example.com/test")

    @patch("httpx.Client.request")
    def test_not_found_error(self, mock_request: Mock) -> None:
        """HTTPClient handles not found errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Resource not found"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=mock_response
        )
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(ResourceNotFoundError):
            http_client.get("https://api.example.com/test")

    @patch("httpx.Client.request")
    def test_bad_request_error(self, mock_request: Mock) -> None:
        """HTTPClient handles bad request errors."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Bad request"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", request=Mock(), response=mock_response
        )
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(BadRequestError):
            http_client.get("https://api.example.com/test")

    # Note: QuotaExceededError uses the same HTTP status code (429) as RateLimitError
    # and is tested through the rate limit error test above

    @patch("httpx.Client.request")
    def test_server_error(self, mock_request: Mock) -> None:
        """HTTPClient handles server errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error", request=Mock(), response=mock_response
        )
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(ServerError):
            http_client.get("https://api.example.com/test")

    @patch("httpx.Client.request")
    def test_network_error(self, mock_request: Mock) -> None:
        """HTTPClient handles network errors."""
        mock_request.side_effect = httpx.ConnectError("Connection failed")

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(NetworkError):
            http_client.get("https://api.example.com/test")

    @patch("httpx.Client.request")
    def test_timeout_error(self, mock_request: Mock) -> None:
        """HTTPClient handles timeout errors."""
        mock_request.side_effect = httpx.TimeoutException("Request timed out")

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(TimeoutError):
            http_client.get("https://api.example.com/test")

    @patch("httpx.Client.request")
    def test_api_error_unknown_status(self, mock_request: Mock) -> None:
        """HTTPClient handles unknown HTTP errors as generic APIError."""
        mock_response = Mock()
        mock_response.status_code = 418
        mock_response.json.return_value = {"error": "I'm a teapot"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "418 I'm a teapot", request=Mock(), response=mock_response
        )
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(APIError):
            http_client.get("https://api.example.com/test")
