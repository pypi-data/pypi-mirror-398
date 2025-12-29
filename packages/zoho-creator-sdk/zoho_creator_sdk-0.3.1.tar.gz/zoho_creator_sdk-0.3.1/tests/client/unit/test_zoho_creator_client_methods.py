"""Unit tests for ZohoCreatorClient additional methods."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from zoho_creator_sdk.client import ZohoCreatorClient
from zoho_creator_sdk.exceptions import APIError
from zoho_creator_sdk.models import Application, Permission


class TestZohoCreatorClientMethods:
    """Test cases for ZohoCreatorClient methods."""

    def test_initialization_with_config_manager(self) -> None:
        """ZohoCreatorClient initializes with ConfigManager."""
        with patch(
            "zoho_creator_sdk.client.ConfigManager"
        ) as mock_config_manager, patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ) as mock_get_auth, patch(
            "zoho_creator_sdk.client.HTTPClient"
        ) as mock_http_client:
            # Mock config manager and its return values
            mock_auth_config = Mock()
            mock_api_config = Mock()

            mock_config_manager.return_value.get_auth_config.return_value = (
                mock_auth_config
            )
            mock_config_manager.return_value.get_api_config.return_value = (
                mock_api_config
            )

            mock_auth_handler = Mock()
            mock_get_auth.return_value = mock_auth_handler

            client = ZohoCreatorClient()

            assert client.config_manager is mock_config_manager.return_value
            assert client.auth_config is mock_auth_config
            assert client.api_config is mock_api_config
            assert client.auth_handler is mock_auth_handler
            mock_get_auth.assert_called_once_with(mock_auth_config, mock_api_config)
            mock_http_client.assert_called_once_with(mock_auth_handler, mock_api_config)

    def test_get_applications_success(self) -> None:
        """get_applications returns list of applications."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            # Setup mock HTTP client
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            # Mock API config
            mock_api_config = Mock()
            mock_api_config.base_url = "https://api.zoho.com"

            client = ZohoCreatorClient()
            client.api_config = mock_api_config
            client.http_client = mock_http_client

            # Mock API response
            apps_data = [
                {
                    "application_name": "App 1",
                    "link_name": "app1",
                    "date_format": "yyyy-MM-dd",
                    "creation_date": "2023-01-01",
                    "category": 1,
                    "time_zone": "America/New_York",
                    "created_by": "test_user",
                    "workspace_name": "Test Workspace",
                },
                {
                    "application_name": "App 2",
                    "link_name": "app2",
                    "date_format": "yyyy-MM-dd",
                    "creation_date": "2023-01-02",
                    "category": 1,
                    "time_zone": "America/New_York",
                    "created_by": "test_user",
                    "workspace_name": "Test Workspace",
                },
            ]
            mock_http_client.get.return_value = {"applications": apps_data}

            result = client.get_applications("test_owner")

            # Verify API call
            expected_url = "https://api.zoho.com/meta/test_owner/applications"
            mock_http_client.get.assert_called_once_with(expected_url)

            # Verify result
            assert len(result) == 2
            assert all(isinstance(app, Application) for app in result)
            assert result[0].link_name == "app1"
            assert result[1].link_name == "app2"

    def test_get_applications_with_no_applications(self) -> None:
        """get_applications handles empty applications list."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            mock_api_config = Mock()
            mock_api_config.base_url = "https://api.zoho.com"

            client = ZohoCreatorClient()
            client.api_config = mock_api_config
            client.http_client = mock_http_client

            mock_http_client.get.return_value = {"applications": []}

            result = client.get_applications("test_owner")

            assert result == []

    def test_get_applications_with_missing_applications_key(self) -> None:
        """get_applications handles missing applications key."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            mock_api_config = Mock()
            mock_api_config.base_url = "https://api.zoho.com"

            client = ZohoCreatorClient()
            client.api_config = mock_api_config
            client.http_client = mock_http_client

            mock_http_client.get.return_value = {"status": "success"}

            result = client.get_applications("test_owner")

            assert result == []

    def test_get_applications_with_invalid_data(self) -> None:
        """get_applications raises APIError for invalid application data."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            mock_api_config = Mock()
            mock_api_config.base_url = "https://api.zoho.com"

            client = ZohoCreatorClient()
            client.api_config = mock_api_config
            client.http_client = mock_http_client

            # Mock response with invalid application data that will fail
            # Pydantic validation
            mock_http_client.get.return_value = {"applications": [{"invalid": "data"}]}

            with pytest.raises(APIError) as exc_info:
                client.get_applications("test_owner")

            assert "Failed to parse application data" in str(exc_info.value)

    def test_get_permissions_success(self) -> None:
        """get_permissions returns list of permissions."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            mock_api_config = Mock()
            mock_api_config.base_url = "https://api.zoho.com"

            client = ZohoCreatorClient()
            client.api_config = mock_api_config
            client.http_client = mock_http_client

            # Mock API response with valid permission data
            from datetime import datetime, timezone

            from zoho_creator_sdk.models.enums import EntityType, PermissionType

            now = datetime.now(timezone.utc)
            perms_data = [
                {
                    "id": "perm1",
                    "name": "Read Access",
                    "entity_type": EntityType.APPLICATION,
                    "entity_id": "app1",
                    "permission_type": PermissionType.READ,
                    "granted_to_user_id": "user1",
                    "granted_by_user_id": "admin",
                    "created_at": now.isoformat(),
                    "modified_at": now.isoformat(),
                },
                {
                    "id": "perm2",
                    "name": "Write Access",
                    "entity_type": EntityType.FORM,
                    "entity_id": "form1",
                    "permission_type": PermissionType.WRITE,
                    "granted_to_user_id": "user2",
                    "granted_by_user_id": "admin",
                    "created_at": now.isoformat(),
                    "modified_at": now.isoformat(),
                },
            ]
            mock_http_client.get.return_value = {"permissions": perms_data}

            result = client.get_permissions("test_owner", "test_app")

            # Verify API call
            expected_url = (
                "https://api.zoho.com/settings/test_owner/test_app/permissions"
            )
            mock_http_client.get.assert_called_once_with(expected_url)

            # Verify result
            assert len(result) == 2
            assert all(isinstance(perm, Permission) for perm in result)
            assert result[0].id == "perm1"
            assert result[1].id == "perm2"

    def test_get_permissions_with_no_permissions(self) -> None:
        """get_permissions handles empty permissions list."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            mock_api_config = Mock()
            mock_api_config.base_url = "https://api.zoho.com"

            client = ZohoCreatorClient()
            client.api_config = mock_api_config
            client.http_client = mock_http_client

            mock_http_client.get.return_value = {"permissions": []}

            result = client.get_permissions("test_owner", "test_app")

            assert result == []

    def test_get_permissions_with_missing_permissions_key(self) -> None:
        """get_permissions handles missing permissions key."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            mock_api_config = Mock()
            mock_api_config.base_url = "https://api.zoho.com"

            client = ZohoCreatorClient()
            client.api_config = mock_api_config
            client.http_client = mock_http_client

            mock_http_client.get.return_value = {"status": "success"}

            result = client.get_permissions("test_owner", "test_app")

            assert result == []

    def test_get_permissions_with_invalid_data(self) -> None:
        """get_permissions raises APIError for invalid permission data."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            mock_api_config = Mock()
            mock_api_config.base_url = "https://api.zoho.com"

            client = ZohoCreatorClient()
            client.api_config = mock_api_config
            client.http_client = mock_http_client

            mock_http_client.get.return_value = {"permissions": [{"invalid": "data"}]}

            with pytest.raises(APIError) as exc_info:
                client.get_permissions("test_owner", "test_app")

            assert "Failed to parse permission data" in str(exc_info.value)

    def test_update_record_success(self) -> None:
        """update_record makes correct API call and returns response."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            mock_api_config = Mock()
            mock_api_config.base_url = "https://api.zoho.com"

            client = ZohoCreatorClient()
            client.api_config = mock_api_config
            client.http_client = mock_http_client

            update_data = {"name": "Updated Name", "status": "Active"}
            expected_response = {
                "id": "123",
                "name": "Updated Name",
                "status": "Active",
            }

            mock_http_client.patch.return_value = expected_response

            result = client.update_record(
                owner_name="test_owner",
                app_link_name="test_app",
                report_link_name="test_report",
                record_id="record123",
                data=update_data,
            )

            # Verify API call
            expected_url = (
                "https://api.zoho.com/data/test_owner/test_app/"
                "report/test_report/record123"
            )
            expected_payload = {"data": update_data}
            mock_http_client.patch.assert_called_once_with(
                expected_url, json=expected_payload
            )

            assert result == expected_response

    def test_update_record_with_empty_data(self) -> None:
        """update_record handles empty update data."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            mock_api_config = Mock()
            mock_api_config.base_url = "https://api.zoho.com"

            client = ZohoCreatorClient()
            client.api_config = mock_api_config
            client.http_client = mock_http_client

            update_data = {}
            expected_response = {"status": "success"}

            mock_http_client.patch.return_value = expected_response

            result = client.update_record(
                owner_name="test_owner",
                app_link_name="test_app",
                report_link_name="test_report",
                record_id="record123",
                data=update_data,
            )

            expected_payload = {"data": {}}
            mock_http_client.patch.assert_called_once_with(
                (
                    "https://api.zoho.com/data/test_owner/test_app/"
                    "report/test_report/record123"
                ),
                json=expected_payload,
            )

            assert result == expected_response

    def test_delete_record_success(self) -> None:
        """delete_record makes correct API call and returns response."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            mock_api_config = Mock()
            mock_api_config.base_url = "https://api.zoho.com"

            client = ZohoCreatorClient()
            client.api_config = mock_api_config
            client.http_client = mock_http_client

            expected_response = {"status": "success", "message": "Record deleted"}

            mock_http_client.delete.return_value = expected_response

            result = client.delete_record(
                owner_name="test_owner",
                app_link_name="test_app",
                report_link_name="test_report",
                record_id="record123",
            )

            # Verify API call
            expected_url = (
                "https://api.zoho.com/data/test_owner/test_app/"
                "report/test_report/record123"
            )
            mock_http_client.delete.assert_called_once_with(expected_url)

            assert result == expected_response

    def test_workflow_context_creation(self) -> None:
        """workflow method creates WorkflowContext correctly."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            client = ZohoCreatorClient()

            workflow_context = client.workflow(
                app_link_name="test_app",
                owner_name="test_owner",
                workflow_link_name="test_workflow",
            )

            # Verify the context was created with correct parameters
            assert workflow_context.http_client is mock_http_client
            assert workflow_context.app_link_name == "test_app"
            assert workflow_context.owner_name == "test_owner"
            assert workflow_context.workflow_link_name == "test_workflow"

    def test_permission_context_creation(self) -> None:
        """permission method creates PermissionContext correctly."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            client = ZohoCreatorClient()

            permission_context = client.permission(
                app_link_name="test_app",
                owner_name="test_owner",
                permission_id="perm123",
            )

            assert permission_context.http_client is mock_http_client
            assert permission_context.app_link_name == "test_app"
            assert permission_context.owner_name == "test_owner"
            assert permission_context.permission_id == "perm123"

    def test_connection_context_creation(self) -> None:
        """connection method creates ConnectionContext correctly."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            client = ZohoCreatorClient()

            connection_context = client.connection(
                app_link_name="test_app",
                owner_name="test_owner",
                connection_id="conn123",
            )

            assert connection_context.http_client is mock_http_client
            assert connection_context.app_link_name == "test_app"
            assert connection_context.owner_name == "test_owner"
            assert connection_context.connection_id == "conn123"

    def test_custom_action_context_creation(self) -> None:
        """custom_action method creates CustomActionContext correctly."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            client = ZohoCreatorClient()

            custom_action_context = client.custom_action(
                app_link_name="test_app",
                owner_name="test_owner",
                custom_action_link_name="action123",
            )

            assert custom_action_context.http_client is mock_http_client
            assert custom_action_context.app_link_name == "test_app"
            assert custom_action_context.owner_name == "test_owner"
            assert custom_action_context.custom_action_link_name == "action123"

    def test_form_context_creation(self) -> None:
        """form method creates FormContext correctly."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            client = ZohoCreatorClient()

            form_context = client.form(
                app_link_name="test_app",
                owner_name="test_owner",
                form_link_name="form123",
            )

            assert form_context.http_client is mock_http_client
            assert form_context.app_link_name == "test_app"
            assert form_context.owner_name == "test_owner"
            assert form_context.form_link_name == "form123"

    def test_report_context_creation(self) -> None:
        """report method creates ReportContext correctly."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            client = ZohoCreatorClient()

            report_context = client.report(
                app_link_name="test_app",
                owner_name="test_owner",
                report_link_name="report123",
            )

            assert report_context.http_client is mock_http_client
            assert report_context.app_link_name == "test_app"
            assert report_context.owner_name == "test_owner"
            assert report_context.report_link_name == "report123"

    def test_page_context_creation(self) -> None:
        """page method creates PageContext correctly."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            client = ZohoCreatorClient()

            page_context = client.page(
                app_link_name="test_app",
                owner_name="test_owner",
                page_link_name="page123",
            )

            assert page_context.http_client is mock_http_client
            assert page_context.app_link_name == "test_app"
            assert page_context.owner_name == "test_owner"
            assert page_context.page_link_name == "page123"

    def test_section_context_creation(self) -> None:
        """section method creates SectionContext correctly."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            client = ZohoCreatorClient()

            section_context = client.section(
                app_link_name="test_app",
                owner_name="test_owner",
                section_link_name="section123",
            )

            assert section_context.http_client is mock_http_client
            assert section_context.app_link_name == "test_app"
            assert section_context.owner_name == "test_owner"
            assert section_context.section_link_name == "section123"

    def test_application_context_creation(self) -> None:
        """application method creates AppContext correctly."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            client = ZohoCreatorClient()

            app_context = client.application(
                app_link_name="test_app", owner_name="test_owner", app_name="Test App"
            )

            assert app_context.http_client is mock_http_client
            assert app_context.app_link_name == "test_app"
            assert app_context.owner_name == "test_owner"

    def test_application_context_creation_without_app_name(self) -> None:
        """application method creates AppContext without app name."""
        with patch("zoho_creator_sdk.client.ConfigManager"), patch(
            "zoho_creator_sdk.client.get_auth_handler"
        ), patch("zoho_creator_sdk.client.HTTPClient") as mock_http_client_class:
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            client = ZohoCreatorClient()

            app_context = client.application(
                app_link_name="test_app", owner_name="test_owner"
            )

            assert app_context.http_client is mock_http_client
            assert app_context.app_link_name == "test_app"
            assert app_context.owner_name == "test_owner"
