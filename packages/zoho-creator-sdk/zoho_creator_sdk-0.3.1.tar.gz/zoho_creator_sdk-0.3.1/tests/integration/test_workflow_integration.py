"""Integration tests for workflow functionality.

These tests verify the SDK's workflow execution capabilities
and interaction with the Zoho Creator workflow engine.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import httpx
import pytest

from zoho_creator_sdk import WorkflowContext, ZohoCreatorClient
from zoho_creator_sdk.models import APIConfig, AuthConfig, Workflow


class TestWorkflowIntegration:
    """Test cases for workflow integration."""

    @pytest.fixture
    def mock_api_config(self) -> APIConfig:
        """Create a mock API configuration."""
        return APIConfig(dc="US", environment="testing")

    @pytest.fixture
    def mock_auth_config(self) -> AuthConfig:
        """Create a mock authentication configuration."""
        return AuthConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            refresh_token="test_refresh_token",
        )

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
            return client

    @pytest.fixture
    def workflow_context(self, client: ZohoCreatorClient) -> WorkflowContext:
        """Create a WorkflowContext instance."""
        return WorkflowContext(
            http_client=client.http_client,
            app_link_name="test_app",
            workflow_link_name="test_workflow",
            owner_name="test_owner",
        )

    def test_workflow_definition_retrieval(
        self, workflow_context: WorkflowContext
    ) -> None:
        """Test retrieving workflow definition from API."""
        workflow_data = {
            "workflow": {
                "id": "workflow123",
                "name": "Approval Workflow",
                "link_name": "approval_workflow",
                "application_id": "app123",
                "form_id": "form123",
                "workflow_type": "approval",
                "owner": "test_owner",
                "created_time": datetime.utcnow().isoformat(),
                "modified_time": datetime.utcnow().isoformat(),
                "triggers": [
                    {
                        "id": "trigger123",
                        "workflow_id": "workflow123",
                        "trigger_type": "form_submitted",
                        "name": "Form Submission Trigger",
                        "enabled": True,
                        "conditions": [],
                    }
                ],
                "actions": [
                    {
                        "id": "action123",
                        "workflow_id": "workflow123",
                        "action_type": "email_notification",
                        "name": "Email Notification Action",
                        "execution_order": 1,
                        "enabled": True,
                        "email_config": {
                            "recipients": ["manager@example.com"],
                            "subject": "Approval Required",
                            "body": "Please review this submission",
                        },
                    }
                ],
            }
        }

        workflow_context.http_client.get.return_value = workflow_data

        result = workflow_context.get_workflow()

        assert isinstance(result, Workflow)
        assert result.name == "Approval Workflow"
        assert result.workflow_type.value == "approval"
        assert len(result.triggers) == 1
        assert len(result.actions) == 1

        # Verify API endpoint was called with correct path structure
        workflow_context.http_client.get.assert_called_once()
        actual_call = workflow_context.http_client.get.call_args[0][0]
        assert "/settings/test_owner/test_app/workflow/test_workflow" in actual_call

    def test_workflow_execution_with_record_data(
        self, workflow_context: WorkflowContext
    ) -> None:
        """Test workflow execution with record data."""
        record_id = "rec123456"
        execution_data = {
            "comments": "Please review this submission",
            "priority": "high",
        }

        expected_response = {
            "status": "success",
            "execution_id": "exec789",
            "message": "Workflow executed successfully",
            "result": {
                "status": "completed",
                "actions_executed": ["email_notification"],
                "next_action": "approval",
            },
        }

        workflow_context.http_client.post.return_value = expected_response

        result = workflow_context.execute_workflow(record_id, **execution_data)

        assert result == expected_response

        # Verify API endpoint was called with correct path structure and payload
        workflow_context.http_client.post.assert_called_once()
        actual_call = workflow_context.http_client.post.call_args
        actual_url = actual_call[0][0]
        actual_payload = actual_call[1]["json"]

        assert (
            "/settings/test_owner/test_app/workflow/test_workflow/rec123456/execute"
            in actual_url
        )
        assert actual_payload == {"data": execution_data}

    def test_workflow_execution_without_parameters(
        self, workflow_context: WorkflowContext
    ) -> None:
        """Test workflow execution without additional parameters."""
        record_id = "rec123456"
        expected_response = {
            "status": "success",
            "execution_id": "exec789",
            "message": "Workflow executed with default parameters",
        }

        workflow_context.http_client.post.return_value = expected_response

        result = workflow_context.execute_workflow(record_id)

        assert result == expected_response

        # Verify API endpoint was called with correct path structure and payload
        workflow_context.http_client.post.assert_called_once()
        actual_call = workflow_context.http_client.post.call_args
        actual_url = actual_call[0][0]
        actual_payload = actual_call[1]["json"]

        assert (
            "/settings/test_owner/test_app/workflow/test_workflow/rec123456/execute"
            in actual_url
        )
        assert actual_payload == {"data": {}}

    def test_complex_workflow_execution(
        self, workflow_context: WorkflowContext
    ) -> None:
        """Test workflow execution with complex data structures."""
        record_id = "rec123456"
        complex_data = {
            "user_data": {
                "name": "John Doe",
                "email": "john@example.com",
                "department": "Sales",
            },
            "approval_chain": ["manager", "director", "vp"],
            "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "attachments": ["doc1.pdf", "doc2.xlsx"],
            "metadata": {
                "source": "web_form",
                "priority": "urgent",
                "auto_approve": False,
            },
        }

        expected_response = {
            "status": "success",
            "execution_id": "exec789",
            "message": "Complex workflow executed successfully",
            "steps_completed": [
                "validation",
                "email_notifications",
                "approval_requests",
            ],
        }

        workflow_context.http_client.post.return_value = expected_response

        result = workflow_context.execute_workflow(record_id, **complex_data)

        assert result == expected_response

        # Verify API endpoint was called with correct path structure and payload
        workflow_context.http_client.post.assert_called_once()
        actual_call = workflow_context.http_client.post.call_args
        actual_url = actual_call[0][0]
        actual_payload = actual_call[1]["json"]

        assert (
            "/settings/test_owner/test_app/workflow/test_workflow/rec123456/execute"
            in actual_url
        )
        assert actual_payload == {"data": complex_data}

    def test_workflow_execution_with_special_characters(
        self, workflow_context: WorkflowContext
    ) -> None:
        """Test workflow execution with special characters and unicode."""
        record_id = "rec123456"
        special_data = {
            "title": "Document résumé with ñ and ß characters",
            "description": (
                "This contains special chars: " "@#$%^&*()_+-={}[]|\\:;\"'<>?,./"
            ),
            "unicode_text": "🚀 Emoji test 中文 العربية русский",
            "json_nested": {
                "array_data": ["item1", "item2", "item with spaces"],
                "boolean_value": True,
                "null_value": None,
                "number_value": 3.14159,
            },
        }

        expected_response = {
            "status": "success",
            "execution_id": "exec789",
            "message": ("Special characters handled successfully"),
        }

        workflow_context.http_client.post.return_value = expected_response

        result = workflow_context.execute_workflow(record_id, **special_data)

        assert result == expected_response

    def test_workflow_error_handling(self, workflow_context: WorkflowContext) -> None:
        """Test workflow execution error handling."""
        record_id = "nonexistent_record"
        error_response = {
            "error": "Record not found",
            "message": "The specified record does not exist",
            "code": 404,
        }

        workflow_context.http_client.post.return_value = error_response

        result = workflow_context.execute_workflow(record_id)

        assert result == error_response

    def test_workflow_api_error_handling(
        self, workflow_context: WorkflowContext
    ) -> None:
        """Test API error handling during workflow operations."""
        record_id = "rec123456"

        # Simulate API error
        workflow_context.http_client.post.side_effect = Exception(
            "API connection failed"
        )

        with pytest.raises(Exception):
            workflow_context.execute_workflow(record_id)

    def test_workflow_timeout_handling(self, workflow_context: WorkflowContext) -> None:
        """Test workflow execution timeout handling."""
        record_id = "rec123456"

        # Simulate timeout
        workflow_context.http_client.post.side_effect = httpx.TimeoutException(
            "Request timed out"
        )

        with pytest.raises(Exception):
            workflow_context.execute_workflow(record_id)

    @pytest.mark.parametrize(
        "record_id",
        [
            "simple_id",
            "record-with-dashes",
            "record_with_underscores",
            "1234567890",
            "a1b2c3d4e5f6g7h8i9j0",
            "UPPERCASE_RECORD_ID",
        ],
    )
    def test_workflow_execution_with_various_record_ids(
        self, workflow_context: WorkflowContext, record_id: str
    ) -> None:
        """Test workflow execution with various record ID formats."""
        expected_response = {"status": "success"}
        workflow_context.http_client.post.return_value = expected_response

        result = workflow_context.execute_workflow(record_id)

        assert result == expected_response

        # Verify API endpoint was called with correct path structure and payload
        workflow_context.http_client.post.assert_called_once()
        actual_call = workflow_context.http_client.post.call_args
        actual_url = actual_call[0][0]
        actual_payload = actual_call[1]["json"]

        assert (
            f"/settings/test_owner/test_app/workflow/test_workflow/{record_id}/execute"
            in actual_url
        )
        assert actual_payload == {"data": {}}

    def test_workflow_execution_with_empty_payload(
        self, workflow_context: WorkflowContext
    ) -> None:
        """Test workflow execution with completely empty payload."""
        record_id = "rec123456"
        expected_response = {"status": "success"}
        workflow_context.http_client.post.return_value = expected_response

        result = workflow_context.execute_workflow(record_id)

        assert result == expected_response

        # Verify API endpoint was called with correct path structure and payload
        workflow_context.http_client.post.assert_called_once()
        actual_call = workflow_context.http_client.post.call_args
        actual_url = actual_call[0][0]
        actual_payload = actual_call[1]["json"]

        assert (
            "/settings/test_owner/test_app/workflow/test_workflow/rec123456/execute"
            in actual_url
        )
        assert actual_payload == {"data": {}}

    def test_workflow_execution_with_large_payload(
        self, workflow_context: WorkflowContext
    ) -> None:
        """Test workflow execution with large payload data."""
        record_id = "rec123456"

        # Create large data payload
        large_data = {
            "large_text": "x" * 10000,  # 10KB of text
            "large_array": list(range(1000)),  # Array of 1000 numbers
            "nested_objects": {f"key_{i}": f"value_{i}" for i in range(100)},
        }

        expected_response = {"status": "success"}
        workflow_context.http_client.post.return_value = expected_response

        result = workflow_context.execute_workflow(record_id, **large_data)

        assert result == expected_response

    def test_workflow_execution_with_file_references(
        self, workflow_context: WorkflowContext
    ) -> None:
        """Test workflow execution with file reference data."""
        record_id = "rec123456"
        file_data = {
            "attachment_ids": ["file_123", "file_456", "file_789"],
            "document_paths": [
                "/documents/contracts/contract_001.pdf",
                "/documents/invoices/invoice_001.pdf",
            ],
            "image_urls": [
                "https://example.com/images/logo.png",
                "https://example.com/images/banner.jpg",
            ],
        }

        expected_response = {"status": "success"}
        workflow_context.http_client.post.return_value = expected_response

        result = workflow_context.execute_workflow(record_id, **file_data)

        assert result == expected_response


class TestWorkflowContextIndependence:
    """Test that WorkflowContext methods work independently."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock HTTP client."""
        client = Mock()
        client.config.base_url = "https://www.zohoapis.com"
        return client

    @pytest.fixture
    def workflow_context(self, mock_client: Mock) -> WorkflowContext:
        """Create a WorkflowContext instance."""
        return WorkflowContext(
            http_client=mock_client,
            app_link_name="test_app",
            workflow_link_name="test_workflow",
            owner_name="test_owner",
        )

    def test_independent_get_workflow_and_execute_workflow(
        self, workflow_context: WorkflowContext
    ) -> None:
        """Test that get_workflow and execute_workflow work independently."""

        # Setup get_workflow response
        workflow_data = {
            "workflow": {
                "id": "workflow123",
                "name": "Test Workflow",
                "link_name": "test_workflow",
                "application_id": "test_app",
                "form_id": "test_form",
                "workflow_type": "conditional",
                "owner": "test_owner",
                "created_time": datetime.utcnow().isoformat(),
                "modified_time": datetime.utcnow().isoformat(),
                "triggers": [
                    {
                        "id": "trigger123",
                        "workflow_id": "workflow123",
                        "trigger_type": "manual",
                        "name": "Manual Trigger",
                        "enabled": True,
                        "conditions": [],
                    }
                ],
                "actions": [
                    {
                        "id": "action123",
                        "workflow_id": "workflow123",
                        "action_type": "field_update",
                        "name": "Update Field Action",
                        "execution_order": 1,
                        "enabled": True,
                        "field_update_config": {
                            "field_updates": {"status": "processed"}
                        },
                    }
                ],
            }
        }

        # Setup execute_workflow response
        execution_response = {
            "status": "success",
            "execution_id": "exec456",
            "message": "Workflow executed successfully",
        }

        workflow_context.http_client.get.return_value = workflow_data
        workflow_context.http_client.post.return_value = execution_response

        # Call both methods
        workflow = workflow_context.get_workflow()
        execution_result = workflow_context.execute_workflow("rec123", param1="value1")

        # Verify both methods were called
        workflow_context.http_client.get.assert_called_once()
        workflow_context.http_client.post.assert_called_once()

        # Verify results
        assert isinstance(workflow, Workflow)
        assert execution_result == execution_response

    def test_workflow_context_with_different_parameters(
        self, workflow_context: WorkflowContext
    ) -> None:
        """Test WorkflowContext with different app/workflow/owner combinations."""
        test_cases = [
            {
                "app_link_name": "app1",
                "workflow_link_name": "workflow1",
                "owner_name": "owner1",
                "expected_base_url": (
                    "https://www.zohoapis.com/settings/owner1/app1/"
                    "workflow/workflow1"
                ),
            },
            {
                "app_link_name": "my-app",
                "workflow_link_name": "approval-workflow",
                "owner_name": "john-doe",
                "expected_base_url": (
                    "https://www.zohoapis.com/settings/john-doe/my-app/"
                    "workflow/approval-workflow"
                ),
            },
            {
                "app_link_name": "app_with_underscores",
                "workflow_link_name": "workflow_with_underscores",
                "owner_name": "owner_with_underscores",
                "expected_base_url": (
                    "https://www.zohoapis.com/settings/owner_with_underscores/"
                    "app_with_underscores/workflow/workflow_with_underscores"
                ),
            },
        ]

        for test_case in test_cases:
            context = WorkflowContext(
                http_client=workflow_context.http_client,
                app_link_name=test_case["app_link_name"],
                workflow_link_name=test_case["workflow_link_name"],
                owner_name=test_case["owner_name"],
            )

            # Test get_workflow URL construction

            workflow_data = {
                "workflow": {
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
                            "trigger_type": "manual",
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
                            "field_update_config": {
                                "field_updates": {"status": "processed"}
                            },
                        }
                    ],
                }
            }

            context.http_client.get.return_value = workflow_data
            context.get_workflow()
            context.http_client.get.assert_called_once_with(
                test_case["expected_base_url"]
            )

            # Test execute_workflow URL construction
            record_id = "rec123"
            context.http_client.post.return_value = {"status": "success"}
            context.execute_workflow(record_id)

            expected_execute_url = (
                f"{test_case['expected_base_url']}/{record_id}/execute"
            )
            context.http_client.post.assert_called_once_with(
                expected_execute_url, json={"data": {}}
            )

            # Reset mock for next iteration
            context.http_client.reset_mock()
