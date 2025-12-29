"""Unit tests for :class:`zoho_creator_sdk.client.PermissionContext`."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from pydantic import ValidationError as PydanticValidationError

from zoho_creator_sdk.client import PermissionContext
from zoho_creator_sdk.exceptions import APIError
from zoho_creator_sdk.models import Permission


class TestPermissionContext:
    """Test cases for PermissionContext class."""

    @pytest.fixture
    def mock_http_client(self) -> Mock:
        """Create a mock HTTP client."""
        client = Mock()
        client.config.base_url = "https://www.zohoapis.com"
        return client

    @pytest.fixture
    def permission_context(self, mock_http_client: Mock) -> PermissionContext:
        """Create a PermissionContext instance for testing."""
        return PermissionContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            permission_id="perm-123",
            owner_name="test-owner",
        )

    def test_initialization(self, mock_http_client: Mock) -> None:
        """PermissionContext initializes correctly."""
        permission_context = PermissionContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            permission_id="perm-123",
            owner_name="test-owner",
        )

        assert permission_context.http_client is mock_http_client
        assert permission_context.app_link_name == "test-app"
        assert permission_context.permission_id == "perm-123"
        assert permission_context.owner_name == "test-owner"

    def test_get_permission_success(
        self, permission_context: PermissionContext
    ) -> None:
        """get_permission makes correct API call and returns Permission object."""
        from datetime import datetime, timezone

        from zoho_creator_sdk.models.enums import EntityType, PermissionType

        now = datetime.now(timezone.utc)
        permission_data = {
            "id": "perm-123",
            "name": "Read Access",
            "entity_type": EntityType.APPLICATION,
            "entity_id": "test-app",
            "permission_type": PermissionType.READ,
            "granted_to_user_id": "user-456",
            "granted_by_user_id": "user-123",
            "created_at": now.isoformat(),
            "modified_at": now.isoformat(),
            "description": "Allows reading records",
            "is_active": True,
        }
        response_data = {"permission": permission_data}

        permission_context.http_client.get.return_value = response_data

        result = permission_context.get_permission()

        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/test-app/permission/perm-123"
        )
        permission_context.http_client.get.assert_called_once_with(expected_url)

        assert isinstance(result, Permission)
        assert result.name == "Read Access"
        assert result.id == "perm-123"

    def test_get_permission_with_minimal_data(
        self, permission_context: PermissionContext
    ) -> None:
        """get_permission handles minimal permission data correctly."""
        from datetime import datetime, timezone

        from zoho_creator_sdk.models.enums import EntityType, PermissionType

        now = datetime.now(timezone.utc)
        permission_data = {
            "id": "perm-basic",
            "name": "Basic Permission",
            "entity_type": EntityType.FORM,
            "entity_id": "form-123",
            "permission_type": PermissionType.READ,
            "granted_to_user_id": "user-456",
            "granted_by_user_id": "user-123",
            "created_at": now.isoformat(),
            "modified_at": now.isoformat(),
        }
        response_data = {"permission": permission_data}

        permission_context.http_client.get.return_value = response_data

        result = permission_context.get_permission()

        assert isinstance(result, Permission)
        assert result.name == "Basic Permission"

    def test_get_permission_with_missing_permission_field(
        self, permission_context: PermissionContext
    ) -> None:
        """get_permission handles response without permission field."""
        response_data = {"status": "success"}  # No permission field

        permission_context.http_client.get.return_value = response_data

        with pytest.raises(APIError) as exc_info:
            permission_context.get_permission()

        assert "Failed to parse permission data" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, PydanticValidationError)

    def test_get_permission_with_invalid_data(
        self, permission_context: PermissionContext
    ) -> None:
        """get_permission raises APIError when permission data is invalid."""
        response_data = {"permission": {"invalid": "data"}}  # Invalid permission data

        permission_context.http_client.get.return_value = response_data

        with pytest.raises(APIError) as exc_info:
            permission_context.get_permission()

        assert "Failed to parse permission data" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, PydanticValidationError)

    def test_update_permission_success(
        self, permission_context: PermissionContext
    ) -> None:
        """update_permission makes correct API call and returns response."""
        update_data = {"permission_name": "Updated Permission", "is_active": False}
        expected_response = {
            "status": "success",
            "permission_id": "perm-123",
            "message": "Permission updated successfully",
        }

        permission_context.http_client.patch.return_value = expected_response

        result = permission_context.update_permission(update_data)

        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/test-app/permission/perm-123"
        )
        expected_payload = {"data": update_data}

        permission_context.http_client.patch.assert_called_once_with(
            expected_url, json=expected_payload
        )
        assert result == expected_response

    def test_update_permission_with_empty_data(
        self, permission_context: PermissionContext
    ) -> None:
        """update_permission handles empty update data correctly."""
        update_data = {}
        expected_response = {"status": "success"}

        permission_context.http_client.patch.return_value = expected_response

        result = permission_context.update_permission(update_data)

        expected_payload = {"data": {}}
        permission_context.http_client.patch.assert_called_once_with(
            "https://www.zohoapis.com/settings/test-owner/test-app/permission/perm-123",
            json=expected_payload,
        )
        assert result == expected_response

    def test_update_permission_with_complex_data(
        self, permission_context: PermissionContext
    ) -> None:
        """update_permission handles complex update data correctly."""
        update_data = {
            "permission_name": "Complex Permission",
            "description": "A complex permission with many fields",
            "is_active": True,
            "conditions": {"field": "status", "operator": "equals", "value": "active"},
            "expiry_date": "2024-12-31",
        }
        expected_response = {"status": "success"}

        permission_context.http_client.patch.return_value = expected_response

        result = permission_context.update_permission(update_data)

        expected_payload = {"data": update_data}
        permission_context.http_client.patch.assert_called_once_with(
            "https://www.zohoapis.com/settings/test-owner/test-app/permission/perm-123",
            json=expected_payload,
        )
        assert result == expected_response

    @pytest.mark.parametrize(
        "app_link_name,permission_id,owner_name,expected_url",
        [
            (
                "app1",
                "perm-123",
                "owner1",
                "https://www.zohoapis.com/settings/owner1/app1/permission/perm-123",
            ),
            (
                "my-app",
                "read-access",
                "john-doe",
                (
                    "https://www.zohoapis.com/settings/"
                    "john-doe/my-app/permission/read-access"
                ),
            ),
            (
                "app_with_underscores",
                "perm_with_underscores",
                "owner_with_underscores",
                (
                    "https://www.zohoapis.com/settings/owner_with_underscores/"
                    "app_with_underscores/permission/perm_with_underscores"
                ),
            ),
        ],
    )
    def test_url_construction(
        self,
        mock_http_client: Mock,
        app_link_name: str,
        permission_id: str,
        owner_name: str,
        expected_url: str,
    ) -> None:
        """PermissionContext constructs URLs correctly from various inputs."""
        from datetime import datetime, timezone

        from zoho_creator_sdk.models.enums import EntityType, PermissionType

        permission_context = PermissionContext(
            http_client=mock_http_client,
            app_link_name=app_link_name,
            permission_id=permission_id,
            owner_name=owner_name,
        )

        # Test get_permission URL
        now = datetime.now(timezone.utc)
        permission_data = {
            "id": permission_id,
            "name": "Test Permission",
            "entity_type": EntityType.APPLICATION,
            "entity_id": app_link_name,
            "permission_type": PermissionType.READ,
            "granted_to_user_id": "user-456",
            "granted_by_user_id": "user-123",
            "created_at": now.isoformat(),
            "modified_at": now.isoformat(),
        }
        permission_context.http_client.get.return_value = {
            "permission": permission_data
        }
        permission_context.get_permission()

        permission_context.http_client.get.assert_called_once_with(expected_url)

        # Test update_permission URL
        update_data = {"permission_name": "Updated"}
        permission_context.http_client.patch.return_value = {"status": "success"}
        permission_context.update_permission(update_data)

        permission_context.http_client.patch.assert_called_once_with(
            expected_url, json={"data": update_data}
        )

    def test_get_permission_api_error_handling(
        self, permission_context: PermissionContext
    ) -> None:
        """get_permission handles API errors correctly."""
        permission_context.http_client.get.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            permission_context.get_permission()

        assert "API Error" in str(exc_info.value)

    def test_update_permission_api_error_handling(
        self, permission_context: PermissionContext
    ) -> None:
        """update_permission handles API errors correctly."""
        permission_context.http_client.patch.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            permission_context.update_permission({"permission_name": "Test"})

        assert "API Error" in str(exc_info.value)

    @pytest.mark.parametrize(
        "permission_id",
        [
            "perm-123",
            "permission-with-dashes",
            "permission_with_underscores",
            "123456789",
            "read_write_access",
        ],
    )
    def test_with_various_permission_ids(
        self, mock_http_client: Mock, permission_id: str
    ) -> None:
        """PermissionContext works with various permission ID formats."""
        from datetime import datetime, timezone

        from zoho_creator_sdk.models.enums import EntityType, PermissionType

        permission_context = PermissionContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            permission_id=permission_id,
            owner_name="test-owner",
        )

        # Test get_permission
        now = datetime.now(timezone.utc)
        permission_data = {
            "id": permission_id,
            "name": "Test Permission",
            "entity_type": EntityType.APPLICATION,
            "entity_id": "test-app",
            "permission_type": PermissionType.READ,
            "granted_to_user_id": "user-456",
            "granted_by_user_id": "user-123",
            "created_at": now.isoformat(),
            "modified_at": now.isoformat(),
        }
        permission_context.http_client.get.return_value = {
            "permission": permission_data
        }
        result = permission_context.get_permission()

        expected_url = (
            f"https://www.zohoapis.com/settings/test-owner/"
            f"test-app/permission/{permission_id}"
        )
        permission_context.http_client.get.assert_called_once_with(expected_url)
        assert isinstance(result, Permission)

    def test_permission_context_methods_are_independent(
        self, permission_context: PermissionContext
    ) -> None:
        """get_permission and update_permission methods work independently."""
        from datetime import datetime, timezone

        from zoho_creator_sdk.models.enums import EntityType, PermissionType

        # Setup get_permission response
        now = datetime.now(timezone.utc)
        permission_data = {
            "id": "perm-123",
            "name": "Test Permission",
            "entity_type": EntityType.APPLICATION,
            "entity_id": "test-app",
            "permission_type": PermissionType.READ,
            "granted_to_user_id": "user-456",
            "granted_by_user_id": "user-123",
            "created_at": now.isoformat(),
            "modified_at": now.isoformat(),
        }
        permission_context.http_client.get.return_value = {
            "permission": permission_data
        }

        # Setup update_permission response
        expected_response = {"status": "success"}
        permission_context.http_client.patch.return_value = expected_response

        # Call both methods
        permission = permission_context.get_permission()
        update_result = permission_context.update_permission(
            {"permission_name": "Updated"}
        )

        # Verify both methods were called
        permission_context.http_client.get.assert_called_once()
        permission_context.http_client.patch.assert_called_once()

        # Verify results
        assert isinstance(permission, Permission)
        assert update_result == expected_response
