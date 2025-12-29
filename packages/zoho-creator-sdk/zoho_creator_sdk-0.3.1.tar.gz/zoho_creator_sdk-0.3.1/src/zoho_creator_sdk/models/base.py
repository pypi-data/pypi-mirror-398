"""
Base models for the Zoho Creator SDK.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Type

from pydantic import BaseModel, Field

from .metadata import Metadata

__all__ = ["CreatorBaseModel", "ModelWithMetadata", "validate_enum_value"]


def validate_enum_value(enum_class: Type[Enum]) -> Callable[[Any], Any]:
    """Custom validator for enum values to provide better error messages."""

    def validate(value: Any) -> Any:
        try:
            return enum_class(value)
        except ValueError as exc:
            valid_values = [item.value for item in enum_class]
            raise ValueError(
                f"Invalid {enum_class.__name__}: '{value}'. "
                f"Valid values are: {valid_values}"
            ) from exc

    return validate


class CreatorBaseModel(BaseModel):
    """Base model for Zoho Creator SDK with consistent configuration."""

    model_config = {"from_attributes": True}


class ModelWithMetadata(CreatorBaseModel):
    """Base model for Zoho Creator SDK models that include metadata."""

    metadata: Metadata = Field(
        default_factory=Metadata,
        description="Comprehensive metadata for the model.",
    )
