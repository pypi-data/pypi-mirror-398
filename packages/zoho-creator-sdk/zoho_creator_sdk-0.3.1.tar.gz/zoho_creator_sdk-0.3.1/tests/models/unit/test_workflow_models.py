"""Unit tests for workflow models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError as PydanticValidationError

from zoho_creator_sdk.models import (
    EmailActionConfig,
    FieldUpdateActionConfig,
    TriggerCondition,
    WebhookActionConfig,
    Workflow,
    WorkflowAction,
    WorkflowExecution,
    WorkflowTrigger,
)
from zoho_creator_sdk.models.enums import (
    ActionType,
    TriggerType,
    WorkflowStatus,
    WorkflowType,
)


class TestWorkflowTrigger:
    """Test cases for WorkflowTrigger."""

    def test_workflow_trigger_minimal_creation(self) -> None:
        """WorkflowTrigger can be created with minimal required fields."""
        trigger = WorkflowTrigger(
            id="trigger123",
            workflow_id="workflow456",
            trigger_type=TriggerType.RECORD_CREATED,
        )

        assert trigger.id == "trigger123"
        assert trigger.workflow_id == "workflow456"
        assert trigger.trigger_type == TriggerType.RECORD_CREATED

    def test_workflow_trigger_complete_creation(self) -> None:
        """WorkflowTrigger can be created with all fields."""
        condition = TriggerCondition(
            field_name="status", operator="equals", value="active"
        )

        trigger = WorkflowTrigger(
            id="trigger789",
            workflow_id="workflow456",
            trigger_type=TriggerType.RECORD_UPDATED,
            conditions=[condition],
        )

        assert trigger.id == "trigger789"
        assert trigger.workflow_id == "workflow456"
        assert trigger.trigger_type == TriggerType.RECORD_UPDATED
        assert len(trigger.conditions) == 1
        assert trigger.conditions[0].field_name == "status"

    def test_workflow_trigger_multiple_conditions(self) -> None:
        """WorkflowTrigger can have multiple trigger conditions."""
        condition1 = TriggerCondition(
            field_name="amount", operator="greater_than", value=1000
        )

        condition2 = TriggerCondition(
            field_name="category", operator="equals", value="urgent"
        )

        trigger = WorkflowTrigger(
            id="trigger-multi",
            workflow_id="workflow456",
            trigger_type=TriggerType.FIELD_CHANGED,
            conditions=[condition1, condition2],
        )

        assert len(trigger.conditions) == 2
        assert trigger.conditions[0].field_name == "amount"
        assert trigger.conditions[1].field_name == "category"

    def test_workflow_trigger_validation_error(self) -> None:
        """WorkflowTrigger raises validation error for invalid data."""
        with pytest.raises(PydanticValidationError):
            WorkflowTrigger(
                id="trigger123",
                workflow_id="workflow456",
                trigger_type="invalid_trigger_type",
            )

    def test_workflow_trigger_string_representation(self) -> None:
        """WorkflowTrigger string representation includes trigger type."""
        trigger = WorkflowTrigger(
            id="trigger123",
            workflow_id="workflow456",
            trigger_type=TriggerType.RECORD_CREATED,
        )

        trigger_str = str(trigger)
        assert "RECORD_CREATED" in trigger_str


class TestTriggerCondition:
    """Test cases for TriggerCondition."""

    def test_trigger_condition_minimal_creation(self) -> None:
        """TriggerCondition can be created with minimal required fields."""
        condition = TriggerCondition(
            field_name="amount", operator="greater_than", value=1000
        )

        assert condition.field_name == "amount"
        assert condition.operator == "greater_than"
        assert condition.value == 1000

    def test_trigger_condition_complete_creation(self) -> None:
        """TriggerCondition can be created with all fields."""
        condition = TriggerCondition(
            field_name="status",
            operator="in",
            value=["active", "pending", "review"],
            logic="AND",
        )

        assert condition.field_name == "status"
        assert condition.operator == "in"
        assert condition.value == ["active", "pending", "review"]
        assert condition.logical_operator == "AND"

    def test_trigger_condition_different_operators(self) -> None:
        """TriggerCondition supports different operators."""
        # Equals operator
        equals_condition = TriggerCondition(
            field_name="category", operator="equals", value="urgent"
        )
        assert equals_condition.operator == "equals"

        # Contains operator
        contains_condition = TriggerCondition(
            field_name="description", operator="contains", value="important"
        )
        assert contains_condition.operator == "contains"

        # Is null operator
        null_condition = TriggerCondition(
            field_name="assigned_to", operator="is_null", value=True
        )
        assert null_condition.value is True

    def test_trigger_condition_validation_error(self) -> None:
        """TriggerCondition raises validation error for missing fields."""
        with pytest.raises(PydanticValidationError):
            TriggerCondition(
                field_name="test"
                # Missing operator and value
            )


class TestWorkflowAction:
    """Test cases for WorkflowAction."""

    def test_workflow_action_minimal_creation(self) -> None:
        """WorkflowAction can be created with minimal required fields."""
        action = WorkflowAction(
            id="action123",
            workflow_id="workflow456",
            action_type=ActionType.RECORD_CREATION,
            name="Record Creation Action",
            execution_order=1,
        )

        assert action.action_type == ActionType.RECORD_CREATION

    def test_workflow_action_complete_creation(self) -> None:
        """WorkflowAction can be created with all fields."""
        email_config = EmailActionConfig(
            recipients=["user@example.com"],
            subject="Workflow Notification",
            body="This is an automated notification",
        )

        action = WorkflowAction(
            id="action123",
            workflow_id="workflow456",
            action_type=ActionType.EMAIL_NOTIFICATION,
            name="Email Action",
            execution_order=1,
            delay_seconds=5,
            email_config=email_config,
        )

        assert action.action_type == ActionType.EMAIL_NOTIFICATION
        assert action.email_config.recipients == ["user@example.com"]
        assert action.email_config.subject == "Workflow Notification"
        assert action.delay_seconds == 5
        assert action.execution_order == 1

    def test_workflow_action_field_update(self) -> None:
        """WorkflowAction can update fields."""
        field_config = FieldUpdateActionConfig(field_updates={"status": "approved"})

        action = WorkflowAction(
            id="action456",
            workflow_id="workflow456",
            action_type=ActionType.FIELD_UPDATE,
            name="Field Update Action",
            execution_order=2,
            field_update_config=field_config,
        )

        assert action.action_type == ActionType.FIELD_UPDATE
        assert action.field_update_config.field_updates["status"] == "approved"

    def test_workflow_action_webhook(self) -> None:
        """WorkflowAction can call webhooks."""
        webhook_config = WebhookActionConfig(
            url="https://api.example.com/webhook",
            method="POST",
            headers={"Authorization": "Bearer token"},
            payload={"event": "workflow_triggered"},
        )

        action = WorkflowAction(
            id="action789",
            workflow_id="workflow456",
            action_type=ActionType.WEBHOOK_CALL,
            name="Webhook Action",
            execution_order=3,
            webhook_config=webhook_config,
        )

        assert action.action_type == ActionType.WEBHOOK_CALL
        assert action.webhook_config.url == "https://api.example.com/webhook"
        assert action.webhook_config.method == "POST"

    def test_workflow_action_validation_error(self) -> None:
        """WorkflowAction raises validation error for invalid action type."""
        with pytest.raises(PydanticValidationError):
            WorkflowAction(
                id="invalid",
                workflow_id="workflow456",
                action_type="invalid_action_type",
                name="Invalid Action",
                execution_order=1,
            )


class TestEmailActionConfig:
    """Test cases for EmailActionConfig."""

    def test_email_action_config_minimal_creation(self) -> None:
        """EmailActionConfig can be created with minimal required fields."""
        config = EmailActionConfig(
            recipients=["recipient@example.com"],
            subject="Test Email",
            body="Test email body",
        )

        assert config.recipients == ["recipient@example.com"]
        assert config.subject == "Test Email"
        assert config.body == "Test email body"

    def test_email_action_config_complete_creation(self) -> None:
        """EmailActionConfig can be created with all fields."""
        config = EmailActionConfig(
            recipients=["user@example.com"],
            cc=["manager@example.com"],
            bcc=["admin@example.com"],
            subject="Important Notification",
            body="This is an important workflow notification",
            attachments=["report.pdf"],
        )

        assert config.recipients == ["user@example.com"]
        assert config.cc == ["manager@example.com"]
        assert config.bcc == ["admin@example.com"]
        assert config.subject == "Important Notification"
        assert config.body == "This is an important workflow notification"
        assert config.attachments == ["report.pdf"]

    def test_email_action_config_multiple_recipients(self) -> None:
        """EmailActionConfig supports multiple recipients."""
        config = EmailActionConfig(
            recipients=["user1@example.com", "user2@example.com"],
            subject="Group Notification",
            body="Group notification body",
        )

        assert "user1@example.com" in config.recipients
        assert "user2@example.com" in config.recipients

    def test_email_action_config_validation_error(self) -> None:
        """EmailActionConfig raises validation error for missing required fields."""
        with pytest.raises(PydanticValidationError):
            EmailActionConfig(
                # Missing required 'recipients' and 'body' fields
                subject="Test"
            )


class TestFieldUpdateActionConfig:
    """Test cases for FieldUpdateActionConfig."""

    def test_field_update_action_config_minimal_creation(self) -> None:
        """FieldUpdateActionConfig can be created with minimal required fields."""
        config = FieldUpdateActionConfig(field_updates={"status": "approved"})

        assert config.field_updates["status"] == "approved"

    def test_field_update_action_config_complete_creation(self) -> None:
        """FieldUpdateActionConfig can be created with all fields."""
        config = FieldUpdateActionConfig(
            field_updates={"priority": "high", "status": "active"},
            update_condition="status == 'pending'",
        )

        assert config.field_updates["priority"] == "high"
        assert config.field_updates["status"] == "active"
        assert config.update_condition == "status == 'pending'"

    def test_field_update_action_config_with_expression(self) -> None:
        """FieldUpdateActionConfig supports expressions."""
        config = FieldUpdateActionConfig(field_updates={"total": "quantity * price"})

        assert config.field_updates["total"] == "quantity * price"


class TestWebhookActionConfig:
    """Test cases for WebhookActionConfig."""

    def test_webhook_action_config_minimal_creation(self) -> None:
        """WebhookActionConfig can be created with minimal required fields."""
        config = WebhookActionConfig(url="https://api.example.com/webhook")

        assert config.url == "https://api.example.com/webhook"

    def test_webhook_action_config_complete_creation(self) -> None:
        """WebhookActionConfig can be created with all fields."""
        config = WebhookActionConfig(
            url="https://api.example.com/webhook",
            method="POST",
            headers={
                "Authorization": "Bearer token123",
                "Content-Type": "application/json",
            },
            payload={"event": "workflow_triggered", "data": "test"},
            authentication={"type": "bearer", "token": "secret"},
        )

        assert config.url == "https://api.example.com/webhook"
        assert config.method == "POST"
        assert config.headers["Authorization"] == "Bearer token123"
        assert config.payload["event"] == "workflow_triggered"
        assert config.authentication["type"] == "bearer"

    def test_webhook_action_config_different_methods(self) -> None:
        """WebhookActionConfig supports different HTTP methods."""
        get_config = WebhookActionConfig(
            url="https://api.example.com/get", method="GET"
        )

        put_config = WebhookActionConfig(
            url="https://api.example.com/put", method="PUT"
        )

        delete_config = WebhookActionConfig(
            url="https://api.example.com/delete", method="DELETE"
        )

        assert get_config.method == "GET"
        assert put_config.method == "PUT"
        assert delete_config.method == "DELETE"

    def test_webhook_action_config_validation_error(self) -> None:
        """WebhookActionConfig raises validation error for missing URL."""
        with pytest.raises(PydanticValidationError):
            WebhookActionConfig(
                method="POST"
                # Missing required 'url' field
            )


class TestWorkflowExecution:
    """Test cases for WorkflowExecution."""

    def test_workflow_execution_minimal_creation(self) -> None:
        """WorkflowExecution can be created with minimal required fields."""
        from datetime import datetime

        execution = WorkflowExecution(
            id="execution123",
            workflow_id="workflow123",
            status=WorkflowStatus.IN_PROGRESS,
            triggered_by="user@example.com",
            trigger_type=TriggerType.MANUAL,
            started_at=datetime.utcnow(),
        )

        assert execution.id == "execution123"
        assert execution.workflow_id == "workflow123"
        assert execution.status == WorkflowStatus.IN_PROGRESS
        assert execution.triggered_by == "user@example.com"
        assert execution.trigger_type == TriggerType.MANUAL

    def test_workflow_execution_complete_creation(self) -> None:
        """WorkflowExecution can be created with all fields."""
        from datetime import datetime, timedelta

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=60)

        execution = WorkflowExecution(
            id="execution789",
            workflow_id="workflow456",
            status=WorkflowStatus.COMPLETED,
            triggered_by="user123",
            trigger_type=TriggerType.MANUAL,
            started_at=start_time,
            completed_at=end_time,
            record_id="record456",
        )

        assert execution.id == "execution789"
        assert execution.workflow_id == "workflow456"
        assert execution.status == WorkflowStatus.COMPLETED
        assert execution.triggered_by == "user123"
        assert execution.record_id == "record456"
        assert execution.duration_seconds == 60

    def test_workflow_execution_failed_status(self) -> None:
        """WorkflowExecution can have failed status with errors."""
        from datetime import datetime, timedelta

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=30)

        execution = WorkflowExecution(
            id="execution_failed",
            workflow_id="workflow123",
            status=WorkflowStatus.FAILED,
            triggered_by="user@example.com",
            trigger_type=TriggerType.MANUAL,
            started_at=start_time,
            completed_at=end_time,
        )

        assert execution.status == WorkflowStatus.FAILED
        assert execution.duration_seconds == 30

    def test_workflow_execution_string_representation(self) -> None:
        """WorkflowExecution string representation includes workflow ID."""
        from datetime import datetime, timedelta

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=30)

        execution = WorkflowExecution(
            id="execution123",
            workflow_id="workflow123",
            status=WorkflowStatus.COMPLETED,
            triggered_by="user123",
            trigger_type=TriggerType.MANUAL,
            started_at=start_time,
            completed_at=end_time,
        )

        execution_str = str(execution)
        assert "workflow123" in execution_str


class TestWorkflow:
    """Test cases for Workflow."""

    def test_workflow_minimal_creation(self) -> None:
        """Workflow can be created with minimal required fields."""
        from datetime import datetime

        trigger = WorkflowTrigger(
            id="trigger123",
            workflow_id="workflow456",
            trigger_type=TriggerType.RECORD_CREATED,
        )
        action = WorkflowAction(
            id="action123",
            workflow_id="workflow456",
            action_type=ActionType.EMAIL_NOTIFICATION,
            name="Email Action",
            execution_order=1,
            email_config=EmailActionConfig(
                recipients=["test@example.com"],
                subject="Test Subject",
                body="Test Body",
            ),
        )

        workflow = Workflow(
            id="workflow123",
            name="Test Workflow",
            link_name="test_workflow",
            application_id="app123",
            form_id="form123",
            workflow_type=WorkflowType.CONDITIONAL,
            owner="test-owner",
            created_time=datetime.utcnow(),
            modified_time=datetime.utcnow(),
            triggers=[trigger],
            actions=[action],
        )

        assert workflow.name == "Test Workflow"
        assert workflow.link_name == "test_workflow"
        assert workflow.triggers[0].trigger_type == TriggerType.RECORD_CREATED
        assert len(workflow.actions) == 1

    def test_workflow_complete_creation(self) -> None:
        """Workflow can be created with all fields."""
        condition = TriggerCondition(
            field_name="amount", operator="greater_than", value=10000
        )

        trigger = WorkflowTrigger(
            id="trigger123",
            workflow_id="workflow456",
            trigger_type=TriggerType.RECORD_UPDATED,
            field_name="status",
            trigger_conditions=[condition],
        )

        email_config = EmailActionConfig(
            recipients=["manager@example.com"],
            subject="Large Amount Alert",
            body="A large amount has been recorded",
        )

        action = WorkflowAction(
            id="action123",
            workflow_id="workflow456",
            action_type=ActionType.EMAIL_NOTIFICATION,
            name="Email Action",
            execution_order=1,
            email_config=email_config,
        )

        now = datetime.now(timezone.utc)

        workflow = Workflow(
            id="workflow123",
            name="Amount Alert Workflow",
            link_name="amount_alert_workflow",
            application_id="app123",
            form_id="form123",
            description="Alerts for large amounts",
            triggers=[trigger],
            actions=[action],
            workflow_type=WorkflowType.CONDITIONAL,
            owner="test-owner",
            created_time=now,
            modified_time=now,
        )

        assert workflow.name == "Amount Alert Workflow"
        assert workflow.link_name == "amount_alert_workflow"
        assert workflow.description == "Alerts for large amounts"
        assert workflow.workflow_type == WorkflowType.CONDITIONAL

    def test_workflow_multiple_actions(self) -> None:
        """Workflow can have multiple actions."""
        from datetime import datetime

        email_action = WorkflowAction(
            id="action123",
            workflow_id="workflow456",
            action_type=ActionType.EMAIL_NOTIFICATION,
            name="Email Action",
            execution_order=1,
            email_config=EmailActionConfig(
                recipients=["test@example.com"],
                subject="Test Subject",
                body="Test Body",
            ),
        )
        update_action = WorkflowAction(
            id="action456",
            workflow_id="workflow456",
            action_type=ActionType.FIELD_UPDATE,
            name="Field Update Action",
            execution_order=2,
            delay_seconds=5,
            field_update_config=FieldUpdateActionConfig(
                field_updates={"status": "processed"}
            ),
        )

        workflow = Workflow(
            id="workflow123",
            name="Multi-Action Workflow",
            link_name="multi_action_workflow",
            application_id="app123",
            form_id="form123",
            workflow_type=WorkflowType.CONDITIONAL,
            owner="test-owner",
            created_time=datetime.utcnow(),
            modified_time=datetime.utcnow(),
            triggers=[
                WorkflowTrigger(
                    id="trigger123",
                    workflow_id="workflow456",
                    trigger_type=TriggerType.RECORD_CREATED,
                )
            ],
            actions=[email_action, update_action],
        )

        assert len(workflow.actions) == 2
        assert workflow.actions[0].action_type == ActionType.EMAIL_NOTIFICATION
        assert workflow.actions[1].action_type == ActionType.FIELD_UPDATE
        assert workflow.actions[1].delay_seconds == 5

    def test_workflow_validation_error_missing_trigger(self) -> None:
        """Workflow raises validation error for missing trigger."""
        with pytest.raises(PydanticValidationError):
            Workflow(
                display_name="Invalid Workflow",
                workflow_name="invalid_workflow",
                actions=[
                    WorkflowAction(
                        id="action123",
                        workflow_id="workflow456",
                        action_type=ActionType.EMAIL_NOTIFICATION,
                        name="Email Action",
                        execution_order=1,
                    )
                ],
                # Missing trigger
            )

    def test_workflow_validation_error_missing_actions(self) -> None:
        """Workflow raises validation error for missing actions."""
        with pytest.raises(PydanticValidationError):
            Workflow(
                display_name="Invalid Workflow",
                workflow_name="invalid_workflow",
                trigger=WorkflowTrigger(
                    id="trigger123",
                    workflow_id="workflow456",
                    trigger_type=TriggerType.RECORD_CREATED,
                ),
                # Missing actions
            )

    def test_workflow_string_representation(self) -> None:
        """Workflow string representation returns workflow name."""
        from datetime import datetime

        workflow = Workflow(
            id="workflow123",
            name="My Workflow",
            link_name="my_workflow",
            application_id="app123",
            form_id="form123",
            workflow_type=WorkflowType.CONDITIONAL,
            owner="test-owner",
            created_time=datetime.utcnow(),
            modified_time=datetime.utcnow(),
            triggers=[
                WorkflowTrigger(
                    id="trigger123",
                    workflow_id="workflow456",
                    trigger_type=TriggerType.RECORD_CREATED,
                )
            ],
            actions=[
                WorkflowAction(
                    id="action123",
                    workflow_id="workflow456",
                    action_type=ActionType.EMAIL_NOTIFICATION,
                    name="Email Action",
                    execution_order=1,
                    email_config=EmailActionConfig(
                        recipients=["test@example.com"],
                        subject="Test Subject",
                        body="Test Body",
                    ),
                )
            ],
        )

        assert "My Workflow" in str(workflow)
