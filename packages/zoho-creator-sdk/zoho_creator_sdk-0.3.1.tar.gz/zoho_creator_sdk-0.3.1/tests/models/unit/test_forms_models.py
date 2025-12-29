"""Unit tests for forms models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from zoho_creator_sdk.models import (
    FieldDisplayProperties,
    FieldValidation,
    FormField,
    FormSchema,
)
from zoho_creator_sdk.models.enums import FieldType


class TestFormField:
    """Test cases for FormField."""

    def test_form_field_minimal_creation(self) -> None:
        """FormField can be created with minimal required fields."""
        field = FormField(
            id="field123",
            name="Test Field",
            link_name="test_field",
            field_type=FieldType.TEXT,
            form_id="form456",
            required=False,
        )

        assert field.name == "Test Field"
        assert field.link_name == "test_field"
        assert field.field_type == FieldType.TEXT
        assert field.form_id == "form456"
        assert field.required is False

    def test_form_field_complete_creation(self) -> None:
        """FormField can be created with all available fields."""
        validation = FieldValidation(is_mandatory=True, max_length=100)

        display_properties = FieldDisplayProperties(
            width=200, placeholder="Enter email here"
        )

        field = FormField(
            id="field_complete",
            name="Complete Field",
            link_name="complete_field",
            field_type=FieldType.EMAIL,
            form_id="form123",
            required=True,
            validation_rules=validation,
            display_properties=display_properties,
            default_value="test@example.com",
        )

        assert field.name == "Complete Field"
        assert field.link_name == "complete_field"
        assert field.field_type == FieldType.EMAIL
        assert field.required is True  # Test the required field instead
        assert field.validation_rules.max_length == 100
        assert field.display_properties.width == 200
        assert field.display_properties.placeholder == "Enter email here"
        assert field.default_value == "test@example.com"

    def test_form_field_with_choices(self) -> None:
        """FormField with choice field works correctly."""
        validation = FieldValidation(min_length=1, max_length=100)

        field = FormField(
            id="field_choice",
            name="Choice Field",
            link_name="choice_field",
            field_type=FieldType.DROPDOWN,
            form_id="form123",
            required=False,
            validation_rules=validation,
            options=["Option 1", "Option 2", "Option 3"],
        )

        assert field.options == ["Option 1", "Option 2", "Option 3"]

    def test_form_field_with_options_on_non_choice_field(self) -> None:
        """FormField allows options on non-choice fields (flexibility)."""
        field = FormField(
            id="field_text_with_options",
            name="Text Field with Options",
            link_name="text_field_with_options",
            field_type=FieldType.TEXT,  # TEXT doesn't require options
            form_id="form123",
            required=False,
            options=[
                "Option 1",
                "Option 2",
            ],  # Providing options anyway for flexibility
        )

        # Should not raise an error and options should be preserved
        assert field.options == ["Option 1", "Option 2"]

    def test_form_field_validation_error(self) -> None:
        """FormField raises validation error for invalid data."""
        with pytest.raises(PydanticValidationError):
            FormField(
                id="",  # Invalid: empty string
                name="",  # Invalid: empty string
                link_name="",  # Invalid: empty string
                field_type=FieldType.TEXT,
                form_id="form123",
                required=False,
            )

    def test_form_field_string_representation(self) -> None:
        """FormField string representation contains field name."""
        field = FormField(
            id="field_string",
            name="My Test Field",
            link_name="my_test_field",
            field_type=FieldType.TEXT,
            form_id="form123",
            required=False,
        )

        # Check that the string representation contains the field name
        assert "My Test Field" in str(field)
        assert "field_string" in str(field)


class TestFieldValidation:
    """Test cases for FieldValidation."""

    def test_field_validation_minimal_creation(self) -> None:
        """FieldValidation can be created with minimal fields."""
        validation = FieldValidation()

        # Check default values for actual FieldValidation fields
        assert validation.min_length is None
        assert validation.max_length is None
        assert validation.min_value is None
        assert validation.max_value is None
        assert validation.pattern is None
        assert validation.allow_duplicates is True  # Default value
        assert validation.case_sensitive is True  # Default value

    def test_field_validation_complete_creation(self) -> None:
        """FieldValidation can be created with all fields."""
        validation = FieldValidation(
            max_length=255,
            min_length=5,
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            allow_duplicates=False,
            case_sensitive=False,
            custom_validation="Custom validation rule",
        )

        assert validation.max_length == 255
        assert validation.min_length == 5
        assert validation.pattern == r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert validation.allow_duplicates is False
        assert validation.case_sensitive is False
        assert validation.custom_validation == "Custom validation rule"

    def test_field_validation_numeric_constraints(self) -> None:
        """FieldValidation supports numeric constraints."""
        validation = FieldValidation(min_value=0, max_value=100)

        assert validation.min_value == 0
        assert validation.max_value == 100

    def test_field_validation_pattern_validation(self) -> None:
        """FieldValidation supports regex pattern validation."""
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        validation = FieldValidation(pattern=email_pattern)

        assert validation.pattern == email_pattern


class TestFieldDisplayProperties:
    """Test cases for FieldDisplayProperties."""

    def test_field_display_properties_minimal_creation(self) -> None:
        """FieldDisplayProperties can be created with minimal fields."""
        display = FieldDisplayProperties()

        assert display.hidden is False
        assert display.readonly is False
        assert display.disabled is False

    def test_field_display_properties_complete_creation(self) -> None:
        """FieldDisplayProperties can be created with all fields."""
        display = FieldDisplayProperties(
            hidden=True,
            readonly=True,
            disabled=True,
            width=200,
            height=100,
            label_position="left",
            help_text="Enter your name here",
            placeholder="John Doe",
        )

        assert display.hidden is True
        assert display.readonly is True
        assert display.disabled is True
        assert display.width == 200
        assert display.height == 100
        assert display.label_position == "left"
        assert display.help_text == "Enter your name here"
        assert display.placeholder == "John Doe"


class TestFormSchema:
    """Test cases for FormSchema."""

    def test_form_schema_minimal_creation(self) -> None:
        """FormSchema can be created with minimal fields."""
        field = FormField(
            id="field1",
            name="Test Field",
            link_name="test_field",
            field_type=FieldType.TEXT,
            form_id="form123",
            required=False,
        )

        schema = FormSchema(
            form_id="form123",
            form_name="Test Form",
            application_id="app123",
            fields=[field],
        )

        assert schema.form_name == "Test Form"
        assert schema.form_id == "form123"
        assert schema.application_id == "app123"
        assert len(schema.fields) == 1

    def test_form_schema_complete_creation(self) -> None:
        """FormSchema can be created with all fields."""
        field1 = FormField(
            id="field1",
            name="Name",
            link_name="name",
            field_type=FieldType.TEXT,
            form_id="form123",
            required=True,
            validation_rules=FieldValidation(min_length=1),
        )

        field2 = FormField(
            id="field2",
            name="Email",
            link_name="email",
            field_type=FieldType.EMAIL,
            form_id="form123",
            required=True,
            validation_rules=FieldValidation(min_length=5),
        )

        schema = FormSchema(
            form_id="form123",
            form_name="Complete Form",
            application_id="app123",
            fields=[field1, field2],
        )

        assert schema.form_name == "Complete Form"
        assert schema.form_id == "form123"
        assert schema.application_id == "app123"
        assert len(schema.fields) == 2
        assert schema.fields[0].name == "Name"
        assert schema.fields[1].name == "Email"

    def test_form_schema_with_multiple_fields(self) -> None:
        """FormSchema can contain multiple fields of different types."""
        text_field = FormField(
            id="field1",
            name="Name",
            link_name="name",
            field_type=FieldType.TEXT,
            form_id="form123",
            required=False,
        )

        email_field = FormField(
            id="field2",
            name="Email",
            link_name="email",
            field_type=FieldType.EMAIL,
            form_id="form123",
            required=False,
        )

        dropdown_field = FormField(
            id="field3",
            name="Category",
            link_name="category",
            field_type=FieldType.DROPDOWN,
            form_id="form123",
            required=False,
            options=["Personal", "Business", "Other"],
        )

        schema = FormSchema(
            form_id="form123",
            form_name="Multi-field Form",
            application_id="app123",
            fields=[text_field, email_field, dropdown_field],
        )

        assert len(schema.fields) == 3
        assert schema.fields[0].field_type == FieldType.TEXT
        assert schema.fields[1].field_type == FieldType.EMAIL
        assert schema.fields[2].field_type == FieldType.DROPDOWN

    def test_form_schema_validation_error_missing_required_fields(self) -> None:
        """FormSchema raises validation error for missing required fields."""
        with pytest.raises(PydanticValidationError):
            FormSchema(
                form_id="form123"
                # Missing form_name, application_id, fields
            )

    def test_form_schema_string_representation(self) -> None:
        """FormSchema string representation contains form name."""
        field = FormField(
            id="field1",
            name="Test Field",
            link_name="test_field",
            field_type=FieldType.TEXT,
            form_id="form123",
            required=False,
        )

        schema = FormSchema(
            form_id="form123",
            form_name="My Test Form",
            application_id="app123",
            fields=[field],
        )

        # Check that the string representation contains the form name
        assert "My Test Form" in str(schema)
        assert "form123" in str(schema)

    def test_form_schema_empty_fields(self) -> None:
        """FormSchema requires at least one field."""
        with pytest.raises(PydanticValidationError) as exc_info:
            FormSchema(
                form_id="form123",
                form_name="Empty Form",
                application_id="app123",
                fields=[],
            )

        assert "Form must have at least one field" in str(exc_info.value)

    def test_form_schema_field_ordering(self) -> None:
        """FormSchema fields maintain their order."""
        field1 = FormField(
            id="field1",
            name="First Field",
            link_name="first_field",
            field_type=FieldType.TEXT,
            form_id="form123",
            required=False,
        )

        field2 = FormField(
            id="field2",
            name="Second Field",
            link_name="second_field",
            field_type=FieldType.TEXT,
            form_id="form123",
            required=False,
        )

        schema = FormSchema(
            form_id="form123",
            form_name="Ordered Form",
            application_id="app123",
            fields=[field2, field1],  # Intentionally out of order
        )

        # Fields should maintain the order they were added
        assert schema.fields[0].name == "Second Field"
        assert schema.fields[1].name == "First Field"
