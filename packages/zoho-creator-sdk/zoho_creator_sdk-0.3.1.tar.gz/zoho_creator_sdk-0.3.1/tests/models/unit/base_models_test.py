"""Unit tests for base model utilities."""

from __future__ import annotations

from enum import Enum

import pytest

from zoho_creator_sdk.models.base import (
    CreatorBaseModel,
    ModelWithMetadata,
    validate_enum_value,
)


class SimpleEnum(Enum):
    OK = "ok"


class SimpleModel(CreatorBaseModel):
    value: str


def test_validate_enum_value() -> None:
    validator = validate_enum_value(SimpleEnum)

    assert validator("ok") is SimpleEnum.OK

    with pytest.raises(ValueError) as exc:
        validator("nope")

    assert "Invalid SimpleEnum" in str(exc.value)
    assert "Valid values are: ['ok']" in str(exc.value)


def test_validate_enum_value_with_multiple_values() -> None:
    """Test validate_enum_value with an enum that has multiple values."""

    class MultiEnum(Enum):
        FIRST = "first"
        SECOND = "second"
        THIRD = "third"

    validator = validate_enum_value(MultiEnum)

    # Test valid values
    assert validator("first") is MultiEnum.FIRST
    assert validator("second") is MultiEnum.SECOND
    assert validator("third") is MultiEnum.THIRD

    # Test invalid value
    with pytest.raises(ValueError) as exc:
        validator("invalid")

    assert "Invalid MultiEnum" in str(exc.value)
    assert "Valid values are: ['first', 'second', 'third']" in str(exc.value)


def test_validate_enum_value_with_numeric_values() -> None:
    """Test validate_enum_value with an enum that has numeric values."""

    class NumericEnum(Enum):
        ONE = 1
        TWO = 2
        THREE = 3

    validator = validate_enum_value(NumericEnum)

    # Test valid values
    assert validator(1) is NumericEnum.ONE
    assert validator(2) is NumericEnum.TWO
    assert validator(3) is NumericEnum.THREE

    # Test invalid value
    with pytest.raises(ValueError) as exc:
        validator(4)

    assert "Invalid NumericEnum" in str(exc.value)
    assert "Valid values are: [1, 2, 3]" in str(exc.value)


def test_validate_enum_value_with_mixed_values() -> None:
    """Test validate_enum_value with an enum that has mixed type values."""

    class MixedEnum(Enum):
        TEXT = "text"
        NUMBER = 42
        BOOLEAN = True

    validator = validate_enum_value(MixedEnum)

    # Test valid values
    assert validator("text") is MixedEnum.TEXT
    assert validator(42) is MixedEnum.NUMBER
    assert validator(True) is MixedEnum.BOOLEAN

    # Test invalid value
    with pytest.raises(ValueError) as exc:
        validator("invalid")

    assert "Invalid MixedEnum" in str(exc.value)
    assert "Valid values are: ['text', 42, True]" in str(exc.value)


def test_model_with_metadata_has_default_metadata() -> None:
    model = ModelWithMetadata()

    assert model.metadata is not None
    assert model.model_dump()["metadata"]
