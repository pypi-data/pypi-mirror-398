"""Unit tests for form-related models."""

from __future__ import annotations

from datetime import datetime

import pytest

from zoho_creator_sdk.models.forms import (
    FieldDisplayProperties,
    FieldType,
    FieldValidation,
    FormField,
    FormSchema,
)


def _field(field_type: FieldType = FieldType.TEXT, **overrides):
    data = {
        "id": "field",
        "name": "Field",
        "link_name": "field",
        "field_type": field_type,
        "form_id": "form",
        "required": True,
    }
    data.update(overrides)
    return FormField(**data)


def test_field_validation_length_constraints() -> None:
    with pytest.raises(ValueError):
        FieldValidation(min_length=10, max_length=5)

    with pytest.raises(ValueError):
        FieldValidation(min_value=10, max_value=5)

    valid = FieldValidation(min_length=1, max_length=5, min_value=1, max_value=10)
    assert valid.max_length == 5


def test_form_field_options_required_for_dropdown() -> None:
    with pytest.raises(ValueError):
        _field(FieldType.DROPDOWN, options=[])

    field = _field(FieldType.DROPDOWN, options=["Small", "Medium"])
    assert field.options == ["Small", "Medium"]

    with pytest.raises(ValueError):
        _field(FieldType.DROPDOWN, options=["x" * 501])


def test_form_schema_validations() -> None:
    field1 = _field(name="A", link_name="a")
    field2 = _field(
        name="B", link_name="b", display_properties=FieldDisplayProperties(hidden=False)
    )
    schema = FormSchema(
        form_id="form",
        form_name="Form",
        application_id="app",
        fields=[field1, field2],
        created_time=datetime.utcnow(),
    )

    assert schema.get_field_by_name("A") is field1
    assert schema.get_field_by_link_name("b") is field2
    assert schema.get_required_fields() == [field1, field2]
    assert schema.get_fields_by_type(FieldType.TEXT)[0] is field1
    assert len(schema.get_visible_fields()) == 2


def test_form_schema_rejects_empty_fields() -> None:
    with pytest.raises(ValueError):
        FormSchema(form_id="f", form_name="F", application_id="app", fields=[])

    field1 = _field(name="same", link_name="a")
    field2 = _field(name="same", link_name="b")
    with pytest.raises(ValueError):
        FormSchema(
            form_id="f", form_name="F", application_id="app", fields=[field1, field2]
        )

    field3 = _field(name="c", link_name="a")
    with pytest.raises(ValueError):
        FormSchema(
            form_id="f", form_name="F", application_id="app", fields=[field1, field3]
        )


def test_form_schema_missing_fields_return_none() -> None:
    hidden = _field(
        name="Hidden",
        link_name="hidden",
        required=False,
        display_properties=FieldDisplayProperties(hidden=True),
    )
    schema = FormSchema(
        form_id="form",
        form_name="Form",
        application_id="app",
        fields=[hidden],
    )

    assert schema.get_field_by_name("missing") is None
    assert schema.get_field_by_link_name("missing") is None
    assert schema.get_visible_fields() == []
