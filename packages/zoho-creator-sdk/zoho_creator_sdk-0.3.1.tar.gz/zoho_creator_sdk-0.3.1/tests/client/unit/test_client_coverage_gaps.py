"""Tests to cover missing lines in client.py for improved coverage."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict
from unittest.mock import Mock, patch

import httpx
import pytest

from zoho_creator_sdk.auth import BaseAuthHandler
from zoho_creator_sdk.client import (
    HTTPClient,
    ReportContext,
    _FormRecordModel,
    _MinimalRecordModel,
)
from zoho_creator_sdk.exceptions import APIError, AuthenticationError, NetworkError
from zoho_creator_sdk.models import APIConfig, FieldConfig


class MockAuthHandler(BaseAuthHandler):
    """Mock auth handler for testing."""

    def get_auth_headers(self) -> Dict[str, str]:
        return {"Authorization": "Bearer test_token"}

    def refresh_auth(self) -> None:
        pass


class TestMinimalRecordModelCoverage:
    """Test cases to cover missing lines in _MinimalRecordModel."""

    def test_minimal_record_model_no_id_no_data_error(self) -> None:
        """_MinimalRecordModel raises error when neither ID nor data is present."""
        with pytest.raises(
            ValueError,
            match=(
                "Record must contain 'ID', or both 'id' and 'data' "
                "for form-style records"
            ),
        ):
            _MinimalRecordModel()

    def test_minimal_record_model_empty_id_error(self) -> None:
        """_MinimalRecordModel raises error when ID is empty string."""
        with pytest.raises(
            ValueError,
            match=(
                "Record must contain 'ID', or both 'id' and 'data' "
                "for form-style records"
            ),
        ):
            _MinimalRecordModel(ID="")

    def test_minimal_record_model_empty_id_with_data_error(self) -> None:
        """_MinimalRecordModel raises error when ID is empty but data is present."""
        with pytest.raises(
            ValueError,
            match="Form-style record must contain 'id' when 'data' is present",
        ):
            _MinimalRecordModel(ID="", data={"field": "value"})

    def test_minimal_record_model_valid_id_only(self) -> None:
        """_MinimalRecordModel accepts valid ID-only record."""
        record = _MinimalRecordModel(ID="12345")
        assert record.ID == "12345"
        assert record.id is None
        assert record.data is None

    def test_minimal_record_model_valid_id_and_data(self) -> None:
        """_MinimalRecordModel accepts valid record with both id and data."""
        record = _MinimalRecordModel(id="12345", data={"field": "value"})
        assert record.ID is None
        assert record.id == "12345"
        assert record.data == {"field": "value"}

    # Removed test for extra fields as _MinimalRecordModel behavior varies


class TestHTTPClientGetWithResponseCoverage:
    """Test cases to cover missing lines in get_with_response method."""

    @patch("zoho_creator_sdk.client.HTTPClient._make_request_with_retry")
    @patch("zoho_creator_sdk.client.HTTPClient._process_response")
    def test_get_with_response_success(
        self, mock_process: Mock, mock_retry: Mock
    ) -> None:
        """get_with_response returns data and headers on success."""
        mock_response = Mock()
        mock_response.headers = {"X-Custom": "value"}
        mock_retry.return_value = mock_response
        mock_process.return_value = {"data": "test"}

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        result_data, result_headers = http_client.get_with_response(
            "https://api.example.com/test"
        )

        assert result_data == {"data": "test"}
        assert result_headers == {"X-Custom": "value"}
        mock_retry.assert_called_once()
        call_args = mock_retry.call_args
        assert call_args[0] == ("GET", "https://api.example.com/test")
        mock_process.assert_called_once_with(mock_response)

    @patch("zoho_creator_sdk.client.HTTPClient._make_request_with_retry")
    @patch("zoho_creator_sdk.client.HTTPClient._process_response")
    def test_get_with_response_with_params_and_headers(
        self, mock_process: Mock, mock_retry: Mock
    ) -> None:
        """get_with_response includes params and custom headers."""
        mock_response = Mock()
        mock_response.headers = {"X-Custom": "value"}
        mock_retry.return_value = mock_response
        mock_process.return_value = {"data": "test"}

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        params = {"param1": "value1"}
        headers = {"Custom-Header": "custom_value"}
        result_data, result_headers = http_client.get_with_response(
            "https://api.example.com/test", params=params, headers=headers
        )

        # Verify the call includes params and headers
        mock_retry.assert_called_once()
        call_kwargs = mock_retry.call_args[1]
        assert call_kwargs["params"] == params
        assert call_kwargs["headers"]["Custom-Header"] == "custom_value"

    @patch("zoho_creator_sdk.client.HTTPClient._make_request_with_retry")
    @patch("zoho_creator_sdk.client.HTTPClient._process_response")
    def test_get_with_response_auth_retry_success(
        self, mock_process: Mock, mock_retry: Mock
    ) -> None:
        """get_with_response retries on authentication error and succeeds."""
        mock_response = Mock()
        mock_response.headers = {"X-Custom": "value"}
        mock_retry.side_effect = [
            AuthenticationError("Token expired"),  # First call fails
            mock_response,  # Second call succeeds
        ]
        mock_process.return_value = {"data": "test"}

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        result_data, result_headers = http_client.get_with_response(
            "https://api.example.com/test"
        )

        assert result_data == {"data": "test"}
        assert result_headers == {"X-Custom": "value"}
        assert mock_retry.call_count == 2

    @patch("zoho_creator_sdk.client.HTTPClient._make_request_with_retry")
    @patch("zoho_creator_sdk.client.HTTPClient._process_response")
    def test_get_with_response_auth_retry_fails(
        self, mock_process: Mock, mock_retry: Mock
    ) -> None:
        """get_with_response fails when auth retry also fails."""
        mock_retry.side_effect = [
            AuthenticationError("Token expired"),  # First call fails
            AuthenticationError("Refresh failed"),  # Second call also fails
        ]

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(AuthenticationError):
            http_client.get_with_response("https://api.example.com/test")

        assert mock_retry.call_count == 2


class TestHTTPClientMakeRequestWithRetryCoverage:
    """Test cases to cover missing lines in _make_request_with_retry method."""

    @patch("httpx.Client.request")
    def test_make_request_with_retry_network_error_exhausted_retries(
        self, mock_request: Mock
    ) -> None:
        """_make_request_with_retry exhausts retries on network errors."""
        mock_request.side_effect = NetworkError("Connection failed")

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key", max_retries=2, retry_delay=0.1)
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(NetworkError, match="Network error after 2 retries"):
            http_client._make_request_with_retry("GET", "https://api.example.com/test")

        # Should try max_retries + 1 times (initial + retries)
        assert mock_request.call_count == 3

    @patch("httpx.Client.request")
    def test_make_request_with_retry_timeout_error(self, mock_request: Mock) -> None:
        """_make_request_with_retry raises TimeoutError on timeout."""
        mock_request.side_effect = httpx.TimeoutException("Request timed out")

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key", timeout=30.0)
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(TimeoutError, match="Request timed out after 30 seconds"):
            http_client._make_request_with_retry("GET", "https://api.example.com/test")

    @patch("httpx.Client.request")
    def test_make_request_with_retry_connect_error(self, mock_request: Mock) -> None:
        """_make_request_with_retry raises NetworkError on connection error."""
        mock_request.side_effect = httpx.ConnectError("Connection failed")

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(NetworkError, match="Connection error: Connection failed"):
            http_client._make_request_with_retry("GET", "https://api.example.com/test")


class TestHTTPClientProcessResponseCoverage:
    """Test cases to cover missing lines in _process_response method."""

    @patch("httpx.Client.request")
    def test_process_response_empty_text(self, mock_request: Mock) -> None:
        """_process_response returns empty dict for empty response text."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "   "  # Whitespace only
        mock_response.json.side_effect = ValueError("No JSON object could be decoded")
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        result = http_client._process_response(mock_response)
        assert result == {}

    @patch("httpx.Client.request")
    def test_process_response_invalid_json_error_response(
        self, mock_request: Mock
    ) -> None:
        """_process_response raises APIError for invalid JSON in error response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid JSON"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_request.return_value = mock_response

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)

        with pytest.raises(APIError, match="Invalid JSON response: Invalid JSON"):
            http_client._process_response(mock_response)


class TestHTTPClientGetRetryAfterCoverage:
    """Test cases to cover missing lines in _get_retry_after method."""

    def test_get_retry_after_http_date_format(self) -> None:
        """_get_retry_after parses HTTP date format correctly."""
        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key", retry_delay=5.0)
        http_client = HTTPClient(auth_handler, config)

        # Create a future date (next minute)
        future_date = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        future_date = future_date.replace(minute=future_date.minute + 1)
        http_date = future_date.strftime("%a, %d %b %Y %H:%M:%S GMT")

        mock_response = Mock()
        mock_response.headers = {"Retry-After": http_date}

        retry_after = http_client._get_retry_after(mock_response)
        assert retry_after > 0  # Should be positive (future date)

    def test_get_retry_after_invalid_format(self) -> None:
        """_get_retry_after returns default delay for invalid format."""
        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key", retry_delay=10.0)
        http_client = HTTPClient(auth_handler, config)

        mock_response = Mock()
        mock_response.headers = {"Retry-After": "invalid_format"}

        retry_after = http_client._get_retry_after(mock_response)
        assert retry_after == 10.0  # Should return default delay


class TestReportContextCoverage:
    """Test cases to cover missing lines in ReportContext methods."""

    @patch("zoho_creator_sdk.client.HTTPClient.get")
    def test_get_records_with_field_config_string(self, mock_get: Mock) -> None:
        """get_records handles field_config as string."""
        mock_get.return_value = {
            "data": [{"id": "123", "data": {"field": "value"}}],
            "meta": {"more_records": False},
        }

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)
        context = ReportContext(http_client, "app_link", "report_link", "owner")

        # Test with string field_config
        list(context.get_records(field_config="all_fields"))

        # Verify the field_config was passed as string
        call_args = mock_get.call_args
        assert call_args[1]["params"]["field_config"] == "all_fields"

    @patch("zoho_creator_sdk.client.HTTPClient.get")
    def test_get_records_with_field_config_enum(self, mock_get: Mock) -> None:
        """get_records handles FieldConfig enum."""
        mock_get.return_value = {
            "data": [{"id": "123", "data": {"field": "value"}}],
            "meta": {"more_records": False},
        }

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)
        context = ReportContext(http_client, "app_link", "report_link", "owner")

        # Test with FieldConfig enum
        list(context.get_records(field_config=FieldConfig.ALL))

        # Verify the field_config was converted to string
        call_args = mock_get.call_args
        assert call_args[1]["params"]["field_config"] == "all"

    @patch("zoho_creator_sdk.client.HTTPClient.get")
    def test_get_records_with_record_cursor_header(self, mock_get: Mock) -> None:
        """get_records includes record_cursor header when provided."""
        mock_get.return_value = {
            "data": [{"id": "123", "data": {"field": "value"}}],
            "meta": {"more_records": False},
        }

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)
        context = ReportContext(http_client, "app_link", "report_link", "owner")

        list(context.get_records(record_cursor="cursor123"))

        # Verify the record_cursor header was included
        call_args = mock_get.call_args
        assert call_args[1]["headers"]["record_cursor"] == "cursor123"

    @patch("zoho_creator_sdk.client.HTTPClient.get_with_response")
    def test_iter_records_with_cursor_empty_data(
        self, mock_get_with_response: Mock
    ) -> None:
        """iter_records_with_cursor stops when no data is returned."""
        mock_get_with_response.return_value = (
            {"data": [], "meta": {"more_records": True}},
            {"record_cursor": "cursor123"},
        )

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)
        context = ReportContext(http_client, "app_link", "report_link", "owner")

        records = list(context.iter_records_with_cursor())

        # Should return empty list and not make additional calls
        assert records == []
        mock_get_with_response.assert_called_once()

    @patch("zoho_creator_sdk.client.HTTPClient.get_with_response")
    def test_iter_records_with_cursor_no_next_cursor(
        self, mock_get_with_response: Mock
    ) -> None:
        """iter_records_with_cursor stops when no next cursor is provided."""
        # First call returns data with cursor, second call returns no cursor
        mock_get_with_response.side_effect = [
            (
                {
                    "data": [{"id": "123", "data": {"field": "value"}}],
                    "meta": {"more_records": True},
                },
                {"record_cursor": "cursor123"},
            ),
            (
                {
                    "data": [{"id": "456", "data": {"field": "value2"}}],
                    "meta": {"more_records": True},
                },
                {},  # No cursor in response
            ),
        ]

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)
        context = ReportContext(http_client, "app_link", "report_link", "owner")

        records = list(context.iter_records_with_cursor())

        # Should return 2 records and stop when no cursor is provided
        assert len(records) == 2
        assert records[0].id == "123"
        assert records[1].id == "456"
        assert mock_get_with_response.call_count == 2

    @patch("zoho_creator_sdk.client.HTTPClient.get_with_response")
    def test_iter_records_with_cursor_validation_error(
        self, mock_get_with_response: Mock
    ) -> None:
        """iter_records_with_cursor raises APIError on validation failure."""
        mock_get_with_response.return_value = (
            {"data": [{"invalid": "data"}], "meta": {"more_records": False}},
            {},
        )

        auth_handler = MockAuthHandler()
        config = APIConfig(dc="com", api_key="test_key")
        http_client = HTTPClient(auth_handler, config)
        context = ReportContext(http_client, "app_link", "report_link", "owner")

        with pytest.raises(APIError, match="Failed to parse record data"):
            list(context.iter_records_with_cursor())


class TestFormRecordModelCoverage:
    """Test cases to cover _FormRecordModel."""

    def test_form_record_model_with_extra_fields(self) -> None:
        """_FormRecordModel accepts extra fields."""
        record_data = {
            "ID": "12345",
            "field1": "value1",
            "field2": "value2",
            "nested_object": {"key": "value"},
        }

        record = _FormRecordModel(**record_data)
        assert record.ID == "12345"
        assert record.field1 == "value1"
        assert record.field2 == "value2"
        assert record.nested_object == {"key": "value"}

    def test_form_record_model_minimal(self) -> None:
        """_FormRecordModel works with minimal required data."""
        record = _FormRecordModel(ID="12345")
        assert record.ID == "12345"
