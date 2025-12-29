"""Unit tests for :class:`zoho_creator_sdk.client.CustomActionContext`."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from pydantic import ValidationError as PydanticValidationError

from zoho_creator_sdk.client import CustomActionContext
from zoho_creator_sdk.exceptions import APIError
from zoho_creator_sdk.models import CustomAction


class TestCustomActionContext:
    """Test cases for CustomActionContext class."""

    @pytest.fixture
    def mock_http_client(self) -> Mock:
        """Create a mock HTTP client."""
        client = Mock()
        client.config.base_url = "https://www.zohoapis.com"
        return client

    @pytest.fixture
    def custom_action_context(self, mock_http_client: Mock) -> CustomActionContext:
        """Create a CustomActionContext instance for testing."""
        return CustomActionContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            custom_action_link_name="test-action",
            owner_name="test-owner",
        )

    def test_initialization(self, mock_http_client: Mock) -> None:
        """CustomActionContext initializes correctly."""
        custom_action_context = CustomActionContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            custom_action_link_name="test-action",
            owner_name="test-owner",
        )

        assert custom_action_context.http_client is mock_http_client
        assert custom_action_context.app_link_name == "test-app"
        assert custom_action_context.custom_action_link_name == "test-action"
        assert custom_action_context.owner_name == "test-owner"

    def test_get_custom_action_success(
        self, custom_action_context: CustomActionContext
    ) -> None:
        """get_custom_action makes correct API call and returns CustomAction object."""
        action_data = {
            "action_name": "Send Email",
            "action_id": "action-123",
            "description": "Sends an email notification",
            "is_active": True,
        }
        response_data = {"customaction": action_data}

        custom_action_context.http_client.get.return_value = response_data

        result = custom_action_context.get_custom_action()

        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/"
            "test-app/customaction/test-action"
        )
        custom_action_context.http_client.get.assert_called_once_with(expected_url)

        assert isinstance(result, CustomAction)
        assert result.action_name == "Send Email"
        assert result.action_id == "action-123"

    def test_get_custom_action_with_minimal_data(
        self, custom_action_context: CustomActionContext
    ) -> None:
        """get_custom_action handles minimal action data correctly."""
        action_data = {"action_name": "Basic Action"}
        response_data = {"customaction": action_data}

        custom_action_context.http_client.get.return_value = response_data

        result = custom_action_context.get_custom_action()

        assert isinstance(result, CustomAction)
        assert result.action_name == "Basic Action"

    def test_get_custom_action_with_missing_action_field(
        self, custom_action_context: CustomActionContext
    ) -> None:
        """get_custom_action handles response without customaction field."""
        response_data = {"status": "success"}  # No customaction field

        custom_action_context.http_client.get.return_value = response_data

        result = custom_action_context.get_custom_action()

        # Should create CustomAction with empty data
        assert isinstance(result, CustomAction)

    def test_get_custom_action_with_invalid_data(
        self, custom_action_context: CustomActionContext
    ) -> None:
        """get_custom_action raises APIError when action data is invalid."""
        response_data = {"customaction": {"invalid": "data"}}  # Invalid action data

        custom_action_context.http_client.get.return_value = response_data

        with pytest.raises(APIError) as exc_info:
            custom_action_context.get_custom_action()

        assert "Failed to parse custom action data" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, PydanticValidationError)

    def test_execute_custom_action_success(
        self, custom_action_context: CustomActionContext
    ) -> None:
        """execute_custom_action makes correct API call and returns response."""
        record_id = "rec123"
        execution_data = {"param1": "value1", "param2": "value2"}
        expected_response = {
            "status": "success",
            "execution_id": "exec456",
            "message": "Custom action executed successfully",
        }

        custom_action_context.http_client.post.return_value = expected_response

        result = custom_action_context.execute_custom_action(
            record_id, **execution_data
        )

        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/test-app/"
            "customaction/test-action/rec123/execute"
        )
        expected_payload = {"data": execution_data}

        custom_action_context.http_client.post.assert_called_once_with(
            expected_url, json=expected_payload
        )
        assert result == expected_response

    def test_execute_custom_action_without_parameters(
        self, custom_action_context: CustomActionContext
    ) -> None:
        """execute_custom_action works without additional parameters."""
        record_id = "rec123"
        expected_response = {"status": "success"}

        custom_action_context.http_client.post.return_value = expected_response

        result = custom_action_context.execute_custom_action(record_id)

        expected_payload = {"data": {}}
        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/test-app/"
            "customaction/test-action/rec123/execute"
        )
        custom_action_context.http_client.post.assert_called_once_with(
            expected_url, json=expected_payload
        )
        assert result == expected_response

    def test_execute_custom_action_with_complex_parameters(
        self, custom_action_context: CustomActionContext
    ) -> None:
        """execute_custom_action handles complex parameters correctly."""
        record_id = "rec123"
        complex_params = {
            "text_field": "Some text",
            "number_field": 42,
            "boolean_field": True,
            "list_field": ["item1", "item2"],
            "nested_object": {"key": "value"},
        }
        expected_response = {"status": "success"}

        custom_action_context.http_client.post.return_value = expected_response

        result = custom_action_context.execute_custom_action(
            record_id, **complex_params
        )

        expected_payload = {"data": complex_params}
        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/test-app/"
            "customaction/test-action/rec123/execute"
        )
        custom_action_context.http_client.post.assert_called_once_with(
            expected_url, json=expected_payload
        )
        assert result == expected_response

    @pytest.mark.parametrize(
        "app_link_name,custom_action_link_name,owner_name,expected_base_url",
        [
            (
                "app1",
                "action1",
                "owner1",
                "https://www.zohoapis.com/settings/owner1/app1/customaction/action1",
            ),
            (
                "my-app",
                "send-email",
                "john-doe",
                (
                    "https://www.zohoapis.com/settings/"
                    "john-doe/my-app/customaction/send-email"
                ),
            ),
            (
                "app_with_underscores",
                "action_with_underscores",
                "owner_with_underscores",
                (
                    "https://www.zohoapis.com/settings/owner_with_underscores/"
                    "app_with_underscores/customaction/action_with_underscores"
                ),
            ),
        ],
    )
    def test_url_construction(
        self,
        mock_http_client: Mock,
        app_link_name: str,
        custom_action_link_name: str,
        owner_name: str,
        expected_base_url: str,
    ) -> None:
        """CustomActionContext constructs URLs correctly from various inputs."""
        custom_action_context = CustomActionContext(
            http_client=mock_http_client,
            app_link_name=app_link_name,
            custom_action_link_name=custom_action_link_name,
            owner_name=owner_name,
        )

        # Test get_custom_action URL
        action_data = {"action_name": "Test"}
        custom_action_context.http_client.get.return_value = {
            "customaction": action_data
        }
        custom_action_context.get_custom_action()

        custom_action_context.http_client.get.assert_called_once_with(expected_base_url)

        # Test execute_custom_action URL
        record_id = "rec123"
        expected_execute_url = f"{expected_base_url}/{record_id}/execute"
        custom_action_context.http_client.post.return_value = {"status": "success"}
        custom_action_context.execute_custom_action(record_id)

        custom_action_context.http_client.post.assert_called_once_with(
            expected_execute_url, json={"data": {}}
        )

    def test_get_custom_action_api_error_handling(
        self, custom_action_context: CustomActionContext
    ) -> None:
        """get_custom_action handles API errors correctly."""
        custom_action_context.http_client.get.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            custom_action_context.get_custom_action()

        assert "API Error" in str(exc_info.value)

    def test_execute_custom_action_api_error_handling(
        self, custom_action_context: CustomActionContext
    ) -> None:
        """execute_custom_action handles API errors correctly."""
        custom_action_context.http_client.post.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            custom_action_context.execute_custom_action("rec123")

        assert "API Error" in str(exc_info.value)

    @pytest.mark.parametrize(
        "custom_action_link_name",
        [
            "action-123",
            "action-with-dashes",
            "action_with_underscores",
            "123456789",
            "send_email_notification",
        ],
    )
    def test_with_various_action_names(
        self, mock_http_client: Mock, custom_action_link_name: str
    ) -> None:
        """CustomActionContext works with various action name formats."""
        custom_action_context = CustomActionContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            custom_action_link_name=custom_action_link_name,
            owner_name="test-owner",
        )

        # Test get_custom_action
        action_data = {"action_name": "Test"}
        custom_action_context.http_client.get.return_value = {
            "customaction": action_data
        }
        result = custom_action_context.get_custom_action()

        expected_url = (
            f"https://www.zohoapis.com/settings/test-owner/"
            f"test-app/customaction/{custom_action_link_name}"
        )
        custom_action_context.http_client.get.assert_called_once_with(expected_url)
        assert isinstance(result, CustomAction)

    def test_custom_action_context_methods_are_independent(
        self, custom_action_context: CustomActionContext
    ) -> None:
        """get_custom_action and execute_custom_action methods work independently."""
        # Setup get_custom_action response
        action_data = {"action_name": "Test Action"}
        custom_action_context.http_client.get.return_value = {
            "customaction": action_data
        }

        # Setup execute_custom_action response
        expected_response = {"status": "success"}

        # Call both methods
        action = custom_action_context.get_custom_action()

        custom_action_context.http_client.post.return_value = expected_response
        execution_result = custom_action_context.execute_custom_action(
            "rec123", param1="value1"
        )

        # Verify both methods were called
        custom_action_context.http_client.get.assert_called_once()
        custom_action_context.http_client.post.assert_called_once()

        # Verify results
        assert isinstance(action, CustomAction)
        assert execution_result == expected_response
