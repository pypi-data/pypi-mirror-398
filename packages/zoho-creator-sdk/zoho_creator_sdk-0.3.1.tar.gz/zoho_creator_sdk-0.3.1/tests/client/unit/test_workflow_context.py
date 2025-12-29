"""Unit tests for :class:`zoho_creator_sdk.client.WorkflowContext`."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from pydantic import ValidationError as PydanticValidationError

from zoho_creator_sdk.client import WorkflowContext
from zoho_creator_sdk.exceptions import APIError
from zoho_creator_sdk.models import Workflow


class TestWorkflowContext:
    """Test cases for WorkflowContext class."""

    @pytest.fixture
    def mock_http_client(self) -> Mock:
        """Create a mock HTTP client."""
        client = Mock()
        client.config.base_url = "https://www.zohoapis.com"
        return client

    @pytest.fixture
    def workflow_context(self, mock_http_client: Mock) -> WorkflowContext:
        """Create a WorkflowContext instance for testing."""
        return WorkflowContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            workflow_link_name="test-workflow",
            owner_name="test-owner",
        )

    def test_initialization(self, mock_http_client: Mock) -> None:
        """WorkflowContext initializes correctly."""
        workflow_context = WorkflowContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            workflow_link_name="test-workflow",
            owner_name="test-owner",
        )

        assert workflow_context.http_client is mock_http_client
        assert workflow_context.app_link_name == "test-app"
        assert workflow_context.workflow_link_name == "test-workflow"
        assert workflow_context.owner_name == "test-owner"

    def test_get_workflow_success(self, workflow_context: WorkflowContext) -> None:
        """get_workflow makes correct API call and returns Workflow object."""
        from datetime import datetime

        workflow_data = {
            "id": "workflow-123",
            "name": "Test Workflow",
            "link_name": "test-workflow",
            "description": "A test workflow",
            "application_id": "test-app",
            "form_id": "test-form",
            "workflow_type": "scheduled",
            "active": True,
            "owner": "test-owner",
            "created_time": datetime.utcnow().isoformat(),
            "modified_time": datetime.utcnow().isoformat(),
            "triggers": [
                {
                    "id": "trigger-1",
                    "workflow_id": "workflow-123",
                    "trigger_type": "form_submitted",
                    "name": "Form Submission Trigger",
                    "enabled": True,
                    "conditions": [],
                }
            ],
            "actions": [
                {
                    "id": "action-1",
                    "workflow_id": "workflow-123",
                    "action_type": "field_update",
                    "name": "Update Field Action",
                    "execution_order": 1,
                    "enabled": True,
                    "field_update_config": {"field_updates": {"status": "processed"}},
                }
            ],
        }
        response_data = {"workflow": workflow_data}

        workflow_context.http_client.get.return_value = response_data

        result = workflow_context.get_workflow()

        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/"
            "test-app/workflow/test-workflow"
        )
        workflow_context.http_client.get.assert_called_once_with(expected_url)

        assert isinstance(result, Workflow)
        assert result.name == "Test Workflow"
        assert result.id == "workflow-123"

    def test_get_workflow_with_minimal_data(
        self, workflow_context: WorkflowContext
    ) -> None:
        """get_workflow handles minimal workflow data correctly."""
        from datetime import datetime

        workflow_data = {
            "id": "minimal-workflow",
            "name": "Minimal Workflow",
            "link_name": "minimal-workflow",
            "application_id": "test-app",
            "form_id": "test-form",
            "workflow_type": "conditional",
            "owner": "test-owner",
            "created_time": datetime.utcnow().isoformat(),
            "modified_time": datetime.utcnow().isoformat(),
            "triggers": [
                {
                    "id": "minimal-trigger",
                    "workflow_id": "minimal-workflow",
                    "trigger_type": "scheduled",
                    "name": "Manual Trigger",
                    "enabled": True,
                    "conditions": [],
                }
            ],
            "actions": [
                {
                    "id": "minimal-action",
                    "workflow_id": "minimal-workflow",
                    "action_type": "field_update",
                    "name": "Minimal Action",
                    "execution_order": 1,
                    "enabled": True,
                    "field_update_config": {"field_updates": {"status": "processed"}},
                }
            ],
        }
        response_data = {"workflow": workflow_data}

        workflow_context.http_client.get.return_value = response_data

        result = workflow_context.get_workflow()

        assert isinstance(result, Workflow)
        assert result.name == "Minimal Workflow"
        assert result.id == "minimal-workflow"

    def test_get_workflow_with_missing_workflow_field(
        self, workflow_context: WorkflowContext
    ) -> None:
        """get_workflow handles response without workflow field."""
        response_data = {"status": "success"}  # No workflow field

        workflow_context.http_client.get.return_value = response_data

        # Should raise APIError when workflow data is missing
        with pytest.raises(APIError) as exc_info:
            workflow_context.get_workflow()

        assert "Failed to parse workflow data" in str(exc_info.value)

    def test_get_workflow_with_invalid_data(
        self, workflow_context: WorkflowContext
    ) -> None:
        """get_workflow raises APIError when workflow data is invalid."""
        response_data = {"workflow": {"invalid": "data"}}  # Invalid workflow data

        workflow_context.http_client.get.return_value = response_data

        with pytest.raises(APIError) as exc_info:
            workflow_context.get_workflow()

        assert "Failed to parse workflow data" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, PydanticValidationError)

    def test_execute_workflow_success(self, workflow_context: WorkflowContext) -> None:
        """execute_workflow makes correct API call and returns response."""
        record_id = "rec123"
        execution_data = {"param1": "value1", "param2": "value2"}
        expected_response = {
            "status": "success",
            "execution_id": "exec456",
            "message": "Workflow executed successfully",
        }

        workflow_context.http_client.post.return_value = expected_response

        result = workflow_context.execute_workflow(record_id, **execution_data)

        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/test-app/"
            "workflow/test-workflow/rec123/execute"
        )
        expected_payload = {"data": execution_data}

        workflow_context.http_client.post.assert_called_once_with(
            expected_url, json=expected_payload
        )
        assert result == expected_response

    def test_execute_workflow_without_parameters(
        self, workflow_context: WorkflowContext
    ) -> None:
        """execute_workflow works without additional parameters."""
        record_id = "rec123"
        expected_response = {"status": "success"}

        workflow_context.http_client.post.return_value = expected_response

        result = workflow_context.execute_workflow(record_id)

        expected_payload = {"data": {}}
        workflow_context.http_client.post.assert_called_once_with(
            (
                "https://www.zohoapis.com/settings/test-owner/"
                "test-app/workflow/test-workflow/rec123/execute"
            ),
            json=expected_payload,
        )
        assert result == expected_response

    def test_execute_workflow_with_empty_parameters(
        self, workflow_context: WorkflowContext
    ) -> None:
        """execute_workflow handles empty parameters correctly."""
        record_id = "rec123"
        expected_response = {"status": "success"}

        workflow_context.http_client.post.return_value = expected_response

        result = workflow_context.execute_workflow(record_id, **{})

        expected_payload = {"data": {}}
        workflow_context.http_client.post.assert_called_once_with(
            (
                "https://www.zohoapis.com/settings/test-owner/"
                "test-app/workflow/test-workflow/rec123/execute"
            ),
            json=expected_payload,
        )
        assert result == expected_response

    def test_execute_workflow_with_complex_parameters(
        self, workflow_context: WorkflowContext
    ) -> None:
        """execute_workflow handles complex parameters correctly."""
        record_id = "rec123"
        complex_params = {
            "text_field": "Some text",
            "number_field": 42,
            "boolean_field": True,
            "list_field": ["item1", "item2"],
            "nested_object": {"key": "value"},
        }
        expected_response = {"status": "success"}

        workflow_context.http_client.post.return_value = expected_response

        result = workflow_context.execute_workflow(record_id, **complex_params)

        expected_payload = {"data": complex_params}
        workflow_context.http_client.post.assert_called_once_with(
            (
                "https://www.zohoapis.com/settings/test-owner/"
                "test-app/workflow/test-workflow/rec123/execute"
            ),
            json=expected_payload,
        )
        assert result == expected_response

    @pytest.mark.parametrize(
        "app_link_name,workflow_link_name,owner_name,expected_base_url",
        [
            (
                "app1",
                "workflow1",
                "owner1",
                "https://www.zohoapis.com/settings/owner1/app1/workflow/workflow1",
            ),
            (
                "my-app",
                "approval-workflow",
                "john-doe",
                (
                    "https://www.zohoapis.com/settings/"
                    "john-doe/my-app/workflow/approval-workflow"
                ),
            ),
            (
                "app_with_underscores",
                "workflow_with_underscores",
                "owner_with_underscores",
                (
                    "https://www.zohoapis.com/settings/owner_with_underscores/"
                    "app_with_underscores/workflow/workflow_with_underscores"
                ),
            ),
        ],
    )
    def test_url_construction(
        self,
        mock_http_client: Mock,
        app_link_name: str,
        workflow_link_name: str,
        owner_name: str,
        expected_base_url: str,
    ) -> None:
        """WorkflowContext constructs URLs correctly from various inputs."""
        workflow_context = WorkflowContext(
            http_client=mock_http_client,
            app_link_name=app_link_name,
            workflow_link_name=workflow_link_name,
            owner_name=owner_name,
        )

        # Test get_workflow URL
        from datetime import datetime

        workflow_data = {
            "id": "test-workflow",
            "name": "Test",
            "link_name": "test",
            "application_id": "test-app",
            "form_id": "test-form",
            "workflow_type": "conditional",
            "owner": "test-owner",
            "created_time": datetime.utcnow().isoformat(),
            "modified_time": datetime.utcnow().isoformat(),
            "triggers": [
                {
                    "id": "trigger-1",
                    "workflow_id": "test-workflow",
                    "trigger_type": "scheduled",
                    "name": "Manual Trigger",
                    "enabled": True,
                    "conditions": [],
                }
            ],
            "actions": [
                {
                    "id": "action-1",
                    "workflow_id": "test-workflow",
                    "action_type": "field_update",
                    "name": "Test Action",
                    "execution_order": 1,
                    "enabled": True,
                    "field_update_config": {"field_updates": {"status": "processed"}},
                }
            ],
        }
        workflow_context.http_client.get.return_value = {"workflow": workflow_data}
        workflow_context.get_workflow()

        workflow_context.http_client.get.assert_called_once_with(expected_base_url)

        # Test execute_workflow URL
        record_id = "rec123"
        expected_execute_url = f"{expected_base_url}/{record_id}/execute"
        workflow_context.http_client.post.return_value = {"status": "success"}
        workflow_context.execute_workflow(record_id)

        workflow_context.http_client.post.assert_called_once_with(
            expected_execute_url, json={"data": {}}
        )

    def test_get_workflow_api_error_handling(
        self, workflow_context: WorkflowContext
    ) -> None:
        """get_workflow handles API errors correctly."""
        workflow_context.http_client.get.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            workflow_context.get_workflow()

        assert "API Error" in str(exc_info.value)

    def test_execute_workflow_api_error_handling(
        self, workflow_context: WorkflowContext
    ) -> None:
        """execute_workflow handles API errors correctly."""
        workflow_context.http_client.post.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            workflow_context.execute_workflow("rec123")

        assert "API Error" in str(exc_info.value)

    @pytest.mark.parametrize(
        "record_id",
        [
            "rec123",
            "record-with-dashes",
            "record_with_underscores",
            "123456789",
            "a1b2c3d4e5f6",
        ],
    )
    def test_execute_workflow_with_various_record_ids(
        self, workflow_context: WorkflowContext, record_id: str
    ) -> None:
        """execute_workflow works with various record ID formats."""
        expected_response = {"status": "success"}
        workflow_context.http_client.post.return_value = expected_response

        result = workflow_context.execute_workflow(record_id)

        expected_url = (
            f"https://www.zohoapis.com/settings/test-owner/test-app/"
            f"workflow/test-workflow/{record_id}/execute"
        )
        workflow_context.http_client.post.assert_called_once_with(
            expected_url, json={"data": {}}
        )
        assert result == expected_response

    def test_workflow_context_methods_are_independent(
        self, workflow_context: WorkflowContext
    ) -> None:
        """get_workflow and execute_workflow methods work independently."""
        # Setup get_workflow response
        from datetime import datetime

        workflow_data = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "link_name": "test-workflow",
            "application_id": "test-app",
            "form_id": "test-form",
            "workflow_type": "conditional",
            "owner": "test-owner",
            "created_time": datetime.utcnow().isoformat(),
            "modified_time": datetime.utcnow().isoformat(),
            "triggers": [
                {
                    "id": "trigger-1",
                    "workflow_id": "test-workflow",
                    "trigger_type": "scheduled",
                    "name": "Scheduled Trigger",
                    "enabled": True,
                    "conditions": [],
                }
            ],
            "actions": [
                {
                    "id": "action-1",
                    "workflow_id": "test-workflow",
                    "action_type": "field_update",
                    "name": "Test Action",
                    "execution_order": 1,
                    "enabled": True,
                    "field_update_config": {"field_updates": {"status": "processed"}},
                }
            ],
        }
        workflow_context.http_client.get.return_value = {"workflow": workflow_data}

        # Setup execute_workflow response
        expected_response = {"status": "success"}
        workflow_context.http_client.post.return_value = expected_response

        # Call both methods
        workflow = workflow_context.get_workflow()
        execution_result = workflow_context.execute_workflow("rec123", param1="value1")

        # Verify both methods were called
        workflow_context.http_client.get.assert_called_once()
        workflow_context.http_client.post.assert_called_once()

        # Verify results
        assert isinstance(workflow, Workflow)
        assert execution_result == expected_response
