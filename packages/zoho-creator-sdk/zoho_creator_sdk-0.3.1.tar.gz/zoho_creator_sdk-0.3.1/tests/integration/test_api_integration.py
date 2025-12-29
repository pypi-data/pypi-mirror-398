"""Integration tests for API interactions.

These tests verify the SDK's ability to interact with
the Zoho Creator API endpoints correctly.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from zoho_creator_sdk.client import ZohoCreatorClient
from zoho_creator_sdk.exceptions import APIError, AuthenticationError, NetworkError
from zoho_creator_sdk.models import Application, Permission, Record


class TestAPIIntegration:
    """Test cases for API integration."""

    @pytest.fixture
    def client(self) -> ZohoCreatorClient:
        """Create a ZohoCreatorClient instance with mocked dependencies."""
        with patch(
            "zoho_creator_sdk.client.ConfigManager"
        ) as mock_config_manager, patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ) as mock_get_auth_handler, patch(
            "zoho_creator_sdk.client.HTTPClient"
        ) as mock_http_client_class:
            # Setup mock config manager
            mock_config_manager.return_value.get_auth_config.return_value = Mock()
            mock_config_manager.return_value.get_api_config.return_value = Mock()

            # Setup mock auth handler
            mock_auth_handler = Mock()
            mock_get_auth_handler.return_value = mock_auth_handler

            # Setup mock HTTP client
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            # Create client with mocked dependencies
            client = ZohoCreatorClient()

            # Setup default successful response on the mocked HTTP client
            mock_http_client.get.return_value = Mock(
                status_code=200, json=lambda: {"message": "success"}
            )
            mock_http_client.post.return_value = Mock(
                status_code=201, json=lambda: {"message": "created"}
            )
            mock_http_client.patch.return_value = Mock(
                status_code=200, json=lambda: {"message": "updated"}
            )
            mock_http_client.delete.return_value = Mock(
                status_code=200, json=lambda: {"message": "deleted"}
            )

            return client

    def test_get_applications_success(self, client: ZohoCreatorClient) -> None:
        """Test successful application listing API call."""
        mock_applications = {
            "applications": [
                {
                    "application_name": "Test App",
                    "link_name": "test_app",
                    "creation_date": "2023-01-01",
                    "category": 1,
                    "date_format": "dd-MM-yyyy",
                    "time_zone": "America/New_York",
                    "created_by": "admin@example.com",
                    "workspace_name": "test_workspace",
                }
            ]
        }

        client.http_client.get.return_value = mock_applications

        result = client.get_applications("test_owner")

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Application)
        assert result[0].application_name == "Test App"
        assert result[0].link_name == "test_app"

        # Verify correct API endpoint was called
        client.http_client.get.assert_called_once()

    def test_get_permissions_success(self, client: ZohoCreatorClient) -> None:
        """Test successful permission listing API call."""
        mock_permissions = {
            "permissions": [
                {
                    "id": "123456",
                    "name": "Read Access",
                    "entity_type": "application",
                    "entity_id": "app123",
                    "permission_type": "read",
                    "granted_to_user_id": "user123",
                    "granted_by_user_id": "admin123",
                    "created_at": "2023-01-01T10:00:00Z",
                    "modified_at": "2023-01-01T10:00:00Z",
                }
            ]
        }

        client.http_client.get.return_value = mock_permissions

        result = client.get_permissions("test_owner", "test_app")

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Permission)
        assert result[0].id == "123456"
        assert result[0].name == "Read Access"

        client.http_client.get.assert_called_once()

    def test_update_record_success(self, client: ZohoCreatorClient) -> None:
        """Test successful record update API call."""
        update_data = {"Name": "Updated Name"}

        mock_response_data = {
            "data": {
                "ID": "12345",
                "Name": "Updated Name",
                "Email": "john@example.com",
                "Modified_Time": "2023-01-01T11:00:00Z",
            }
        }

        client.http_client.patch.return_value = mock_response_data

        result = client.update_record(
            "test_owner", "test_app", "test_report", "12345", data=update_data
        )

        assert isinstance(result, dict)
        assert "data" in result
        assert result["data"]["Name"] == "Updated Name"

        client.http_client.patch.assert_called_once()

    def test_delete_record_success(self, client: ZohoCreatorClient) -> None:
        """Test successful record deletion API call."""
        mock_response_data = {"message": "Record deleted successfully"}

        client.http_client.delete.return_value = mock_response_data

        result = client.delete_record("test_owner", "test_app", "test_report", "12345")

        assert isinstance(result, dict)
        assert result["message"] == "Record deleted successfully"

        client.http_client.delete.assert_called_once()

    def test_application_context_operations(self, client: ZohoCreatorClient) -> None:
        """Test application context creation and operations."""
        app_context = client.application("test_app", "test_owner", "Test Application")

        assert app_context.app_link_name == "test_app"
        assert app_context.owner_name == "test_owner"

    def test_form_context_operations(self, client: ZohoCreatorClient) -> None:
        """Test form context creation and operations."""
        form_context = client.form("test_app", "test_owner", "test_form")

        assert form_context.app_link_name == "test_app"
        assert form_context.form_link_name == "test_form"
        assert form_context.owner_name == "test_owner"

        # Mock form data
        mock_form_data = {
            "data": [{"ID": "12345", "Name": "John Doe", "Email": "john@example.com"}]
        }

        client.http_client.get.return_value = mock_form_data

        # Test getting records from form
        records = list(form_context.get_records())
        assert len(records) == 1
        assert isinstance(records[0], Record)
        assert records[0].ID == "12345"

    def test_report_context_operations(self, client: ZohoCreatorClient) -> None:
        """Test report context creation and operations."""
        report_context = client.report("test_app", "test_owner", "test_report")

        assert report_context.app_link_name == "test_app"
        assert report_context.report_link_name == "test_report"
        assert report_context.owner_name == "test_owner"

        # Mock report data
        mock_report_data = {
            "data": [{"ID": "12345", "Name": "John Doe", "Email": "john@example.com"}],
            "meta": {"more_records": False},
        }

        client.http_client.get.return_value = mock_report_data

        # Test getting records from report
        records = list(report_context.get_records())
        assert len(records) == 1
        assert isinstance(records[0], Record)
        assert records[0].ID == "12345"

    def test_workflow_context_operations(self, client: ZohoCreatorClient) -> None:
        """Test workflow context creation and operations."""
        workflow_context = client.workflow("test_app", "test_owner", "test_workflow")

        assert workflow_context.app_link_name == "test_app"
        assert workflow_context.workflow_link_name == "test_workflow"
        assert workflow_context.owner_name == "test_owner"

        # Mock workflow execution
        mock_execution_data = {
            "data": {
                "workflow_id": "workflow123",
                "execution_id": "execution123",
                "status": "success",
            }
        }

        client.http_client.post.return_value = mock_execution_data

        # Test executing workflow
        result = workflow_context.execute_workflow("12345", test_param="test_value")
        assert isinstance(result, dict)
        assert result["data"]["workflow_id"] == "workflow123"

    def test_permission_context_operations(self, client: ZohoCreatorClient) -> None:
        """Test permission context creation and operations."""
        permission_context = client.permission(
            "test_app", "test_owner", "permission123"
        )

        assert permission_context.app_link_name == "test_app"
        assert permission_context.permission_id == "permission123"
        assert permission_context.owner_name == "test_owner"

        # Mock permission data
        mock_permission_data = {
            "permission": {
                "id": "permission123",
                "name": "Read Access",
                "entity_type": "application",
                "entity_id": "app123",
                "permission_type": "read",
                "granted_to_user_id": "user123",
                "granted_by_user_id": "admin123",
                "created_at": "2023-01-01T10:00:00Z",
                "modified_at": "2023-01-01T10:00:00Z",
            }
        }

        client.http_client.get.return_value = mock_permission_data

        # Test getting permission
        permission = permission_context.get_permission()
        assert permission.id == "permission123"
        assert permission.name == "Read Access"

    def test_connection_context_operations(self, client: ZohoCreatorClient) -> None:
        """Test connection context creation and operations."""
        connection_context = client.connection(
            "test_app", "test_owner", "connection123"
        )

        assert connection_context.app_link_name == "test_app"
        assert connection_context.connection_id == "connection123"
        assert connection_context.owner_name == "test_owner"

        # Mock connection test
        mock_test_data = {"status": "success", "message": "Connection successful"}

        client.http_client.get.return_value = mock_test_data

        # Test connection
        result = connection_context.test_connection()
        assert result["status"] == "success"

    def test_custom_action_context_operations(self, client: ZohoCreatorClient) -> None:
        """Test custom action context creation and operations."""
        custom_action_context = client.custom_action(
            "test_app", "test_owner", "action123"
        )

        assert custom_action_context.app_link_name == "test_app"
        assert custom_action_context.custom_action_link_name == "action123"
        assert custom_action_context.owner_name == "test_owner"

        # Mock custom action execution
        mock_execution_data = {
            "data": {
                "action_id": "action123",
                "execution_id": "execution123",
                "status": "success",
            }
        }

        client.http_client.post.return_value = mock_execution_data

        # Test executing custom action
        result = custom_action_context.execute_custom_action(
            "12345", test_param="test_value"
        )
        assert isinstance(result, dict)
        assert result["data"]["action_id"] == "action123"


class TestAPIErrorHandling:
    """Test comprehensive API error handling."""

    @pytest.fixture
    def client(self) -> ZohoCreatorClient:
        """Create a client with mocked HTTP client."""
        with patch(
            "zoho_creator_sdk.client.ConfigManager"
        ) as mock_config_manager, patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ) as mock_get_auth_handler, patch(
            "zoho_creator_sdk.client.HTTPClient"
        ) as mock_http_client_class:
            mock_config_manager.return_value.get_auth_config.return_value = Mock()
            mock_config_manager.return_value.get_api_config.return_value = Mock()
            mock_get_auth_handler.return_value = Mock()
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            client = ZohoCreatorClient()
            return client

    def test_authentication_error(self, client: ZohoCreatorClient) -> None:
        """Test authentication error handling."""
        # Configure the HTTP client mock to raise AuthenticationError
        client.http_client.get.side_effect = AuthenticationError("Invalid token")

        with pytest.raises(AuthenticationError):
            client.get_applications("test_owner")

    def test_network_error_handling(self, client: ZohoCreatorClient) -> None:
        """Test network connectivity error handling."""
        # Configure the HTTP client mock to raise NetworkError
        client.http_client.get.side_effect = NetworkError("Network unreachable")

        with pytest.raises(NetworkError):
            client.get_applications("test_owner")

    def test_api_error_response(self, client: ZohoCreatorClient) -> None:
        """Test API error response handling."""
        # Configure the HTTP client mock to raise APIError
        client.http_client.get.side_effect = APIError("API Error", 400)

        with pytest.raises(APIError):
            client.get_applications("test_owner")
