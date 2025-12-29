"""Unit tests for :mod:`zoho_creator_sdk.auth.BaseAuthHandler`."""

from __future__ import annotations

import pytest

from zoho_creator_sdk.auth import BaseAuthHandler


class DummyHandler(BaseAuthHandler):
    """Concrete handler used for exercising the abstract base class."""

    def __init__(self) -> None:
        self.refresh_count = 0

    def get_auth_headers(self):  # type: ignore[override]
        return {"Authorization": "Token"}

    def refresh_auth(self) -> None:  # type: ignore[override]
        self.refresh_count += 1


def test_base_handler_cannot_be_instantiated_directly() -> None:
    """Instantiating the abstract base class must fail."""

    with pytest.raises(TypeError):
        BaseAuthHandler()  # type: ignore[abstract]


def test_concrete_handler_inherits_contract() -> None:
    """A concrete subclass can be instantiated and returns headers."""

    handler = DummyHandler()

    assert handler.get_auth_headers()["Authorization"] == "Token"

    handler.refresh_auth()
    assert handler.refresh_count == 1
