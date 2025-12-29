from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from zoho_projects_sdk.api.projects import ProjectsAPI


@pytest.mark.asyncio
async def test_get_all_returns_validated_projects() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(
            return_value={
                "projects": [
                    {
                        "id": 101,
                        "name": "Sample Project",
                        "status": {
                            "id": "status-1",
                            "name": "active",
                            "color": "green",
                            "color_hexcode": "#00FF00",
                            "is_closed_type": False,
                        },
                    }
                ]
            }
        ),
    )

    projects = await ProjectsAPI(client).get_all(page=2, per_page=50)

    assert len(projects) == 1
    assert projects[0].id == 101
    assert projects[0].name == "Sample Project"
    client.get.assert_awaited_once_with(
        "/portal/portal-123/projects",
        params={"page": 2, "per_page": 50},
    )


@pytest.mark.asyncio
async def test_get_returns_empty_project_when_not_found() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(return_value={"projects": []}),
    )

    project = await ProjectsAPI(client).get(project_id=42)

    assert project.id == 0
    assert project.name == ""
    assert project.status == "active"
    client.get.assert_awaited_once_with(
        "/portal/portal-123/projects/42",
    )


@pytest.mark.asyncio
async def test_get_returns_first_project_when_present() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(
            return_value={
                "projects": [
                    {
                        "id": 7,
                        "name": "Primary",
                        "status": {
                            "id": "status-1",
                            "name": "active",
                            "color": "green",
                            "color_hexcode": "#00FF00",
                            "is_closed_type": False,
                        },
                    },
                    {
                        "id": 8,
                        "name": "Secondary",
                        "status": {
                            "id": "status-2",
                            "name": "on hold",
                            "color": "yellow",
                            "color_hexcode": "#FFFF00",
                            "is_closed_type": False,
                        },
                    },
                ]
            }
        ),
    )

    project = await ProjectsAPI(client).get(project_id=7)

    assert project.id == 7
    assert project.name == "Primary"
    client.get.assert_awaited_once_with(
        "/portal/portal-123/projects/7",
    )


@pytest.mark.asyncio
async def test_portal_id_missing_raises_value_error() -> None:
    client = SimpleNamespace(portal_id=None, get=AsyncMock())
    projects_api = ProjectsAPI(client)

    with pytest.raises(ValueError, match="Portal ID is not configured"):
        await projects_api.get_all()


@pytest.mark.asyncio
async def test_create_posts_payload_and_returns_project() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        post=AsyncMock(
            return_value={
                "project": {
                    "id": 10,
                    "name": "Created",
                    "status": {
                        "id": "status-1",
                        "name": "active",
                        "color": "green",
                        "color_hexcode": "#00FF00",
                        "is_closed_type": False,
                    },
                }
            }
        ),
    )

    class ProjectPayload:
        def model_dump(
            self, *, by_alias: bool, exclude_none: bool
        ) -> dict[str, object]:
            assert by_alias is True
            assert exclude_none is True
            return {"name": "Created", "status": "active"}

    result = await ProjectsAPI(client).create(project_data=ProjectPayload())

    assert result.id == 10
    assert result.name == "Created"
    client.post.assert_awaited_once_with(
        "/portal/portal-123/projects",
        json={"name": "Created", "status": "active"},
    )


@pytest.mark.asyncio
async def test_update_patches_payload_and_returns_project() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        patch=AsyncMock(
            return_value={
                "project": {
                    "id": 10,
                    "name": "Updated",
                    "status": {
                        "id": "status-3",
                        "name": "inactive",
                        "color": "red",
                        "color_hexcode": "#FF0000",
                        "is_closed_type": True,
                    },
                }
            }
        ),
    )

    class ProjectPayload:
        def model_dump(
            self, *, by_alias: bool, exclude_none: bool
        ) -> dict[str, object]:
            assert by_alias is True
            assert exclude_none is True
            return {"name": "Updated", "status": "inactive"}

    result = await ProjectsAPI(client).update(
        project_id=10,
        project_data=ProjectPayload(),
    )

    assert result.id == 10
    assert result.status.name == "inactive"
    client.patch.assert_awaited_once_with(
        "/portal/portal-123/projects/10",
        json={"name": "Updated", "status": "inactive"},
    )


@pytest.mark.asyncio
async def test_delete_invokes_client_delete_and_returns_true() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        delete=AsyncMock(return_value=None),
    )

    result = await ProjectsAPI(client).delete(project_id=5)

    assert result is True
    client.delete.assert_awaited_once_with(
        "/portal/portal-123/projects/5",
    )


