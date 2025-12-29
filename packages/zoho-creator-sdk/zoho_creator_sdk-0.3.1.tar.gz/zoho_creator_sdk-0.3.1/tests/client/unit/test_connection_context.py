"""Unit tests for :class:`zoho_creator_sdk.client.ConnectionContext`."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from pydantic import ValidationError as PydanticValidationError

from zoho_creator_sdk.client import ConnectionContext
from zoho_creator_sdk.exceptions import APIError
from zoho_creator_sdk.models import Connection


class TestConnectionContext:
    """Test cases for ConnectionContext class."""

    @pytest.fixture
    def mock_http_client(self) -> Mock:
        """Create a mock HTTP client."""
        client = Mock()
        client.config.base_url = "https://www.zohoapis.com"
        return client

    @pytest.fixture
    def connection_context(self, mock_http_client: Mock) -> ConnectionContext:
        """Create a ConnectionContext instance for testing."""
        return ConnectionContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            connection_id="conn-123",
            owner_name="test-owner",
        )

    def test_initialization(self, mock_http_client: Mock) -> None:
        """ConnectionContext initializes correctly."""
        connection_context = ConnectionContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            connection_id="conn-123",
            owner_name="test-owner",
        )

        assert connection_context.http_client is mock_http_client
        assert connection_context.app_link_name == "test-app"
        assert connection_context.connection_id == "conn-123"
        assert connection_context.owner_name == "test-owner"

    def test_get_connection_success(
        self, connection_context: ConnectionContext
    ) -> None:
        """get_connection makes correct API call and returns Connection object."""
        connection_data = {
            "connection_name": "Database Connection",
            "connection_id": "conn-123",
            "description": "Connects to external database",
            "is_active": True,
            "connection_type": "database",
        }
        response_data = {"connection": connection_data}

        connection_context.http_client.get.return_value = response_data

        result = connection_context.get_connection()

        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/test-app/connection/conn-123"
        )
        connection_context.http_client.get.assert_called_once_with(expected_url)

        assert isinstance(result, Connection)
        assert result.connection_name == "Database Connection"
        assert result.connection_id == "conn-123"

    def test_get_connection_with_minimal_data(
        self, connection_context: ConnectionContext
    ) -> None:
        """get_connection handles minimal connection data correctly."""
        connection_data = {"connection_name": "Basic Connection"}
        response_data = {"connection": connection_data}

        connection_context.http_client.get.return_value = response_data

        result = connection_context.get_connection()

        assert isinstance(result, Connection)
        assert result.connection_name == "Basic Connection"

    def test_get_connection_with_missing_connection_field(
        self, connection_context: ConnectionContext
    ) -> None:
        """get_connection handles response without connection field."""
        response_data = {"status": "success"}  # No connection field

        connection_context.http_client.get.return_value = response_data

        result = connection_context.get_connection()

        # Should create Connection with empty data
        assert isinstance(result, Connection)

    def test_get_connection_with_invalid_data(
        self, connection_context: ConnectionContext
    ) -> None:
        """get_connection raises APIError when connection data is invalid."""
        response_data = {"connection": {"invalid": "data"}}  # Invalid connection data

        connection_context.http_client.get.return_value = response_data

        with pytest.raises(APIError) as exc_info:
            connection_context.get_connection()

        assert "Failed to parse connection data" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, PydanticValidationError)

    def test_test_connection_success(
        self, connection_context: ConnectionContext
    ) -> None:
        """test_connection makes correct API call and returns response."""
        expected_response = {
            "status": "success",
            "message": "Connection test successful",
            "response_time": 150,
            "timestamp": "2024-01-01T10:00:00Z",
        }

        connection_context.http_client.get.return_value = expected_response

        result = connection_context.test_connection()

        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/"
            "test-app/connection/conn-123/test"
        )
        connection_context.http_client.get.assert_called_once_with(expected_url)
        assert result == expected_response

    def test_test_connection_failure_response(
        self, connection_context: ConnectionContext
    ) -> None:
        """test_connection handles failure response correctly."""
        failure_response = {
            "status": "failure",
            "message": "Connection test failed",
            "error": "Timeout occurred",
            "response_time": 5000,
        }

        connection_context.http_client.get.return_value = failure_response

        result = connection_context.test_connection()

        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/"
            "test-app/connection/conn-123/test"
        )
        connection_context.http_client.get.assert_called_once_with(expected_url)
        assert result == failure_response

    def test_test_connection_with_empty_response(
        self, connection_context: ConnectionContext
    ) -> None:
        """test_connection handles empty response correctly."""
        empty_response = {}

        connection_context.http_client.get.return_value = empty_response

        result = connection_context.test_connection()

        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/"
            "test-app/connection/conn-123/test"
        )
        connection_context.http_client.get.assert_called_once_with(expected_url)
        assert result == empty_response

    @pytest.mark.parametrize(
        "app_link_name,connection_id,owner_name,expected_base_url",
        [
            (
                "app1",
                "conn-123",
                "owner1",
                "https://www.zohoapis.com/settings/owner1/app1/connection/conn-123",
            ),
            (
                "my-app",
                "db-connection",
                "john-doe",
                (
                    "https://www.zohoapis.com/settings/"
                    "john-doe/my-app/connection/db-connection"
                ),
            ),
            (
                "app_with_underscores",
                "conn_with_underscores",
                "owner_with_underscores",
                (
                    "https://www.zohoapis.com/settings/owner_with_underscores/"
                    "app_with_underscores/connection/conn_with_underscores"
                ),
            ),
        ],
    )
    def test_url_construction(
        self,
        mock_http_client: Mock,
        app_link_name: str,
        connection_id: str,
        owner_name: str,
        expected_base_url: str,
    ) -> None:
        """ConnectionContext constructs URLs correctly from various inputs."""
        connection_context = ConnectionContext(
            http_client=mock_http_client,
            app_link_name=app_link_name,
            connection_id=connection_id,
            owner_name=owner_name,
        )

        # Test get_connection URL
        connection_data = {"connection_name": "Test"}
        connection_context.http_client.get.return_value = {
            "connection": connection_data
        }
        connection_context.get_connection()

        connection_context.http_client.get.assert_called_once_with(expected_base_url)

        # Test test_connection URL
        expected_test_url = f"{expected_base_url}/test"
        connection_context.http_client.get.return_value = {"status": "success"}
        connection_context.test_connection()

        connection_context.http_client.get.assert_called_with(expected_test_url)

    def test_get_connection_api_error_handling(
        self, connection_context: ConnectionContext
    ) -> None:
        """get_connection handles API errors correctly."""
        connection_context.http_client.get.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            connection_context.get_connection()

        assert "API Error" in str(exc_info.value)

    def test_test_connection_api_error_handling(
        self, connection_context: ConnectionContext
    ) -> None:
        """test_connection handles API errors correctly."""
        connection_context.http_client.get.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            connection_context.test_connection()

        assert "API Error" in str(exc_info.value)

    @pytest.mark.parametrize(
        "connection_id",
        [
            "conn-123",
            "connection-with-dashes",
            "connection_with_underscores",
            "123456789",
            "db_connection_main",
        ],
    )
    def test_with_various_connection_ids(
        self, mock_http_client: Mock, connection_id: str
    ) -> None:
        """ConnectionContext works with various connection ID formats."""
        connection_context = ConnectionContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            connection_id=connection_id,
            owner_name="test-owner",
        )

        # Test get_connection
        connection_data = {"connection_name": "Test"}
        connection_context.http_client.get.return_value = {
            "connection": connection_data
        }
        result = connection_context.get_connection()

        expected_url = (
            f"https://www.zohoapis.com/settings/test-owner/"
            f"test-app/connection/{connection_id}"
        )
        connection_context.http_client.get.assert_called_once_with(expected_url)
        assert isinstance(result, Connection)

    def test_connection_context_methods_are_independent(
        self, connection_context: ConnectionContext
    ) -> None:
        """get_connection and test_connection methods work independently."""
        # Setup get_connection response
        connection_data = {"connection_name": "Test Connection"}
        connection_context.http_client.get.return_value = {
            "connection": connection_data
        }

        # Setup test_connection response
        test_response = {"status": "success"}

        # Call both methods
        connection = connection_context.get_connection()

        # Reset mock for test_connection
        connection_context.http_client.get.reset_mock()
        connection_context.http_client.get.return_value = test_response
        test_result = connection_context.test_connection()

        # Verify both methods were called
        connection_context.http_client.get.assert_called_once()

        # Verify results
        assert isinstance(connection, Connection)
        assert test_result == test_response

    def test_test_connection_with_various_responses(
        self, connection_context: ConnectionContext
    ) -> None:
        """test_connection handles various response formats correctly."""
        test_cases = [
            {"status": "success", "message": "OK"},
            {"status": "failure", "error": "Connection failed"},
            {"connected": True, "latency": 100},
            {"result": "tested", "details": {"timeout": 30}},
            {},  # Empty response
        ]

        for i, response_data in enumerate(test_cases):
            connection_context.http_client.get.return_value = response_data

            result = connection_context.test_connection()

            expected_url = (
                "https://www.zohoapis.com/settings/test-owner/"
                "test-app/connection/conn-123/test"
            )
            connection_context.http_client.get.assert_called_once_with(expected_url)
            assert result == response_data

            # Reset mock for next iteration
            connection_context.http_client.get.reset_mock()
