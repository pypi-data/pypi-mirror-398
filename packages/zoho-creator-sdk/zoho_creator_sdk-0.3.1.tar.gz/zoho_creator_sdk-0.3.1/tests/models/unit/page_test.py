"""Unit tests for the page model."""

from __future__ import annotations

from zoho_creator_sdk.models.page import Page


def test_page_defaults() -> None:
    page = Page(
        id="page",
        name="Dashboard",
        link_name="dashboard",
        application_id="app",
    )

    assert page.is_active is True
