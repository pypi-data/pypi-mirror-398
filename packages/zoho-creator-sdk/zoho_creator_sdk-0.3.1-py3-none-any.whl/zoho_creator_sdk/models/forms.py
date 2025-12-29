"""
Pydantic models for forms and fields in the Zoho Creator SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Sequence, Union

from pydantic import Field, ValidationInfo, field_validator, model_validator

from .base import CreatorBaseModel
from .enums import FieldType


class FieldValidation(CreatorBaseModel):
    """Represents validation rules and constraints for a form field."""

    min_length: Optional[int] = Field(
        default=None, ge=0, le=10000, description="Minimum length for text fields."
    )
    max_length: Optional[int] = Field(
        default=None, ge=1, le=10000, description="Maximum length for text fields."
    )
    min_value: Optional[Union[int, float]] = Field(
        default=None, description="Minimum value for numeric fields."
    )
    max_value: Optional[Union[int, float]] = Field(
        default=None, description="Maximum value for numeric fields."
    )
    pattern: Optional[str] = Field(
        default=None, max_length=1000, description="Regex pattern for text validation."
    )
    custom_validation: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Custom validation expression or rule.",
    )
    allow_duplicates: bool = Field(
        default=True, description="Whether duplicate values are allowed."
    )
    case_sensitive: bool = Field(
        default=True, description="Whether validation is case sensitive."
    )

    @model_validator(mode="after")
    def validate_length_constraints(self) -> "FieldValidation":
        """Validate that min_length is not greater than max_length."""
        if (
            self.min_length is not None
            and self.max_length is not None
            and self.min_length > self.max_length
        ):
            raise ValueError(
                f"min_length ({self.min_length}) cannot be greater than "
                f"max_length ({self.max_length})"
            )
        return self

    @model_validator(mode="after")
    def validate_value_constraints(self) -> "FieldValidation":
        """Validate that min_value is not greater than max_value."""
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            raise ValueError(
                f"min_value ({self.min_value}) cannot be greater than "
                f"max_value ({self.max_value})"
            )
        return self


class FieldDisplayProperties(CreatorBaseModel):
    """Represents display properties and settings for a form field."""

    width: Optional[int] = Field(
        default=None, ge=1, description="Display width in pixels."
    )
    height: Optional[int] = Field(
        default=None, ge=1, description="Display height in pixels."
    )
    placeholder: Optional[str] = Field(
        default=None, description="Placeholder text for the field."
    )
    help_text: Optional[str] = Field(
        default=None, description="Help text or tooltip for the field."
    )
    css_class: Optional[str] = Field(
        default=None, description="CSS class for styling the field."
    )
    display_order: Optional[int] = Field(
        default=None, ge=0, description="Order in which the field should be displayed."
    )
    hidden: bool = Field(
        default=False, description="Whether the field should be hidden from the form."
    )
    readonly: bool = Field(default=False, description="Whether the field is read-only.")
    disabled: bool = Field(default=False, description="Whether the field is disabled.")
    label_position: Optional[str] = Field(
        default="top",
        description="Position of the field label (top, left, right, bottom).",
    )
    input_type: Optional[str] = Field(
        default=None, description="HTML input type for web forms."
    )


class FormField(CreatorBaseModel):
    """Represents a comprehensive field definition within a Zoho Creator form."""

    id: str = Field(
        description="The unique identifier of the field.",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    name: str = Field(
        description="The display name of the field.", min_length=1, max_length=200
    )
    link_name: str = Field(
        description="The link name of the field (URL-friendly).",
        min_length=1,
        max_length=200,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    field_type: FieldType = Field(description="The type of the field.")
    form_id: str = Field(
        description="The ID of the form the field belongs to.",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    required: bool = Field(description="Whether the field is required.")
    default_value: Optional[Any] = Field(
        default=None, description="The default value of the field."
    )
    options: Optional[Sequence[str]] = Field(
        default=None,
        description="Available options for dropdown, radio, and multiselect fields.",
    )
    validation_rules: Optional[FieldValidation] = Field(
        default=None, description="Validation rules and constraints for the field."
    )
    display_properties: Optional[FieldDisplayProperties] = Field(
        default=None, description="Display properties and settings for the field."
    )
    created_time: Optional[datetime] = Field(
        default=None, description="The time the field was created."
    )
    modified_time: Optional[datetime] = Field(
        default=None, description="The time the field was last modified."
    )
    is_system_field: bool = Field(
        default=False, description="Whether this is a system-generated field."
    )
    is_encrypted: bool = Field(
        default=False, description="Whether the field data is encrypted."
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Description or help text for the field.",
    )

    @field_validator("options")
    @classmethod
    def validate_options_for_field_type(
        cls, v: Optional[Sequence[str]], info: ValidationInfo
    ) -> Optional[Sequence[str]]:
        """Validate that options are provided for fields that require them."""
        field_type = info.data.get("field_type")
        if field_type in [FieldType.DROPDOWN, FieldType.RADIO, FieldType.MULTISELECT]:
            if not v or len(v) == 0:
                raise ValueError(
                    f"Field type {field_type.value} requires options to be specified"
                )
            # Validate that options are not too long
            for option in v:
                if len(option) > 500:
                    raise ValueError(
                        f"Option '{option}' exceeds maximum length of 500 characters"
                    )
        elif (
            field_type
            not in [FieldType.DROPDOWN, FieldType.RADIO, FieldType.MULTISELECT]
            and v
        ):
            # For other field types, options should be None or empty
            pass  # Allow empty options for flexibility
        return v


class FormSchema(CreatorBaseModel):
    """Complete form schema with all fields for dynamic form handling."""

    form_id: str = Field(description="The unique identifier of the form.")
    form_name: str = Field(description="The name of the form.")
    application_id: str = Field(
        description="The ID of the application the form belongs to."
    )
    fields: Sequence[FormField] = Field(
        description="Sequence of form fields that define the form structure."
    )
    created_time: Optional[datetime] = Field(
        default=None, description="The time the form was created."
    )
    modified_time: Optional[datetime] = Field(
        default=None, description="The time the form was last modified."
    )
    version: Optional[int] = Field(
        default=None, ge=1, description="Version number of the form schema."
    )
    is_active: bool = Field(
        default=True, description="Whether the form is currently active."
    )
    description: Optional[str] = Field(
        default=None, description="Description of the form's purpose and usage."
    )

    @field_validator("fields")
    @classmethod
    def validate_fields_not_empty(cls, v: Sequence[FormField]) -> Sequence[FormField]:
        """Validate that the form has at least one field."""
        if not v:
            raise ValueError("Form must have at least one field")
        return v

    @field_validator("fields")
    @classmethod
    def validate_unique_field_names(cls, v: Sequence[FormField]) -> Sequence[FormField]:
        """Validate that all fields have unique names within the form."""
        field_names = [field.name for field in v]
        if len(field_names) != len(set(field_names)):
            raise ValueError("All fields must have unique names within the form")
        return v

    @field_validator("fields")
    @classmethod
    def validate_unique_field_link_names(
        cls, v: Sequence[FormField]
    ) -> Sequence[FormField]:
        """Validate that all fields have unique link names within the form."""
        link_names = [field.link_name for field in v]
        if len(link_names) != len(set(link_names)):
            raise ValueError("All fields must have unique link names within the form")
        return v

    def get_field_by_name(self, field_name: str) -> Optional[FormField]:
        """Get a field by its name."""
        for field in self.fields:
            if field.name == field_name:
                return field
        return None

    def get_field_by_link_name(self, link_name: str) -> Optional[FormField]:
        """Get a field by its link name."""
        for field in self.fields:
            if field.link_name == link_name:
                return field
        return None

    def get_required_fields(self) -> Sequence[FormField]:
        """Get all required fields in the form."""
        return [field for field in self.fields if field.required]

    def get_fields_by_type(self, field_type: FieldType) -> Sequence[FormField]:
        """Get all fields of a specific type."""
        return [field for field in self.fields if field.field_type == field_type]

    def get_visible_fields(self) -> Sequence[FormField]:
        """Get all visible fields (not hidden)."""
        visible_fields = []
        for field in self.fields:
            if field.display_properties and not field.display_properties.hidden:
                visible_fields.append(field)
            elif not field.display_properties:
                # If no display properties, assume visible
                visible_fields.append(field)
        return visible_fields
