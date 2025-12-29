# pylint: disable=redefined-outer-name
"""Unit tests for PortalsAPI behavior."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from zoho_projects_sdk.api.portals import PortalsAPI
from zoho_projects_sdk.models.portal_models import Portal


@pytest.fixture
def fake_api_client() -> SimpleNamespace:
    auth_handler = SimpleNamespace(portal_id="test_portal")
    client = SimpleNamespace(
        _auth_handler=auth_handler,
        get=AsyncMock(),
        post=AsyncMock(),
        patch=AsyncMock(),
        delete=AsyncMock(),
    )
    # Add portal_id property to match the expected interface
    client.portal_id = "test_portal"
    return client


@pytest.fixture
def portals_api_instance(fake_api_client: SimpleNamespace) -> PortalsAPI:
    return PortalsAPI(fake_api_client)


@pytest.mark.asyncio
async def test_get_all_handles_list_response(
    portals_api_instance: PortalsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.get.return_value = [
        {"id": 1, "name": "Portal A"},
        {"id": 2, "name": "Portal B"},
    ]

    portals = await portals_api_instance.get_all()

    assert [portal.id for portal in portals] == [1, 2]
    fake_api_client.get.assert_awaited_once_with("/portals/")


@pytest.mark.asyncio
async def test_get_all_handles_dict_response(
    portals_api_instance: PortalsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.get.return_value = {
        "portals": [
            {"id": 11, "name": "Portal Eleven"},
        ]
    }

    portals = await portals_api_instance.get_all()

    assert len(portals) == 1
    assert portals[0].name == "Portal Eleven"


@pytest.mark.asyncio
async def test_get_handles_list_response(
    portals_api_instance: PortalsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.get.return_value = [{"id": 5, "name": "List Portal"}]

    portal = await portals_api_instance.get(5)

    assert portal.id == 5
    fake_api_client.get.assert_awaited_once_with("/portals/5/")


@pytest.mark.asyncio
async def test_get_handles_dict_response(
    portals_api_instance: PortalsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.get.return_value = {
        "portals": [
            {"id": 7, "name": "Dict Portal"},
        ]
    }

    portal = await portals_api_instance.get(7)

    assert portal.name == "Dict Portal"


@pytest.mark.asyncio
async def test_get_returns_default_when_missing(
    portals_api_instance: PortalsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.get.return_value = {}

    portal = await portals_api_instance.get(123)

    assert portal.id == 0
    assert portal.name == ""
    fake_api_client.get.assert_awaited_once_with("/portals/123/")


@pytest.mark.asyncio
async def test_create_uses_post_and_returns_portal(
    portals_api_instance: PortalsAPI, fake_api_client: SimpleNamespace
) -> None:
    portal_model = Portal(id=20, name="New Portal")
    fake_api_client.post.return_value = {"portal": {"id": 21, "name": "Created Portal"}}

    created = await portals_api_instance.create(portal_model)

    assert created.id == 21
    fake_api_client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_uses_patch_and_returns_portal(
    portals_api_instance: PortalsAPI, fake_api_client: SimpleNamespace
) -> None:
    portal_model = Portal(id=30, name="Updated Portal")
    fake_api_client.patch.return_value = {
        "portal": {"id": 30, "name": "Updated Portal"}
    }

    updated = await portals_api_instance.update(30, portal_model)

    assert updated.name == "Updated Portal"
    fake_api_client.patch.assert_awaited_once_with(
        "/portals/30/",
        json=portal_model.model_dump(by_alias=True),
    )


@pytest.mark.asyncio
async def test_delete_invokes_client_delete(
    portals_api_instance: PortalsAPI, fake_api_client: SimpleNamespace
) -> None:
    result = await portals_api_instance.delete(99)

    assert result is True
    fake_api_client.delete.assert_awaited_once_with("/portals/99/")
