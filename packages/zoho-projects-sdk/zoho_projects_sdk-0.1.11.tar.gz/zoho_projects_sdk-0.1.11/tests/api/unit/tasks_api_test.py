from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from zoho_projects_sdk.api.tasks import ListParams, TasksAPI


@pytest.mark.asyncio
async def test_move_coerces_status_mapping_to_list() -> None:
    client = SimpleNamespace(portal_id="portal-123", post=AsyncMock())
    status_mapping_tuple = ("status-a", "status-b")

    result = await TasksAPI(client).move(
        project_id=1,
        task_id=2,
        target_tasklist_id=3,
        status_mapping=status_mapping_tuple,
    )

    assert result is True
    client.post.assert_awaited_once_with(
        "/portal/portal-123/projects/1/tasks/2/move",
        json={
            "target_tasklist_id": 3,
            "status_mapping": list(status_mapping_tuple),
        },
    )


@pytest.mark.asyncio
async def test_move_without_status_mapping_does_not_set_key() -> None:
    client = SimpleNamespace(portal_id="portal-123", post=AsyncMock())

    result = await TasksAPI(client).move(
        project_id="proj",
        task_id="task",
        target_tasklist_id="list",
        status_mapping=None,
    )

    assert result is True
    client.post.assert_awaited_once_with(
        "/portal/portal-123/projects/proj/tasks/task/move",
        json={"target_tasklist_id": "list"},
    )


@pytest.mark.asyncio
async def test_get_associated_bugs_returns_list_only_when_payload_has_list() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(return_value={"associated_bugs": "not-a-list"}),
    )

    result = await TasksAPI(client).get_associated_bugs(project_id=1, task_id=2)

    assert result == []
    client.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_portal_id_missing_raises_value_error() -> None:
    client = SimpleNamespace(portal_id=None)
    tasks_api = TasksAPI(client)

    with pytest.raises(ValueError, match="Portal ID is not configured"):
        await tasks_api.list_by_portal()


@pytest.mark.asyncio
async def test_create_with_model_dump_filters_none() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        post=AsyncMock(return_value={"task": {}}),
    )

    class ModelDumpOnly:
        def model_dump(
            self, *, by_alias: bool, exclude_none: bool
        ) -> dict[str, object]:
            assert by_alias is True
            assert exclude_none is True
            return {"a": 1, "b": None}

    await TasksAPI(client).create(project_id=1, task_data=ModelDumpOnly())

    client.post.assert_awaited_once_with(
        "/portal/portal-123/projects/1/tasks",
        json={"a": 1},
    )


@pytest.mark.asyncio
async def test_create_with_mapping_filters_none_values() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        post=AsyncMock(return_value={"task": {}}),
    )

    await TasksAPI(client).create(project_id=1, task_data={"a": 1, "b": None})

    client.post.assert_awaited_once_with(
        "/portal/portal-123/projects/1/tasks",
        json={"a": 1},
    )


@pytest.mark.asyncio
async def test_create_with_dict_method_excludes_private_fields() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        post=AsyncMock(return_value={"task": {}}),
    )

    class DictMethodOnly:
        def dict(self) -> dict[str, object]:
            return {"a": 1, "_secret": "hidden", "none": None}

    await TasksAPI(client).create(project_id=1, task_data=DictMethodOnly())

    client.post.assert_awaited_once_with(
        "/portal/portal-123/projects/1/tasks",
        json={"a": 1},
    )


@pytest.mark.asyncio
async def test_create_with_object_attrs_excludes_private_fields() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        post=AsyncMock(return_value={"task": {}}),
    )

    class HasAttrs:
        def __init__(self) -> None:
            self.allowed = 1
            self._ignored = "value"
            self.also_none = None

    await TasksAPI(client).create(project_id=1, task_data=HasAttrs())

    client.post.assert_awaited_once_with(
        "/portal/portal-123/projects/1/tasks",
        json={"allowed": 1},
    )


@pytest.mark.asyncio
async def test_create_rejects_unsupported_task_data_type() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        post=AsyncMock(return_value={"task": {}}),
    )

    with pytest.raises(TypeError):
        await TasksAPI(client).create(project_id=1, task_data=42)


@pytest.mark.asyncio
async def test_list_by_portal_with_all_params() -> None:
    """Test list_by_portal with all parameters to cover missing lines."""
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(return_value={"tasks": []}),
    )

    params = ListParams(
        page=2,
        per_page=10,
        filter_={"status": "active"},
        sort_by="name",
        view_id="view-123",
    )
    await TasksAPI(client).list_by_portal(params=params)

    client.get.assert_awaited_once_with(
        "/portal/portal-123/tasks",
        params={
            "page": 2,
            "per_page": 10,
            "filter": '{"status": "active"}',
            "sort_by": "name",
            "view_id": "view-123",
        },
    )


@pytest.mark.asyncio
async def test_list_by_project_with_string_filter() -> None:
    """Test list_by_project with string filter to cover missing lines."""
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(return_value={"tasks": []}),
    )

    params = ListParams(
        page=1,
        per_page=5,
        filter_="status:active",
        sort_by="created_time",
        view_id=456,
    )
    await TasksAPI(client).list_by_project(project_id="proj-123", params=params)

    client.get.assert_awaited_once_with(
        "/portal/portal-123/projects/proj-123/tasks",
        params={
            "page": 1,
            "per_page": 5,
            "filter": "status:active",
            "sort_by": "created_time",
            "view_id": 456,
        },
    )
