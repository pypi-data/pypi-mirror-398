"""Unit tests for workflow models."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError
from pydantic_core import ValidationError as CoreValidationError

from zoho_creator_sdk.models.enums import (
    ActionType,
    TriggerType,
    WorkflowStatus,
    WorkflowType,
)
from zoho_creator_sdk.models.workflows import (
    EmailActionConfig,
    TriggerCondition,
    Workflow,
    WorkflowAction,
    WorkflowExecution,
    WorkflowTrigger,
)


def _trigger(trigger_type: TriggerType, **kwargs):
    base = {
        "id": "t1",
        "workflow_id": "wf",
        "trigger_type": trigger_type,
        "active": True,
    }
    base.update(kwargs)
    return WorkflowTrigger(**base)


def _action(action_type: ActionType, order: int = 1, **kwargs) -> WorkflowAction:
    base = {
        "id": f"a{order}",
        "workflow_id": "wf",
        "action_type": action_type,
        "name": "Action",
        "execution_order": order,
        "active": True,
    }
    base.update(kwargs)
    return WorkflowAction(**base)


def test_trigger_validations() -> None:
    condition = TriggerCondition(field_name="Status", operator="equals", value="New")

    with pytest.raises(ValueError):
        _trigger(TriggerType.CONDITIONAL, conditions=[])

    with pytest.raises(ValueError):
        _trigger(TriggerType.SCHEDULED, schedule_expression=None)

    with pytest.raises(ValueError):
        _trigger(TriggerType.WEBHOOK, webhook_url=None)

    trig = _trigger(TriggerType.CONDITIONAL, conditions=[condition])
    assert trig.conditions[0].field_name == "Status"


def test_trigger_valid_scheduled_and_webhook() -> None:
    condition = TriggerCondition(field_name="Status", operator="equals", value="New")

    scheduled = _trigger(
        TriggerType.SCHEDULED,
        schedule_expression="0 0 * * *",
        conditions=[condition],
    )
    assert scheduled.schedule_expression == "0 0 * * *"

    webhook = _trigger(TriggerType.WEBHOOK, webhook_url="https://example.com/hook")
    assert webhook.webhook_url == "https://example.com/hook"


def test_action_configuration_validation() -> None:
    with pytest.raises(ValueError):
        _action(ActionType.EMAIL_NOTIFICATION)

    with pytest.raises(ValueError):
        _action(ActionType.FIELD_UPDATE)

    with pytest.raises(ValueError):
        _action(ActionType.WEBHOOK_CALL)

    email_action = _action(
        ActionType.EMAIL_NOTIFICATION,
        email_config=EmailActionConfig(
            recipients=["a@example.com"], subject="Hi", body="Body"
        ),
    )
    assert email_action.email_config.subject == "Hi"


def test_workflow_validations_and_helpers() -> None:
    trigger = _trigger(
        TriggerType.CONDITIONAL,
        conditions=[
            TriggerCondition(field_name="Status", operator="equals", value="New")
        ],
    )
    action = _action(
        ActionType.EMAIL_NOTIFICATION,
        email_config=EmailActionConfig(
            recipients=["a@example.com"], subject="Hi", body="Body"
        ),
    )

    workflow = Workflow(
        id="wf",
        name="Notify",
        link_name="notify",
        application_id="app",
        form_id="form",
        workflow_type=WorkflowType.EMAIL,
        triggers=[trigger],
        actions=[action],
        owner="owner",
        created_time=datetime.utcnow(),
        modified_time=datetime.utcnow(),
        execution_count=10,
        success_count=8,
        failure_count=2,
    )

    assert workflow.get_active_triggers()[0].id == "t1"
    assert workflow.get_active_actions()[0].id == "a1"
    assert workflow.get_actions_by_type(ActionType.EMAIL_NOTIFICATION)
    assert workflow.get_success_rate() == 80.0

    with pytest.raises((ValueError, ValidationError, CoreValidationError)):
        Workflow(
            id="wf",
            name="Invalid",
            link_name="invalid",
            application_id="app",
            form_id="form",
            workflow_type=WorkflowType.EMAIL,
            owner="owner",
            created_time=datetime.utcnow(),
            modified_time=datetime.utcnow(),
        )


def test_workflow_action_and_trigger_validations() -> None:
    trigger = _trigger(
        TriggerType.CONDITIONAL,
        conditions=[
            TriggerCondition(field_name="Status", operator="equals", value="New")
        ],
    )
    action = _action(
        ActionType.EMAIL_NOTIFICATION,
        email_config=EmailActionConfig(
            recipients=["a@example.com"], subject="Hi", body="Body"
        ),
    )

    with pytest.raises((ValueError, ValidationError, CoreValidationError)):
        Workflow(
            id="wf",
            name="Invalid",
            link_name="invalid",
            application_id="app",
            form_id="form",
            workflow_type=WorkflowType.EMAIL,
            owner="owner",
            created_time=datetime.utcnow(),
            modified_time=datetime.utcnow(),
            triggers=[],
            actions=[action],
        )

    with pytest.raises((ValueError, ValidationError, CoreValidationError)):
        Workflow(
            id="wf",
            name="Invalid",
            link_name="invalid",
            application_id="app",
            form_id="form",
            workflow_type=WorkflowType.EMAIL,
            owner="owner",
            created_time=datetime.utcnow(),
            modified_time=datetime.utcnow(),
            triggers=[trigger],
            actions=[],
        )

    out_of_order = _action(
        ActionType.EMAIL_NOTIFICATION,
        email_config=EmailActionConfig(
            recipients=["a@example.com"], subject="Hi", body="Body"
        ),
        execution_order=3,
    )

    with pytest.raises((ValueError, ValidationError, CoreValidationError)):
        Workflow(
            id="wf",
            name="Invalid",
            link_name="invalid",
            application_id="app",
            form_id="form",
            workflow_type=WorkflowType.EMAIL,
            owner="owner",
            created_time=datetime.utcnow(),
            modified_time=datetime.utcnow(),
            triggers=[trigger],
            actions=[action, out_of_order],
        )

    duplicate_order = _action(
        ActionType.EMAIL_NOTIFICATION,
        email_config=EmailActionConfig(
            recipients=["a@example.com"], subject="Hi", body="Body"
        ),
        execution_order=1,
        id="a2",
    )

    with pytest.raises((ValueError, ValidationError, CoreValidationError)):
        Workflow(
            id="wf",
            name="Invalid",
            link_name="invalid",
            application_id="app",
            form_id="form",
            workflow_type=WorkflowType.EMAIL,
            owner="owner",
            created_time=datetime.utcnow(),
            modified_time=datetime.utcnow(),
            triggers=[trigger],
            actions=[action, duplicate_order],
        )

    class TruthyEmpty(list):
        def __bool__(self) -> bool:  # pragma: no cover - bool path ensures truthy
            return True

    with pytest.raises((ValueError, ValidationError, CoreValidationError)):
        Workflow(
            id="wf",
            name="Invalid",
            link_name="invalid",
            application_id="app",
            form_id="form",
            workflow_type=WorkflowType.EMAIL,
            owner="owner",
            created_time=datetime.utcnow(),
            modified_time=datetime.utcnow(),
            triggers=[trigger],
            actions=[action],
            approval_users=TruthyEmpty(),
        )


def test_workflow_helpers_with_empty_collections() -> None:
    trigger = _trigger(
        TriggerType.CONDITIONAL,
        conditions=[
            TriggerCondition(field_name="Status", operator="equals", value="New")
        ],
    )
    action = _action(
        ActionType.EMAIL_NOTIFICATION,
        email_config=EmailActionConfig(
            recipients=["a@example.com"], subject="Hi", body="Body"
        ),
    )

    workflow_actions_only = Workflow(
        id="wf-actions",
        name="With actions",
        link_name="with-actions",
        application_id="app",
        form_id="form",
        workflow_type=WorkflowType.EMAIL,
        actions=[action],
        owner="owner",
        created_time=datetime.utcnow(),
        modified_time=datetime.utcnow(),
    )

    assert workflow_actions_only.get_active_triggers() == []

    workflow_triggers_only = Workflow(
        id="wf-triggers",
        name="With triggers",
        link_name="with-triggers",
        application_id="app",
        form_id="form",
        workflow_type=WorkflowType.EMAIL,
        triggers=[trigger],
        owner="owner",
        created_time=datetime.utcnow(),
        modified_time=datetime.utcnow(),
    )

    assert workflow_triggers_only.get_active_actions() == []
    assert (
        workflow_triggers_only.get_actions_by_type(ActionType.EMAIL_NOTIFICATION) == []
    )
    assert workflow_triggers_only.get_success_rate() == 0.0


def test_workflow_execution_validations_and_methods() -> None:
    started = datetime.utcnow()
    completed = started + timedelta(seconds=5)

    execution = WorkflowExecution(
        id="exe",
        workflow_id="wf",
        status=WorkflowStatus.COMPLETED,
        triggered_by="user",
        trigger_type=TriggerType.CONDITIONAL,
        started_at=started,
        completed_at=completed,
        total_actions=2,
        completed_actions=2,
        failed_actions=0,
    )

    assert execution.duration_seconds == 5
    assert execution.is_completed() is True
    assert execution.is_successful() is True
    assert execution.is_failed() is False
    assert execution.is_running() is False
    assert execution.can_retry() is False
    assert execution.get_progress_percentage() == 100.0

    execution.add_execution_log_entry("info", "message", {"key": "value"})
    assert execution.execution_log and execution.execution_log[0]["level"] == "info"

    with pytest.raises(ValueError):
        WorkflowExecution(
            id="exe",
            workflow_id="wf",
            status=WorkflowStatus.FAILED,
            triggered_by="user",
            trigger_type=TriggerType.CONDITIONAL,
            started_at=started,
            total_actions=1,
            completed_actions=2,
            failed_actions=0,
        )

    retry_candidate = WorkflowExecution(
        id="exe2",
        workflow_id="wf",
        status=WorkflowStatus.FAILED,
        triggered_by="user",
        trigger_type=TriggerType.CONDITIONAL,
        started_at=started,
        completed_at=completed,
        total_actions=1,
        completed_actions=0,
        failed_actions=1,
        retry_count=0,
        max_retries=1,
    )
    assert retry_candidate.can_retry() is True


def test_workflow_execution_duration_mismatch_and_zero_progress() -> None:
    started = datetime.utcnow()
    completed = started + timedelta(seconds=5)

    with pytest.raises((ValueError, ValidationError)):
        WorkflowExecution(
            id="exe-mismatch",
            workflow_id="wf",
            status=WorkflowStatus.COMPLETED,
            triggered_by="user",
            trigger_type=TriggerType.CONDITIONAL,
            started_at=started,
            completed_at=completed,
            total_actions=1,
            completed_actions=1,
            failed_actions=0,
            duration_seconds=999,
        )

    zero_actions = WorkflowExecution(
        id="exe-zero",
        workflow_id="wf",
        status=WorkflowStatus.PENDING,
        triggered_by="user",
        trigger_type=TriggerType.CONDITIONAL,
        started_at=started,
        total_actions=0,
        completed_actions=0,
        failed_actions=0,
    )
    assert zero_actions.get_progress_percentage() == 0.0


def test_workflow_execution_validation_errors() -> None:
    started = datetime.utcnow()

    with pytest.raises((ValueError, ValidationError)):
        WorkflowExecution(
            id="exe",
            workflow_id="wf",
            status=WorkflowStatus.COMPLETED,
            triggered_by="user",
            trigger_type=TriggerType.CONDITIONAL,
            started_at=started,
            completed_at=None,
            total_actions=1,
            completed_actions=1,
            failed_actions=0,
        )

    with pytest.raises((ValueError, ValidationError)):
        WorkflowExecution(
            id="exe",
            workflow_id="wf",
            status=WorkflowStatus.IN_PROGRESS,
            triggered_by="user",
            trigger_type=TriggerType.CONDITIONAL,
            started_at=started,
            completed_at=started + timedelta(seconds=1),
            total_actions=1,
            completed_actions=0,
            failed_actions=0,
        )

    completed = started + timedelta(seconds=5)
    with pytest.raises((ValueError, ValidationError)):
        WorkflowExecution(
            id="exe",
            workflow_id="wf",
            status=WorkflowStatus.COMPLETED,
            triggered_by="user",
            trigger_type=TriggerType.CONDITIONAL,
            started_at=started,
            completed_at=completed,
            total_actions=1,
            completed_actions=2,
            failed_actions=0,
        )

    with pytest.raises((ValueError, ValidationError)):
        WorkflowExecution(
            id="exe",
            workflow_id="wf",
            status=WorkflowStatus.COMPLETED,
            triggered_by="user",
            trigger_type=TriggerType.CONDITIONAL,
            started_at=started,
            completed_at=completed,
            total_actions=1,
            completed_actions=0,
            failed_actions=2,
        )

    with pytest.raises((ValueError, ValidationError)):
        WorkflowExecution(
            id="exe",
            workflow_id="wf",
            status=WorkflowStatus.COMPLETED,
            triggered_by="user",
            trigger_type=TriggerType.CONDITIONAL,
            started_at=started,
            completed_at=completed,
            total_actions=1,
            completed_actions=1,
            failed_actions=0,
            approved_by="manager",
        )

    with pytest.raises((ValueError, ValidationError)):
        WorkflowExecution(
            id="exe",
            workflow_id="wf",
            status=WorkflowStatus.FAILED,
            triggered_by="user",
            trigger_type=TriggerType.CONDITIONAL,
            started_at=started,
            completed_at=completed,
            total_actions=1,
            completed_actions=0,
            failed_actions=1,
            cancelled_by="manager",
        )
