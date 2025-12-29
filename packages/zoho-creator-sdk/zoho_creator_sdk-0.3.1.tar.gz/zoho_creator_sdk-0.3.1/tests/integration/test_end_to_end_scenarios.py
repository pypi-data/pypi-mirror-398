"""End-to-end tests for critical user journeys.

These tests verify complete application workflows that users would
actually perform when using the Zoho Creator SDK.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from zoho_creator_sdk.client import ZohoCreatorClient
from zoho_creator_sdk.exceptions import AuthenticationError, NetworkError


class TestEndToEndScenarios:
    """Test cases for end-to-end user workflows."""

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

    def test_complete_crud_workflow(self, client: ZohoCreatorClient) -> None:
        """Test complete Create-Read-Update-Delete workflow for records."""

        # Step 1: Get applications to find the target app
        mock_applications = {
            "applications": [
                {
                    "application_name": "Contact Management",
                    "link_name": "contact_management",
                    "creation_date": "2023-01-01",
                    "category": 1,
                    "date_format": "dd-MM-yyyy",
                    "time_zone": "America/New_York",
                    "created_by": "admin@example.com",
                    "workspace_name": "main_workspace",
                }
            ]
        }
        client.http_client.get.return_value = mock_applications

        applications = client.get_applications("test_owner")
        assert len(applications) == 1
        app = applications[0]

        # Step 2: Create a new record using form context
        form_context = client.form(app.link_name, "test_owner", "contacts")

        mock_create_response = {
            "data": {
                "ID": "12345",
                "Name": "John Doe",
                "Email": "john@example.com",
                "Phone": "+1-555-0123",
                "Created_Time": "2023-01-01T10:00:00Z",
            }
        }
        client.http_client.post.return_value = mock_create_response

        create_result = form_context.add_record(
            {"Name": "John Doe", "Email": "john@example.com", "Phone": "+1-555-0123"}
        )
        assert create_result["data"]["Name"] == "John Doe"

        # Step 3: Read the record back using report context
        report_context = client.report(app.link_name, "test_owner", "all_contacts")

        mock_read_response = {
            "data": [
                {
                    "ID": "12345",
                    "Name": "John Doe",
                    "Email": "john@example.com",
                    "Phone": "+1-555-0123",
                }
            ],
            "meta": {"more_records": False},
        }
        client.http_client.get.return_value = mock_read_response

        records = list(report_context.get_records())
        assert len(records) == 1
        assert records[0].ID == "12345"
        assert records[0].Name == "John Doe"

        # Step 4: Update the record
        mock_update_response = {
            "data": {
                "ID": "12345",
                "Name": "John Doe",
                "Email": "john.doe@company.com",  # Updated email
                "Phone": "+1-555-0123",
                "Modified_Time": "2023-01-01T11:00:00Z",
            }
        }
        client.http_client.patch.return_value = mock_update_response

        update_result = client.update_record(
            "test_owner",
            app.link_name,
            "all_contacts",
            "12345",
            data={"Email": "john.doe@company.com"},
        )
        assert update_result["data"]["Email"] == "john.doe@company.com"

        # Step 5: Delete the record
        mock_delete_response = {"message": "Record deleted successfully"}
        client.http_client.delete.return_value = mock_delete_response

        delete_result = client.delete_record(
            "test_owner", app.link_name, "all_contacts", "12345"
        )
        assert delete_result["message"] == "Record deleted successfully"

        # Verify all HTTP client calls were made correctly
        assert client.http_client.get.call_count >= 2  # applications + read records
        assert client.http_client.post.call_count >= 1  # create record
        assert client.http_client.patch.call_count >= 1  # update record
        assert client.http_client.delete.call_count >= 1  # delete record

    def test_workflow_automation_scenario(self, client: ZohoCreatorClient) -> None:
        """Test a complete workflow automation scenario."""

        # Setup: Get application and execute a workflow on a record
        mock_applications = {
            "applications": [
                {
                    "application_name": "Leave Management",
                    "link_name": "leave_management",
                    "creation_date": "2023-01-01",
                    "category": 1,
                    "date_format": "dd-MM-yyyy",
                    "time_zone": "America/New_York",
                    "created_by": "admin@example.com",
                    "workspace_name": "hr_workspace",
                }
            ]
        }
        client.http_client.get.return_value = mock_applications

        applications = client.get_applications("hr_admin")
        app = applications[0]

        # Step 1: Create a leave request record
        form_context = client.form(app.link_name, "hr_admin", "leave_requests")

        mock_create_response = {
            "data": {
                "ID": "req123",
                "Employee": "Jane Smith",
                "Leave_Type": "Annual",
                "Start_Date": "2023-06-01",
                "End_Date": "2023-06-05",
                "Status": "Pending",
                "Created_Time": "2023-05-25T09:00:00Z",
            }
        }
        client.http_client.post.return_value = mock_create_response

        leave_request = form_context.add_record(
            {
                "Employee": "Jane Smith",
                "Leave_Type": "Annual",
                "Start_Date": "2023-06-01",
                "End_Date": "2023-06-05",
                "Status": "Pending",
            }
        )
        assert leave_request["data"]["Status"] == "Pending"

        # Step 2: Execute approval workflow
        workflow_context = client.workflow(
            app.link_name, "hr_admin", "approval_workflow"
        )

        mock_workflow_execution = {
            "data": {
                "workflow_id": "approval_workflow",
                "execution_id": "exec456",
                "status": "success",
                "result": "approved",
                "approved_by": "manager@example.com",
                "approved_time": "2023-05-25T10:30:00Z",
            }
        }
        client.http_client.post.return_value = mock_workflow_execution

        workflow_result = workflow_context.execute_workflow(
            "req123",
            action="approve",
            comments="Approved for annual leave",
            approver="manager@example.com",
        )
        assert workflow_result["data"]["status"] == "success"
        assert workflow_result["data"]["result"] == "approved"

        # Step 3: Verify the record was updated through a report
        report_context = client.report(app.link_name, "hr_admin", "leave_status")

        mock_updated_record = {
            "data": [
                {
                    "ID": "req123",
                    "Employee": "Jane Smith",
                    "Leave_Type": "Annual",
                    "Start_Date": "2023-06-01",
                    "End_Date": "2023-06-05",
                    "Status": "Approved",  # Status updated by workflow
                    "Approved_By": "manager@example.com",
                    "Approved_Time": "2023-05-25T10:30:00Z",
                }
            ],
            "meta": {"more_records": False},
        }
        client.http_client.get.return_value = mock_updated_record

        records = list(report_context.get_records(Status="Approved"))
        assert len(records) == 1
        assert records[0].Status == "Approved"
        assert records[0].Approved_By == "manager@example.com"

    def test_permission_management_workflow(self, client: ZohoCreatorClient) -> None:
        """Test a complete permission management workflow."""

        # Step 1: Get all permissions for an application
        mock_permissions = {
            "permissions": [
                {
                    "id": "perm001",
                    "name": "Read Access",
                    "entity_type": "application",
                    "entity_id": "app123",
                    "permission_type": "read",
                    "granted_to_user_id": "user001",
                    "granted_by_user_id": "admin001",
                    "created_at": "2023-01-01T10:00:00Z",
                    "modified_at": "2023-01-01T10:00:00Z",
                }
            ]
        }
        client.http_client.get.return_value = mock_permissions

        permissions = client.get_permissions("admin", "project_management")
        assert len(permissions) == 1
        assert permissions[0].name == "Read Access"

        # Step 2: Create a new permission via permission context
        permission_context = client.permission("project_management", "admin", "perm002")

        mock_permission_data = {
            "permission": {
                "id": "perm002",
                "name": "Write Access",
                "entity_type": "form",
                "entity_id": "tasks_form",
                "permission_type": "write",
                "granted_to_user_id": "user002",
                "granted_by_user_id": "admin001",
                "created_at": "2023-01-02T10:00:00Z",
                "modified_at": "2023-01-02T10:00:00Z",
            }
        }
        client.http_client.get.return_value = mock_permission_data

        permission = permission_context.get_permission()
        assert permission.id == "perm002"
        assert permission.permission_type.value == "write"

        # Step 3: Update the permission
        mock_update_response = {
            "data": {
                "id": "perm002",
                "name": "Full Access",
                "entity_type": "form",
                "entity_id": "tasks_form",
                "permission_type": "admin",
                "granted_to_user_id": "user002",
                "granted_by_user_id": "admin001",
                "created_at": "2023-01-02T10:00:00Z",
                "modified_at": "2023-01-03T15:30:00Z",
            }
        }
        client.http_client.patch.return_value = mock_update_response

        update_result = permission_context.update_permission(
            {"name": "Full Access", "permission_type": "admin"}
        )
        assert update_result["data"]["name"] == "Full Access"

    def test_multi_user_collaboration_scenario(self, client: ZohoCreatorClient) -> None:
        """Test a multi-user collaboration scenario."""

        # Setup: Multiple users working on the same application
        app_name = "project_tracker"
        owner_name = "project_admin"

        # User 1: Creates a project record
        user1_form_context = client.form(app_name, owner_name, "projects")

        mock_project_create = {
            "data": {
                "ID": "proj001",
                "Project_Name": "Website Redesign",
                "Description": "Complete redesign of company website",
                "Status": "Planning",
                "Assigned_To": "designer@example.com",
                "Created_By": "manager@example.com",
                "Created_Time": "2023-01-01T09:00:00Z",
            }
        }
        client.http_client.post.return_value = mock_project_create

        project = user1_form_context.add_record(
            {
                "Project_Name": "Website Redesign",
                "Description": "Complete redesign of company website",
                "Status": "Planning",
                "Assigned_To": "designer@example.com",
            }
        )
        assert project["data"]["ID"] == "proj001"

        # User 2: Adds tasks to the project
        user2_form_context = client.form(app_name, owner_name, "tasks")

        mock_task_create = {
            "data": {
                "ID": "task001",
                "Project_ID": "proj001",
                "Task_Name": "Design Homepage",
                "Description": "Create mockups for the new homepage",
                "Status": "Not Started",
                "Assigned_To": "designer@example.com",
                "Due_Date": "2023-01-15",
                "Created_By": "designer@example.com",
                "Created_Time": "2023-01-01T10:30:00Z",
            }
        }
        client.http_client.post.return_value = mock_task_create

        task = user2_form_context.add_record(
            {
                "Project_ID": "proj001",
                "Task_Name": "Design Homepage",
                "Description": "Create mockups for the new homepage",
                "Status": "Not Started",
                "Assigned_To": "designer@example.com",
                "Due_Date": "2023-01-15",
            }
        )
        assert task["data"]["Project_ID"] == "proj001"

        # User 3: Updates the project status
        mock_project_update = {
            "data": {
                "ID": "proj001",
                "Project_Name": "Website Redesign",
                "Description": "Complete redesign of company website",
                "Status": "In Progress",  # Updated status
                "Assigned_To": "designer@example.com",
                "Created_By": "manager@example.com",
                "Modified_By": "developer@example.com",
                "Modified_Time": "2023-01-02T14:00:00Z",
            }
        }
        client.http_client.patch.return_value = mock_project_update

        update_result = client.update_record(
            owner_name, app_name, "projects", "proj001", data={"Status": "In Progress"}
        )
        assert update_result["data"]["Status"] == "In Progress"

        # Verify all users can see the updated project status
        report_context = client.report(app_name, owner_name, "project_status")

        mock_project_status = {
            "data": [
                {
                    "ID": "proj001",
                    "Project_Name": "Website Redesign",
                    "Status": "In Progress",
                    "Task_Count": 1,
                    "Last_Updated": "2023-01-02T14:00:00Z",
                }
            ],
            "meta": {"more_records": False},
        }
        client.http_client.get.return_value = mock_project_status

        projects = list(report_context.get_records())
        assert len(projects) == 1
        assert projects[0].Status == "In Progress"
        assert projects[0].Task_Count == 1

    def test_custom_action_integration(self, client: ZohoCreatorClient) -> None:
        """Test custom action integration in a workflow."""

        # Setup: Get application and trigger custom action
        mock_applications = {
            "applications": [
                {
                    "application_name": "Customer Support",
                    "link_name": "customer_support",
                    "creation_date": "2023-01-01",
                    "category": 1,
                    "date_format": "dd-MM-yyyy",
                    "time_zone": "America/New_York",
                    "created_by": "admin@example.com",
                    "workspace_name": "support_workspace",
                }
            ]
        }
        client.http_client.get.return_value = mock_applications

        applications = client.get_applications("support_manager")
        app = applications[0]

        # Step 1: Create a support ticket
        form_context = client.form(app.link_name, "support_manager", "tickets")

        mock_ticket_create = {
            "data": {
                "ID": "ticket123",
                "Customer_Email": "customer@example.com",
                "Subject": "Login Issue",
                "Description": "Cannot access account",
                "Priority": "High",
                "Status": "Open",
                "Created_Time": "2023-01-01T08:00:00Z",
            }
        }
        client.http_client.post.return_value = mock_ticket_create

        ticket = form_context.add_record(
            {
                "Customer_Email": "customer@example.com",
                "Subject": "Login Issue",
                "Description": "Cannot access account",
                "Priority": "High",
                "Status": "Open",
            }
        )
        assert ticket["data"]["Status"] == "Open"

        # Step 2: Execute custom action (send escalation notification)
        custom_action_context = client.custom_action(
            app.link_name, "support_manager", "escalate_ticket"
        )

        mock_escalation_result = {
            "data": {
                "action_id": "escalate_ticket",
                "execution_id": "exec789",
                "status": "success",
                "result": "escalated",
                "notified_manager": "manager@example.com",
                "escalation_time": "2023-01-01T08:15:00Z",
            }
        }
        client.http_client.post.return_value = mock_escalation_result

        escalation_result = custom_action_context.execute_custom_action(
            "ticket123", escalation_reason="High priority customer", notify_manager=True
        )
        assert escalation_result["data"]["status"] == "success"
        assert escalation_result["data"]["result"] == "escalated"

        # Step 3: Verify the ticket was updated
        report_context = client.report(
            app.link_name, "support_manager", "escalated_tickets"
        )

        mock_escalated_tickets = {
            "data": [
                {
                    "ID": "ticket123",
                    "Customer_Email": "customer@example.com",
                    "Subject": "Login Issue",
                    "Priority": "High",
                    "Status": "Escalated",
                    "Escalated_To": "manager@example.com",
                    "Escalation_Time": "2023-01-01T08:15:00Z",
                }
            ],
            "meta": {"more_records": False},
        }
        client.http_client.get.return_value = mock_escalated_tickets

        escalated_tickets = list(report_context.get_records(Priority="High"))
        assert len(escalated_tickets) == 1
        assert escalated_tickets[0].Status == "Escalated"
        assert escalated_tickets[0].Escalated_To == "manager@example.com"

    def test_connection_management_workflow(self, client: ZohoCreatorClient) -> None:
        """Test a complete connection management workflow."""

        # Setup: Get application and manage external connections
        app_name = "integration_hub"
        owner_name = "dev_admin"

        # Step 1: Create connection context
        connection_context = client.connection(app_name, owner_name, "slack_connection")

        # Step 2: Test the connection
        mock_test_result = {
            "status": "success",
            "message": "Connection to Slack is working",
            "connection_time": "2023-01-01T12:00:00Z",
            "response_time": "150ms",
        }
        client.http_client.get.return_value = mock_test_result

        test_result = connection_context.test_connection()
        assert test_result["status"] == "success"

        # Step 3: Get connection details
        mock_connection_details = {
            "connection": {
                "connection_id": "slack_connection",
                "connection_name": "Slack Integration",
                "connection_type": "webhook",
                "application_id": "integration_hub",
                "configuration": {
                    "url": "https://hooks.slack.com/services/...",
                    "webhook_secret": "secret123",
                },
                "is_active": True,
                "description": "Slack webhook integration for notifications",
            }
        }
        client.http_client.get.return_value = mock_connection_details

        connection = connection_context.get_connection()
        assert connection.id == "slack_connection"
        assert connection.is_active is True

    def test_error_handling_workflow(self, client: ZohoCreatorClient) -> None:
        """Test error handling in a complete workflow."""

        # Setup: Simulate authentication failure
        client.http_client.get.side_effect = AuthenticationError("Token expired")

        with pytest.raises(AuthenticationError):
            client.get_applications("test_user")

        # Reset and test network error
        client.http_client.get.side_effect = NetworkError("Connection refused")

        with pytest.raises(NetworkError):
            client.get_applications("test_user")

        # Reset for normal operation
        client.http_client.get.side_effect = None
        mock_applications = {"applications": []}
        client.http_client.get.return_value = mock_applications

        # Should work fine after error scenarios
        applications = client.get_applications("test_user")
        assert isinstance(applications, list)


class TestComplexDataScenarios:
    """Test complex data handling scenarios."""

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
            mock_config_manager.return_value.get_auth_config.return_value = Mock()
            mock_config_manager.return_value.get_api_config.return_value = Mock()
            mock_auth_handler = Mock()
            mock_get_auth_handler.return_value = mock_auth_handler
            mock_http_client = Mock()
            mock_http_client_class.return_value = mock_http_client

            client = ZohoCreatorClient()
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

    def test_bulk_data_operations(self, client: ZohoCreatorClient) -> None:
        """Test bulk data operations and pagination."""

        # Setup application
        mock_applications = {
            "applications": [
                {
                    "application_name": "Data Management",
                    "link_name": "data_management",
                    "creation_date": "2023-01-01",
                    "category": 1,
                    "date_format": "dd-MM-yyyy",
                    "time_zone": "America/New_York",
                    "created_by": "admin@example.com",
                    "workspace_name": "data_workspace",
                }
            ]
        }
        client.http_client.get.return_value = mock_applications

        applications = client.get_applications("data_admin")
        app = applications[0]

        # Test bulk data retrieval with pagination
        report_context = client.report(app.link_name, "data_admin", "large_dataset")

        # Mock paginated response
        mock_page_1 = {
            "data": [
                {"ID": f"record_{i}", "Name": f"Record {i}", "Value": i * 10}
                for i in range(1, 101)  # 100 records
            ],
            "meta": {"more_records": True, "next_page_token": "page_2_token"},
        }

        mock_page_2 = {
            "data": [
                {"ID": f"record_{i}", "Name": f"Record {i}", "Value": i * 10}
                for i in range(101, 151)  # 50 more records
            ],
            "meta": {"more_records": False},
        }

        # Setup sequential responses for pagination
        client.http_client.get.side_effect = [mock_page_1, mock_page_2]

        # Collect all records
        all_records = list(report_context.get_records())
        assert len(all_records) == 150
        assert all_records[0].ID == "record_1"
        assert all_records[-1].ID == "record_150"

    def test_special_characters_and_unicode(self, client: ZohoCreatorClient) -> None:
        """Test handling of special characters and unicode data."""

        mock_applications = {
            "applications": [
                {
                    "application_name": "International App",
                    "link_name": "international_app",
                    "creation_date": "2023-01-01",
                    "category": 1,
                    "date_format": "dd-MM-yyyy",
                    "time_zone": "America/New_York",
                    "created_by": "admin@example.com",
                    "workspace_name": "global_workspace",
                }
            ]
        }
        client.http_client.get.return_value = mock_applications

        applications = client.get_applications("global_admin")
        app = applications[0]

        # Create record with special characters
        form_context = client.form(app.link_name, "global_admin", "international_data")

        mock_create_response = {
            "data": {
                "ID": "unicode_123",
                "Name": "José María González",
                "Description": "产品描述 🌟 Special chars: @#$%^&*()",
                "Email": "user+test@example.co.uk",
                "Notes": "Café résumé naïve façade",
                "Created_Time": "2023-01-01T10:00:00Z",
            }
        }
        client.http_client.post.return_value = mock_create_response

        result = form_context.add_record(
            {
                "Name": "José María González",
                "Description": "产品描述 🌟 Special chars: @#$%^&*()",
                "Email": "user+test@example.co.uk",
                "Notes": "Café résumé naïve façade",
            }
        )

        assert result["data"]["Name"] == "José María González"
        assert "🌟" in result["data"]["Description"]

    def test_large_data_payloads(self, client: ZohoCreatorClient) -> None:
        """Test handling of large data payloads."""

        mock_applications = {
            "applications": [
                {
                    "application_name": "Content Management",
                    "link_name": "content_management",
                    "creation_date": "2023-01-01",
                    "category": 1,
                    "date_format": "dd-MM-yyyy",
                    "time_zone": "America/New_York",
                    "created_by": "admin@example.com",
                    "workspace_name": "content_workspace",
                }
            ]
        }
        client.http_client.get.return_value = mock_applications

        applications = client.get_applications("content_admin")
        app = applications[0]

        # Create record with large content
        form_context = client.form(app.link_name, "content_admin", "articles")

        large_content = "A" * 10000  # 10KB of text
        mock_create_response = {
            "data": {
                "ID": "large_content_123",
                "Title": "Large Article",
                "Content": large_content,
                "Word_Count": 1667,
                "Created_Time": "2023-01-01T10:00:00Z",
            }
        }
        client.http_client.post.return_value = mock_create_response

        result = form_context.add_record(
            {"Title": "Large Article", "Content": large_content}
        )

        assert result["data"]["Word_Count"] == 1667
        assert len(result["data"]["Content"]) == 10000

    def test_concurrent_operations_simulation(self, client: ZohoCreatorClient) -> None:
        """Test simulation of concurrent operations."""

        mock_applications = {
            "applications": [
                {
                    "application_name": "Task Management",
                    "link_name": "task_management",
                    "creation_date": "2023-01-01",
                    "category": 1,
                    "date_format": "dd-MM-yyyy",
                    "time_zone": "America/New_York",
                    "created_by": "admin@example.com",
                    "workspace_name": "task_workspace",
                }
            ]
        }
        client.http_client.get.return_value = mock_applications

        applications = client.get_applications("task_admin")
        app = applications[0]

        # Simulate multiple users creating tasks simultaneously
        form_context = client.form(app.link_name, "task_admin", "tasks")

        # Mock responses for multiple task creations
        task_responses = [
            {
                "data": {
                    "ID": f"task_{i}",
                    "Title": f"Task {i}",
                    "Assigned_To": f"user{i}@example.com",
                    "Created_Time": f"2023-01-01T{10+i:02d}:00:00Z",
                }
            }
            for i in range(1, 6)
        ]

        client.http_client.post.side_effect = task_responses

        # Create multiple tasks
        created_tasks = []
        for i in range(1, 6):
            task = form_context.add_record(
                {"Title": f"Task {i}", "Assigned_To": f"user{i}@example.com"}
            )
            created_tasks.append(task)

        assert len(created_tasks) == 5
        assert created_tasks[0]["data"]["Title"] == "Task 1"
        assert created_tasks[4]["data"]["Title"] == "Task 5"