@pytest.mark.asyncio
async def test_get_all_with_dict_response() -> None:
    """Test get_all when API returns a dictionary with projects key."""
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(
            return_value={
                "projects": [
                    {
                        "id": 201,
                        "name": "Dict Response Project",
                        "status": {
                            "id": "status-201",
                            "name": "active",
                            "color": "green",
                            "color_hexcode": "#00FF00",
                            "is_closed_type": False,
                        },
                    }
                ]
            }
        ),
    )

    projects = await ProjectsAPI(client).get_all(page=1, per_page=10)

    assert len(projects) == 1
    assert projects[0].id == 201
    assert projects[0].name == "Dict Response Project"
    assert projects[0].status_name == "active"
    client.get.assert_awaited_once_with(
        "/portal/portal-123/projects",
        params={"page": 1, "per_page": 10},
    )


@pytest.mark.asyncio
async def test_get_with_dict_response() -> None:
    """Test get when API returns a dictionary with projects key."""
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(
            return_value={
                "projects": [
                    {
                        "id": 202,
                        "name": "Dict Single Project",
                        "status": {
                            "id": "status-202",
                            "name": "completed",
                            "color": "blue",
                            "color_hexcode": "#0000FF",
                            "is_closed_type": True,
                        },
                    }
                ]
            }
        ),
    )

    project = await ProjectsAPI(client).get(project_id=202)

    assert project.id == 202
    assert project.name == "Dict Single Project"
    assert project.status_name == "completed"
    client.get.assert_awaited_once_with("/portal/portal-123/projects/202")


@pytest.mark.asyncio
async def test_get_all_with_list_response() -> None:
    """Test get_all when API returns a list directly (hits the if branch)."""
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(
            return_value=[
                {
                    "id": 301,
                    "name": "List Response Project",
                    "status": {
                        "id": "status-301",
                        "name": "active",
                        "color": "green",
                        "color_hexcode": "#00FF00",
                        "is_closed_type": False,
                    },
                }
            ]
        ),
    )

    projects = await ProjectsAPI(client).get_all(page=1, per_page=10)

    assert len(projects) == 1
    assert projects[0].id == 301
    assert projects[0].name == "List Response Project"
    assert projects[0].status_name == "active"
    client.get.assert_awaited_once_with(
        "/portal/portal-123/projects",
        params={"page": 1, "per_page": 10},
    )


@pytest.mark.asyncio
async def test_get_with_list_response() -> None:
    """Test get when API returns a list directly (hits the if branch)."""
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(
            return_value=[
                {
                    "id": 302,
                    "name": "List Single Project",
                    "status": {
                        "id": "status-302",
                        "name": "completed",
                        "color": "blue",
                        "color_hexcode": "#0000FF",
                        "is_closed_type": True,
                    },
                }
            ]
        ),
    )

    project = await ProjectsAPI(client).get(project_id=302)

    assert project.id == 302
    assert project.name == "List Single Project"
    assert project.status_name == "completed"
    client.get.assert_awaited_once_with("/portal/portal-123/projects/302")


@pytest.mark.asyncio
async def test_get_with_empty_project_object() -> None:
    """Test get when API returns an empty project object (line 65 coverage)."""
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(return_value={"project": None}),  # Empty/falsy project object
    )

    project = await ProjectsAPI(client).get(project_id=999)

    assert project.id == 0
    assert project.name == ""
    assert project.status == "active"
    client.get.assert_awaited_once_with("/portal/portal-123/projects/999")


@pytest.mark.asyncio
async def test_get_with_unexpected_response_format() -> None:
    """Test get when API returns unexpected response format (line 73 coverage)."""
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(
            return_value="unexpected_string_response"  # Neither list nor dict
        ),
    )

    project = await ProjectsAPI(client).get(project_id=888)

    assert project.id == 0
    assert project.name == ""
    assert project.status == "active"
    client.get.assert_awaited_once_with("/portal/portal-123/projects/888")


@pytest.mark.asyncio
async def test_extract_projects_from_response_with_empty_project() -> None:
    """Test the private method _extract_projects_from_response with empty project."""
    client = SimpleNamespace(portal_id="portal-123")
    projects_api = ProjectsAPI(client)

    # Test empty project object case
    result = projects_api._extract_projects_from_response({"project": None})
    assert len(result) == 1
    assert result[0].id == 0
    assert result[0].name == ""
    assert result[0].status == "active"


@pytest.mark.asyncio
async def test_extract_projects_from_response_with_unexpected_format() -> None:
    """Test the private method _extract_projects_from_response with unexpected format."""
    client = SimpleNamespace(portal_id="portal-123")
    projects_api = ProjectsAPI(client)

    # Test unexpected response format case
    result = projects_api._extract_projects_from_response("unexpected")
    assert len(result) == 0  # Should return empty list


@pytest.mark.asyncio
async def test_create_empty_project() -> None:
    """Test the private method _create_empty_project."""
    client = SimpleNamespace(portal_id="portal-123")
    projects_api = ProjectsAPI(client)

    empty_project = projects_api._create_empty_project()
    assert empty_project.id == 0
    assert empty_project.name == ""
    assert empty_project.status == "active"
