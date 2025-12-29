"""
Enum definitions for the Zoho Creator SDK.
"""

from enum import Enum


class ImportFormat(Enum):
    """Enumeration of supported import formats for bulk operations."""

    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
    XLS = "xls"
    TSV = "tsv"
    XML = "xml"
    YAML = "yaml"


class ImportMode(Enum):
    """Enumeration of import behaviors for bulk operations."""

    CREATE = "create"
    UPDATE = "update"
    UPSERT = "upsert"
    DELETE = "delete"
    VALIDATE = "validate"


class ExportFormat(Enum):
    """Enumeration of supported export formats for bulk operations."""

    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
    XLS = "xls"
    PDF = "pdf"
    TSV = "tsv"
    XML = "xml"
    YAML = "yaml"


class BulkOperationStatus(Enum):
    """Enumeration of bulk operation statuses."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class BulkOperationType(Enum):
    """Enumeration of bulk operation types."""

    IMPORT = "import"
    EXPORT = "export"
    DELETE = "delete"
    UPDATE = "update"


class ResponseStatus(Enum):
    """Enumeration of API response statuses."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    PARTIAL_SUCCESS = "partial_success"
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND = "not_found"
    RATE_LIMITED = "rate_limited"
    SERVER_ERROR = "server_error"
    SERVICE_UNAVAILABLE = "service_unavailable"


class ReportType(Enum):
    """Enumeration of Zoho Creator report types."""

    LIST = "list"
    SUMMARY = "summary"
    CALENDAR = "calendar"
    KANBAN = "kanban"
    PIVOT = "pivot"
    CHART = "chart"
    MAP = "map"
    TIMELINE = "timeline"


class WorkflowType(Enum):
    """Enumeration of Zoho Creator workflow types."""

    APPROVAL = "approval"
    EMAIL = "email"
    FIELD_UPDATE = "field_update"
    WEBHOOK = "webhook"
    SMS = "sms"
    TASK = "task"
    RECORD_CREATION = "record_creation"
    CONDITIONAL = "conditional"
    SCHEDULED = "scheduled"
    INTEGRATION = "integration"


class WorkflowStatus(Enum):
    """Enumeration of Zoho Creator workflow execution statuses."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RETRY = "retry"


class TriggerType(Enum):
    """Enumeration of workflow trigger types."""

    RECORD_CREATED = "record_created"
    RECORD_UPDATED = "record_updated"
    RECORD_DELETED = "record_deleted"
    FIELD_CHANGED = "field_changed"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    WEBHOOK = "webhook"
    FORM_SUBMITTED = "form_submitted"
    TIME_BASED = "time_based"
    CONDITIONAL = "conditional"


class FieldType(Enum):
    """Enumeration of Zoho Creator field types."""

    TEXT = "text"
    NUMBER = "number"
    DECIMAL = "decimal"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    BOOLEAN = "boolean"
    DROPDOWN = "dropdown"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    MULTISELECT = "multiselect"
    TEXTAREA = "textarea"
    RICHTEXT = "richtext"
    FILEUPLOAD = "fileupload"
    IMAGE = "image"
    SIGNATURE = "signature"
    LOOKUP = "lookup"
    SUBFORM = "subform"
    FORMULA = "formula"
    AUTO_NUMBER = "auto_number"
    USER = "user"
    SECTION = "section"
    NAME = "name"
    ADDRESS = "address"
    DECISION_BOX = "decision_box"
    RATING = "rating"
    SLIDER = "slider"
    PREDICTION = "prediction"
    AUDIO = "audio"
    VIDEO = "video"
    GEO_LOCATION = "geo_location"


class PermissionType(Enum):
    """Enumeration of permission types for access control."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE = "create"
    UPDATE = "update"
    EXECUTE = "execute"
    ADMIN = "admin"
    SHARE = "share"
    EXPORT = "export"
    IMPORT = "import"
    VIEW = "view"
    EDIT = "edit"
    MANAGE = "manage"
    CONFIGURE = "configure"
    APPROVE = "approve"
    REJECT = "reject"
    ASSIGN = "assign"
    COMMENT = "comment"
    ATTACH = "attach"
    DOWNLOAD = "download"


class EntityType(Enum):
    """Enumeration of entity types that can have permissions."""

    APPLICATION = "application"
    FORM = "form"
    REPORT = "report"
    WORKFLOW = "workflow"
    RECORD = "record"
    FIELD = "field"
    USER = "user"
    ROLE = "role"
    DASHBOARD = "dashboard"
    PAGE = "page"
    SECTION = "section"
    VIEW = "view"
    FILTER = "filter"
    TEMPLATE = "template"
    CONNECTION = "connection"
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    NOTIFICATION = "notification"
    FILE = "file"
    FOLDER = "folder"


class ActionType(Enum):
    """Enumeration of workflow action types."""

    EMAIL_NOTIFICATION = "email_notification"
    FIELD_UPDATE = "field_update"
    RECORD_CREATION = "record_creation"
    WEBHOOK_CALL = "webhook_call"
    SMS_NOTIFICATION = "sms_notification"
    TASK_ASSIGNMENT = "task_assignment"
    APPROVAL_REQUEST = "approval_request"
    INTEGRATION_CALL = "integration_call"
    DELAY = "delay"
    CONDITION_BRANCH = "condition_branch"


class FieldConfig(Enum):
    """Valid values for the Get Records field_config parameter."""

    QUICK_VIEW = "quick_view"
    DETAIL_VIEW = "detail_view"
    CUSTOM = "custom"
    ALL = "all"
