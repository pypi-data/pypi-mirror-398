"""Unit tests for section models."""

from __future__ import annotations

from zoho_creator_sdk.models.section import Component, Section


def test_component_defaults() -> None:
    comp = Component(
        id="c1",
        name="Widget",
        link_name="widget",
        component_type=1,
        section_id="s1",
    )

    assert comp.is_visible is True


def test_section_contains_components() -> None:
    section = Section(
        id="s1",
        name="Main",
        link_name="main",
        application_id="app",
        page_id="page",
        components=[
            Component(
                id="c1",
                name="Widget",
                link_name="widget",
                component_type=1,
                section_id="s1",
            )
        ],
    )

    assert len(section.components) == 1
