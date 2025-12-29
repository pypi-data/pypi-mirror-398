"""Unit tests for :class:`zoho_creator_sdk.client.AppContext`."""

from __future__ import annotations

from typing import Optional
from unittest.mock import Mock

import pytest

from zoho_creator_sdk.client import (
    AppContext,
    ConnectionContext,
    CustomActionContext,
    FormContext,
    PermissionContext,
    ReportContext,
    WorkflowContext,
)


class TestAppContext:
    """Test cases for AppContext class."""

    @pytest.fixture
    def mock_http_client(self) -> Mock:
        """Create a mock HTTP client."""
        client = Mock()
        client.config.base_url = "https://www.zohoapis.com"
        return client

    @pytest.fixture
    def app_context(self, mock_http_client: Mock) -> AppContext:
        """Create an AppContext instance for testing."""
        return AppContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            owner_name="test-owner",
            app_name="Test App",
        )

    def test_initialization_with_all_parameters(self, mock_http_client: Mock) -> None:
        """AppContext initializes correctly with all parameters."""
        app_context = AppContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            owner_name="test-owner",
            app_name="Test App",
        )

        assert app_context.http_client is mock_http_client
        assert app_context.app_link_name == "test-app"
        assert app_context.owner_name == "test-owner"

    def test_initialization_without_app_name(self, mock_http_client: Mock) -> None:
        """AppContext initializes correctly without app_name."""
        app_context = AppContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            owner_name="test-owner",
        )

        assert app_context.app_link_name == "test-app"
        assert app_context.owner_name == "test-owner"

    def test_initialization_with_empty_app_link_name(
        self, mock_http_client: Mock
    ) -> None:
        """AppContext uses app_name when app_link_name is empty."""
        app_context = AppContext(
            http_client=mock_http_client,
            app_link_name="",
            owner_name="test-owner",
            app_name="fallback-app",
        )

        assert app_context.app_link_name == "fallback-app"

    def test_initialization_with_none_values(self, mock_http_client: Mock) -> None:
        """AppContext handles None values correctly."""
        app_context = AppContext(
            http_client=mock_http_client,
            app_link_name=None,  # type: ignore[arg-type]
            owner_name="test-owner",
            app_name="fallback-app",
        )

        assert app_context.app_link_name == "fallback-app"

    def test_form_method_with_link_name(self, app_context: AppContext) -> None:
        """form method creates FormContext with link_name."""
        form_context = app_context.form("test-form")

        assert isinstance(form_context, FormContext)
        assert form_context.http_client is app_context.http_client
        assert form_context.app_link_name == app_context.app_link_name
        assert form_context.form_link_name == "test-form"
        assert form_context.owner_name == app_context.owner_name

    def test_form_method_with_name_parameter(self, app_context: AppContext) -> None:
        """form method creates FormContext with name parameter."""
        form_context = app_context.form(form_link_name="", form_name="test-form")

        assert isinstance(form_context, FormContext)
        assert form_context.form_link_name == "test-form"

    def test_form_method_with_both_parameters(self, app_context: AppContext) -> None:
        """form method prefers link_name over name parameter."""
        form_context = app_context.form("link-name", "form-name")

        assert form_context.form_link_name == "link-name"

    def test_form_method_raises_error_with_empty_parameters(
        self, app_context: AppContext
    ) -> None:
        """form method raises ValueError when both parameters are empty."""
        with pytest.raises(ValueError) as exc_info:
            app_context.form("", "")

        assert "Either form_link_name or form_name must be provided" in str(
            exc_info.value
        )

    def test_form_method_raises_error_with_none_parameters(
        self, app_context: AppContext
    ) -> None:
        """form method raises ValueError when both parameters are None."""
        with pytest.raises(ValueError) as exc_info:
            app_context.form(None, None)  # type: ignore[arg-type]

        assert "Either form_link_name or form_name must be provided" in str(
            exc_info.value
        )

    def test_report_method_with_link_name(self, app_context: AppContext) -> None:
        """report method creates ReportContext with link_name."""
        report_context = app_context.report("test-report")

        assert isinstance(report_context, ReportContext)
        assert report_context.http_client is app_context.http_client
        assert report_context.app_link_name == app_context.app_link_name
        assert report_context.report_link_name == "test-report"
        assert report_context.owner_name == app_context.owner_name

    def test_report_method_with_name_parameter(self, app_context: AppContext) -> None:
        """report method creates ReportContext with name parameter."""
        report_context = app_context.report(
            report_link_name="", report_name="test-report"
        )

        assert isinstance(report_context, ReportContext)
        assert report_context.report_link_name == "test-report"

    def test_report_method_with_both_parameters(self, app_context: AppContext) -> None:
        """report method prefers link_name over name parameter."""
        report_context = app_context.report("link-name", "report-name")

        assert report_context.report_link_name == "link-name"

    def test_report_method_raises_error_with_empty_parameters(
        self, app_context: AppContext
    ) -> None:
        """report method raises ValueError when both parameters are empty."""
        with pytest.raises(ValueError) as exc_info:
            app_context.report("", "")

        assert "Either report_link_name or report_name must be provided" in str(
            exc_info.value
        )

    def test_workflow_method_with_link_name(self, app_context: AppContext) -> None:
        """workflow method creates WorkflowContext with link_name."""
        workflow_context = app_context.workflow("test-workflow")

        assert isinstance(workflow_context, WorkflowContext)
        assert workflow_context.http_client is app_context.http_client
        assert workflow_context.app_link_name == app_context.app_link_name
        assert workflow_context.workflow_link_name == "test-workflow"
        assert workflow_context.owner_name == app_context.owner_name

    def test_workflow_method_with_name_parameter(self, app_context: AppContext) -> None:
        """workflow method creates WorkflowContext with name parameter."""
        workflow_context = app_context.workflow(
            workflow_link_name="", workflow_name="test-workflow"
        )

        assert isinstance(workflow_context, WorkflowContext)
        assert workflow_context.workflow_link_name == "test-workflow"

    def test_workflow_method_with_both_parameters(
        self, app_context: AppContext
    ) -> None:
        """workflow method prefers link_name over name parameter."""
        workflow_context = app_context.workflow("link-name", "workflow-name")

        assert workflow_context.workflow_link_name == "link-name"

    def test_workflow_method_raises_error_with_empty_parameters(
        self, app_context: AppContext
    ) -> None:
        """workflow method raises ValueError when both parameters are empty."""
        with pytest.raises(ValueError) as exc_info:
            app_context.workflow("", "")

        assert "Either workflow_link_name or workflow_name must be provided" in str(
            exc_info.value
        )

    def test_permission_method(self, app_context: AppContext) -> None:
        """permission method creates PermissionContext."""
        permission_context = app_context.permission("perm-123")

        assert isinstance(permission_context, PermissionContext)
        assert permission_context.http_client is app_context.http_client
        assert permission_context.app_link_name == app_context.app_link_name
        assert permission_context.permission_id == "perm-123"
        assert permission_context.owner_name == app_context.owner_name

    def test_connection_method(self, app_context: AppContext) -> None:
        """connection method creates ConnectionContext."""
        connection_context = app_context.connection("conn-123")

        assert isinstance(connection_context, ConnectionContext)
        assert connection_context.http_client is app_context.http_client
        assert connection_context.app_link_name == app_context.app_link_name
        assert connection_context.connection_id == "conn-123"
        assert connection_context.owner_name == app_context.owner_name

    def test_custom_action_method_with_link_name(self, app_context: AppContext) -> None:
        """custom_action method creates CustomActionContext with link_name."""
        custom_action_context = app_context.custom_action("test-action")

        assert isinstance(custom_action_context, CustomActionContext)
        assert custom_action_context.http_client is app_context.http_client
        assert custom_action_context.app_link_name == app_context.app_link_name
        assert custom_action_context.custom_action_link_name == "test-action"
        assert custom_action_context.owner_name == app_context.owner_name

    def test_custom_action_method_with_name_parameter(
        self, app_context: AppContext
    ) -> None:
        """custom_action method creates CustomActionContext with name parameter."""
        custom_action_context = app_context.custom_action(
            custom_action_link_name="", custom_action_name="test-action"
        )

        assert isinstance(custom_action_context, CustomActionContext)
        assert custom_action_context.custom_action_link_name == "test-action"

    def test_custom_action_method_with_both_parameters(
        self, app_context: AppContext
    ) -> None:
        """custom_action method prefers link_name over name parameter."""
        custom_action_context = app_context.custom_action("link-name", "action-name")

        assert custom_action_context.custom_action_link_name == "link-name"

    def test_custom_action_method_raises_error_with_empty_parameters(
        self, app_context: AppContext
    ) -> None:
        """custom_action method raises ValueError when both parameters are empty."""
        with pytest.raises(ValueError) as exc_info:
            app_context.custom_action("", "")

        assert (
            "Either custom_action_link_name or custom_action_name must be provided"
            in str(exc_info.value)
        )

    @pytest.mark.parametrize(
        "app_link_name,owner_name,app_name,expected_link_name",
        [
            ("app1", "owner1", None, "app1"),
            ("", "owner1", "app2", "app2"),
            (None, "owner1", "app3", "app3"),  # type: ignore[arg-type]
            ("app4", "owner1", "fallback", "app4"),
        ],
    )
    def test_app_link_name_resolution(
        self,
        mock_http_client: Mock,
        app_link_name: str,
        owner_name: str,
        app_name: Optional[str],
        expected_link_name: str,
    ) -> None:
        """AppContext resolves app_link_name correctly from various inputs."""
        app_context = AppContext(
            http_client=mock_http_client,
            app_link_name=app_link_name,
            owner_name=owner_name,
            app_name=app_name,
        )

        assert app_context.app_link_name == expected_link_name
