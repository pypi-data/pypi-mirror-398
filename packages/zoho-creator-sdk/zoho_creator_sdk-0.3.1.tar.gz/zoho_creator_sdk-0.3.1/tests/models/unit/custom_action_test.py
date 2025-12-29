"""Unit tests for the custom action model."""

from __future__ import annotations

from datetime import datetime

from zoho_creator_sdk.models.custom_action import CustomAction


def test_custom_action_model_instantiation() -> None:
    action = CustomAction(
        id="act",
        name="Notify",
        link_name="notify",
        application_id="app",
        form_id="form",
        action_type="script",
        configuration={"script": "info"},
        created_time=datetime.utcnow(),
        modified_time=datetime.utcnow(),
        owner="user",
    )

    assert action.configuration["script"] == "info"
