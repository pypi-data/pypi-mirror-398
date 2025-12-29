"""Final tests to reach 100% coverage."""

from __future__ import annotations

import pytest

from zoho_creator_sdk.client import _MinimalRecordModel


class TestMinimalRecordModelFinal:
    """Final tests for _MinimalRecordModel edge cases."""

    def test_minimal_record_model_data_without_id_error(self) -> None:
        """_MinimalRecordModel raises error when data is present but id is missing."""
        with pytest.raises(
            ValueError,
            match="Form-style record must contain 'id' when 'data' is present",
        ):
            _MinimalRecordModel(data={"field": "value"})
