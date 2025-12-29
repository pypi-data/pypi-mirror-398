"""Unit tests for base models."""

from __future__ import annotations

import pytest

from zoho_creator_sdk.models.base import (
    CreatorBaseModel,
    ModelWithMetadata,
    validate_enum_value,
)
from zoho_creator_sdk.models.enums import FieldType


class TestCreatorBaseModel:
    """Test cases for CreatorBaseModel."""

    def test_creator_base_model_basic_instantiation(self) -> None:
        """CreatorBaseModel can be instantiated with valid data."""
        model = CreatorBaseModel()

        assert isinstance(model, CreatorBaseModel)
        # CreatorBaseModel should be able to be instantiated without any required fields

    def test_creator_base_model_config(self) -> None:
        """CreatorBaseModel has correct configuration."""
        config = CreatorBaseModel.model_config
        assert config.get("from_attributes") is True


class TestModelWithMetadata:
    """Test cases for ModelWithMetadata."""

    def test_model_with_metadata_basic_instantiation(self) -> None:
        """ModelWithMetadata can be instantiated with default metadata."""
        model = ModelWithMetadata()

        assert isinstance(model, ModelWithMetadata)
        assert hasattr(model, "metadata")
        assert model.metadata is not None

    def test_model_with_metadata_with_data(self) -> None:
        """ModelWithMetadata can be instantiated with additional data."""
        data = {"name": "Test", "description": "Test description"}

        model = ModelWithMetadata(**data)

        assert model is not None
        assert hasattr(model, "metadata")
        assert model.metadata is not None


class TestValidateEnumValue:
    """Test cases for validate_enum_value function."""

    def test_validate_enum_value_valid(self) -> None:
        """validate_enum_value accepts valid enum values."""
        validator = validate_enum_value(FieldType)

        result = validator("text")
        assert result == FieldType.TEXT

    def test_validate_enum_value_invalid(self) -> None:
        """validate_enum_value raises ValueError for invalid enum values."""
        validator = validate_enum_value(FieldType)

        with pytest.raises(ValueError) as exc_info:
            validator("INVALID_VALUE")

        assert "Invalid FieldType: 'INVALID_VALUE'" in str(exc_info.value)
        assert "Valid values are:" in str(exc_info.value)

    def test_validate_enum_value_enum_instance(self) -> None:
        """validate_enum_value accepts enum instances directly."""
        validator = validate_enum_value(FieldType)

        result = validator(FieldType.EMAIL)
        assert result == FieldType.EMAIL

    def test_validate_enum_value_case_sensitivity(self) -> None:
        """validate_enum_value requires exact case matching."""
        validator = validate_enum_value(FieldType)

        # Test with lowercase value (should work - this is the actual enum value)
        result = validator("text")
        assert result == FieldType.TEXT

        # Test with invalid case (should fail)
        with pytest.raises(ValueError):
            validator("Text")  # Mixed case should fail
