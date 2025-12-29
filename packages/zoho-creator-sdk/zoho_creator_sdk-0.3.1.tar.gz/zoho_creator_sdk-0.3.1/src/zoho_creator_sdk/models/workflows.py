"""
Pydantic models for workflows in the Zoho Creator SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Mapping, Optional, Sequence

from pydantic import Field, ValidationInfo, field_validator, model_validator

from .base import CreatorBaseModel
from .enums import ActionType, TriggerType, WorkflowStatus, WorkflowType


class TriggerCondition(CreatorBaseModel):
    """Represents a condition for workflow triggers."""

    field_name: str = Field(description="The name of the field to evaluate.")
    operator: str = Field(
        description="The comparison operator (equals, not_equals, greater_than, "
        "less_than, contains, etc.)."
    )
    value: Any = Field(description="The value to compare against.")
    logical_operator: Optional[str] = Field(
        default="AND",
        description="Logical operator for combining multiple conditions (AND, OR).",
    )


class WorkflowTrigger(CreatorBaseModel):
    """Represents trigger conditions for a workflow."""

    id: str = Field(description="The unique identifier of the workflow trigger.")
    workflow_id: str = Field(
        description="The ID of the workflow this trigger belongs to."
    )
    trigger_type: TriggerType = Field(description="The type of trigger event.")
    conditions: Optional[Sequence[TriggerCondition]] = Field(
        default=None,
        description="List of conditions that must be met for the trigger to fire.",
    )
    schedule_expression: Optional[str] = Field(
        default=None, description="Cron expression for scheduled triggers."
    )
    webhook_url: Optional[str] = Field(
        default=None, description="Webhook URL for webhook triggers."
    )
    field_dependencies: Optional[Sequence[str]] = Field(
        default=None,
        description="List of fields that trigger the workflow when changed.",
    )
    active: bool = Field(
        default=True, description="Whether the trigger is currently active."
    )
    created_time: Optional[datetime] = Field(
        default=None, description="The time the trigger was created."
    )
    modified_time: Optional[datetime] = Field(
        default=None, description="The time the trigger was last modified."
    )

    @field_validator("conditions")
    @classmethod
    def validate_conditions_for_conditional_trigger(
        cls, v: Optional[Sequence[TriggerCondition]], info: ValidationInfo
    ) -> Optional[Sequence[TriggerCondition]]:
        """Validate that conditional triggers have conditions."""
        trigger_type = info.data.get("trigger_type")
        if trigger_type == TriggerType.CONDITIONAL and (not v or len(v) == 0):
            raise ValueError("Conditional triggers must have at least one condition")
        return v

    @field_validator("schedule_expression")
    @classmethod
    def validate_schedule_expression_for_scheduled_trigger(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        """Validate that scheduled triggers have a schedule expression."""
        trigger_type = info.data.get("trigger_type")
        if trigger_type == TriggerType.SCHEDULED and not v:
            raise ValueError("Scheduled triggers must have a schedule expression")
        return v

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url_for_webhook_trigger(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        """Validate that webhook triggers have a webhook URL."""
        trigger_type = info.data.get("trigger_type")
        if trigger_type == TriggerType.WEBHOOK and not v:
            raise ValueError("Webhook triggers must have a webhook URL")
        return v


class EmailActionConfig(CreatorBaseModel):
    """Configuration for email notification actions."""

    recipients: Sequence[str] = Field(description="List of email recipients.")
    subject: str = Field(description="Email subject template.")
    body: str = Field(description="Email body template.")
    cc: Optional[Sequence[str]] = Field(default=None, description="CC recipients.")
    bcc: Optional[Sequence[str]] = Field(default=None, description="BCC recipients.")
    attachments: Optional[Sequence[str]] = Field(
        default=None, description="File attachment paths or URLs."
    )


class FieldUpdateActionConfig(CreatorBaseModel):
    """Configuration for field update actions."""

    field_updates: Mapping[str, Any] = Field(
        description="Dictionary of field names to new values."
    )
    update_condition: Optional[str] = Field(
        default=None, description="Condition for when to apply the update."
    )


class WebhookActionConfig(CreatorBaseModel):
    """Configuration for webhook call actions."""

    url: str = Field(description="Webhook URL to call.")
    method: str = Field(
        default="POST", description="HTTP method (GET, POST, PUT, etc.)."
    )
    headers: Optional[Mapping[str, str]] = Field(
        default=None, description="HTTP headers to include."
    )
    payload: Optional[Mapping[str, Any]] = Field(
        default=None, description="Request payload data."
    )
    authentication: Optional[Mapping[str, str]] = Field(
        default=None, description="Authentication credentials."
    )


class WorkflowAction(CreatorBaseModel):
    """Represents an action within a workflow."""

    id: str = Field(description="The unique identifier of the workflow action.")
    workflow_id: str = Field(
        description="The ID of the workflow this action belongs to."
    )
    action_type: ActionType = Field(description="The type of action to perform.")
    name: str = Field(description="Display name for the action.")
    description: Optional[str] = Field(
        default=None, description="Description of what this action does."
    )
    execution_order: int = Field(
        ge=1, description="Order in which this action should be executed."
    )
    active: bool = Field(default=True, description="Whether this action is active.")
    config: Optional[Mapping[str, Any]] = Field(
        default=None, description="Action-specific configuration."
    )
    # Specific configuration models for type safety
    email_config: Optional[EmailActionConfig] = Field(
        default=None, description="Configuration for email actions."
    )
    field_update_config: Optional[FieldUpdateActionConfig] = Field(
        default=None, description="Configuration for field update actions."
    )
    webhook_config: Optional[WebhookActionConfig] = Field(
        default=None, description="Configuration for webhook actions."
    )
    delay_seconds: Optional[int] = Field(
        default=None, ge=0, description="Delay in seconds before executing this action."
    )
    retry_count: int = Field(
        default=0, ge=0, description="Number of times to retry this action on failure."
    )
    retry_delay: int = Field(
        default=60, ge=1, description="Delay in seconds between retries."
    )
    timeout_seconds: Optional[int] = Field(
        default=None, ge=1, description="Maximum time to wait for action completion."
    )
    created_time: Optional[datetime] = Field(
        default=None, description="The time the action was created."
    )
    modified_time: Optional[datetime] = Field(
        default=None, description="The time the action was last modified."
    )

    @model_validator(mode="after")
    def validate_action_config(self) -> "WorkflowAction":
        """Validate that the action has appropriate configuration for its type."""
        action_type = self.action_type

        if action_type == ActionType.EMAIL_NOTIFICATION and not self.email_config:
            raise ValueError("Email actions must have email configuration")
        if action_type == ActionType.FIELD_UPDATE and not self.field_update_config:
            raise ValueError(
                "Field update actions must have field update configuration"
            )
        if action_type == ActionType.WEBHOOK_CALL and not self.webhook_config:
            raise ValueError("Webhook actions must have webhook configuration")

        return self


class Workflow(CreatorBaseModel):
    """Represents a workflow for automating business processes."""

    id: str = Field(description="The unique identifier of the workflow.")
    name: str = Field(description="The display name of the workflow.")
    link_name: str = Field(description="The link name of the workflow (URL-friendly).")
    description: Optional[str] = Field(
        default=None, description="Detailed description of the workflow purpose."
    )
    application_id: str = Field(
        description="The ID of the application this workflow belongs to."
    )
    form_id: str = Field(
        description="The ID of the form this workflow is associated with."
    )
    workflow_type: WorkflowType = Field(description="The type of workflow.")
    version: int = Field(default=1, ge=1, description="Version number of the workflow.")
    active: bool = Field(
        default=True, description="Whether the workflow is currently active."
    )
    triggers: Optional[Sequence[WorkflowTrigger]] = Field(
        default=None, description="List of triggers that activate this workflow."
    )
    actions: Optional[Sequence[WorkflowAction]] = Field(
        default=None, description="List of actions to execute when the workflow runs."
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Priority level (1-10, higher number = higher priority).",
    )
    execution_timeout: Optional[int] = Field(
        default=None, ge=1, description="Maximum execution time in seconds."
    )
    max_executions_per_day: Optional[int] = Field(
        default=None, ge=1, description="Maximum number of executions per day."
    )
    tags: Optional[Sequence[str]] = Field(
        default=None, description="Tags for categorizing and searching workflows."
    )
    owner: str = Field(description="The owner/creator of the workflow.")
    created_time: datetime = Field(description="The time the workflow was created.")
    modified_time: datetime = Field(
        description="The time the workflow was last modified."
    )
    last_executed_time: Optional[datetime] = Field(
        default=None, description="The time the workflow was last executed."
    )
    execution_count: int = Field(
        default=0,
        ge=0,
        description="Total number of times the workflow has been executed.",
    )
    success_count: int = Field(
        default=0, ge=0, description="Number of successful executions."
    )
    failure_count: int = Field(
        default=0, ge=0, description="Number of failed executions."
    )
    is_system_workflow: bool = Field(
        default=False, description="Whether this is a system-generated workflow."
    )
    requires_approval: bool = Field(
        default=False, description="Whether this workflow requires manual approval."
    )
    approval_users: Optional[Sequence[str]] = Field(
        default=None, description="List of users who can approve this workflow."
    )

    @field_validator("actions")
    @classmethod
    def validate_actions_not_empty(
        cls, v: Optional[Sequence[WorkflowAction]]
    ) -> Optional[Sequence[WorkflowAction]]:
        """Validate that workflow has at least one action if actions are provided."""
        if v is not None and len(v) == 0:
            raise ValueError(
                "Workflow must have at least one action if actions are specified"
            )
        return v

    @field_validator("actions")
    @classmethod
    def validate_action_execution_order(
        cls, v: Optional[Sequence[WorkflowAction]]
    ) -> Optional[Sequence[WorkflowAction]]:
        """Validate that action execution orders are unique and sequential."""
        if v is not None:
            orders = [action.execution_order for action in v]
            if len(orders) != len(set(orders)):
                raise ValueError("All actions must have unique execution orders")
            if sorted(orders) != list(range(1, len(orders) + 1)):
                raise ValueError(
                    "Action execution orders must be sequential starting from 1"
                )
        return v

    @field_validator("triggers")
    @classmethod
    def validate_triggers_not_empty(
        cls, v: Optional[Sequence[WorkflowTrigger]]
    ) -> Optional[Sequence[WorkflowTrigger]]:
        """Validate that workflow has at least one trigger if triggers are provided."""
        if v is not None and len(v) == 0:
            raise ValueError(
                "Workflow must have at least one trigger if triggers are specified"
            )
        return v

    @model_validator(mode="after")
    def validate_workflow_configuration(self) -> "Workflow":
        """Validate the overall workflow configuration."""
        # Ensure workflow has either triggers or actions
        if (not self.triggers or len(self.triggers) == 0) and (
            not self.actions or len(self.actions) == 0
        ):
            raise ValueError("Workflow must have at least one trigger or action")

        # Validate approval configuration
        if self.approval_users and len(self.approval_users) == 0:
            raise ValueError("Approval users list cannot be empty if provided")

        return self

    def get_active_triggers(self) -> Sequence[WorkflowTrigger]:
        """Get all active triggers for this workflow."""
        if not self.triggers:
            return []
        return [trigger for trigger in self.triggers if trigger.active]

    def get_active_actions(self) -> Sequence[WorkflowAction]:
        """Get all active actions for this workflow."""
        if not self.actions:
            return []
        return [action for action in self.actions if action.active]

    def get_actions_by_type(self, action_type: ActionType) -> Sequence[WorkflowAction]:
        """Get all actions of a specific type."""
        if not self.actions:
            return []
        return [action for action in self.actions if action.action_type == action_type]

    def get_success_rate(self) -> float:
        """Calculate the success rate of workflow executions."""
        total_executions = self.execution_count
        if total_executions == 0:
            return 0.0
        return (self.success_count / total_executions) * 100.0


class WorkflowExecution(CreatorBaseModel):
    """Represents an execution instance of a workflow."""

    id: str = Field(description="The unique identifier of the workflow execution.")
    workflow_id: str = Field(description="The ID of the workflow being executed.")
    record_id: Optional[str] = Field(
        default=None, description="The ID of the record that triggered this execution."
    )
    status: WorkflowStatus = Field(description="The current status of the execution.")
    triggered_by: str = Field(
        description="The user or system that triggered the execution."
    )
    trigger_type: TriggerType = Field(
        description="The type of trigger that started this execution."
    )
    started_at: datetime = Field(description="The time when execution started.")
    completed_at: Optional[datetime] = Field(
        default=None, description="The time when execution completed."
    )
    duration_seconds: Optional[int] = Field(
        default=None, ge=0, description="Total execution time in seconds."
    )
    current_action_index: int = Field(
        default=0, ge=0, description="Index of the currently executing action."
    )
    total_actions: int = Field(
        default=0, ge=0, description="Total number of actions in this workflow."
    )
    completed_actions: int = Field(
        default=0, ge=0, description="Number of completed actions."
    )
    failed_actions: int = Field(
        default=0, ge=0, description="Number of failed actions."
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if execution failed."
    )
    error_details: Optional[Mapping[str, Any]] = Field(
        default=None, description="Detailed error information."
    )
    retry_count: int = Field(
        default=0, ge=0, description="Number of retries attempted."
    )
    max_retries: int = Field(
        default=3, ge=0, description="Maximum number of retries allowed."
    )
    input_data: Optional[Mapping[str, Any]] = Field(
        default=None, description="Input data passed to the workflow execution."
    )
    output_data: Optional[Mapping[str, Any]] = Field(
        default=None, description="Output data from the workflow execution."
    )
    execution_context: Optional[Mapping[str, Any]] = Field(
        default=None, description="Additional context information for the execution."
    )
    parent_execution_id: Optional[str] = Field(
        default=None, description="ID of parent execution if this is a sub-workflow."
    )
    child_execution_ids: Optional[Sequence[str]] = Field(
        default=None,
        description="IDs of child executions if this workflow spawned others.",
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Execution priority (inherited from workflow).",
    )
    scheduled_for: Optional[datetime] = Field(
        default=None, description="Scheduled execution time for delayed workflows."
    )
    approval_status: Optional[str] = Field(
        default=None, description="Approval status if workflow requires approval."
    )
    approved_by: Optional[str] = Field(
        default=None, description="User who approved the workflow execution."
    )
    approved_at: Optional[datetime] = Field(
        default=None, description="Time when workflow was approved."
    )
    paused_at: Optional[datetime] = Field(
        default=None, description="Time when execution was paused."
    )
    resumed_at: Optional[datetime] = Field(
        default=None, description="Time when execution was resumed."
    )
    cancelled_by: Optional[str] = Field(
        default=None, description="User who cancelled the execution."
    )
    cancelled_at: Optional[datetime] = Field(
        default=None, description="Time when execution was cancelled."
    )
    execution_log: Optional[List[Mapping[str, Any]]] = Field(
        default=None, description="Detailed execution log with timestamps."
    )

    @field_validator("completed_actions")
    @classmethod
    def validate_completed_actions(cls, v: int, info: ValidationInfo) -> int:
        """Validate that completed actions don't exceed total actions."""
        total_actions = info.data.get("total_actions", 0)
        if v > total_actions:
            raise ValueError("Completed actions cannot exceed total actions")
        return v

    @field_validator("failed_actions")
    @classmethod
    def validate_failed_actions(cls, v: int, info: ValidationInfo) -> int:
        """Validate that failed actions don't exceed total actions."""
        total_actions = info.data.get("total_actions", 0)
        if v > total_actions:
            raise ValueError("Failed actions cannot exceed total actions")
        return v

    @model_validator(mode="after")
    def validate_execution_timestamps(self) -> "WorkflowExecution":
        """Validate execution timestamp consistency."""
        # If execution is completed, completed_at should be set
        if self.status in [
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        ]:
            if not self.completed_at:
                raise ValueError(
                    "Completed executions must have completed_at timestamp"
                )

        # If execution is in progress, completed_at should not be set
        if self.status == WorkflowStatus.IN_PROGRESS and self.completed_at:
            raise ValueError(
                "In-progress executions cannot have completed_at timestamp"
            )

        # Duration should be calculable if both start and completion times are available
        if self.started_at and self.completed_at:
            duration = int((self.completed_at - self.started_at).total_seconds())
            if self.duration_seconds is None:
                self.duration_seconds = duration
            elif abs(self.duration_seconds - duration) > 1:  # Allow 1 second tolerance
                raise ValueError("Duration_seconds doesn't match calculated duration")

        return self

    @model_validator(mode="after")
    def validate_approval_workflow(self) -> "WorkflowExecution":
        """Validate approval-related fields."""
        if self.approved_by and not self.approved_at:
            raise ValueError("Approved executions must have approved_at timestamp")

        if self.cancelled_by and not self.cancelled_at:
            raise ValueError("Cancelled executions must have cancelled_at timestamp")

        return self

    def is_completed(self) -> bool:
        """Check if the execution is completed (successfully or not)."""
        return self.status in [
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        ]

    def is_successful(self) -> bool:
        """Check if the execution completed successfully."""
        return self.status == WorkflowStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if the execution failed."""
        return self.status == WorkflowStatus.FAILED

    def is_running(self) -> bool:
        """Check if the execution is currently running."""
        return self.status == WorkflowStatus.IN_PROGRESS

    def can_retry(self) -> bool:
        """Check if the execution can be retried."""
        return (
            self.status in [WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]
            and self.retry_count < self.max_retries
        )

    def get_progress_percentage(self) -> float:
        """Calculate execution progress as a percentage."""
        if self.total_actions == 0:
            return 0.0
        return (self.completed_actions / self.total_actions) * 100.0

    def add_execution_log_entry(
        self, level: str, message: str, details: Optional[Mapping[str, Any]] = None
    ) -> None:
        """Add an entry to the execution log."""
        if not self.execution_log:
            self.execution_log = []

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "details": details or {},
        }
        self.execution_log.append(log_entry)
