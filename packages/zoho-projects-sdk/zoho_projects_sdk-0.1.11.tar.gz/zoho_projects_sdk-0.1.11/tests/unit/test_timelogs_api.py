# pylint: disable=redefined-outer-name
"""Unit tests for the TimelogsAPI class."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from zoho_projects_sdk.api.timelogs import (
    TimelogFilters,
    TimelogOperationParams,
    TimelogRequestParams,
    TimelogsAPI,
    ZohoProjectsException,
)
from zoho_projects_sdk.models.timelog_models import TimeLog


@pytest.fixture
def fake_api_client() -> SimpleNamespace:
    """Create an ApiClient-like object backed by AsyncMocks."""

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
def timelogs_api_instance(fake_api_client: SimpleNamespace) -> TimelogsAPI:
    return TimelogsAPI(fake_api_client)


@pytest.mark.asyncio
async def test_get_all_with_log_details_structure(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.get.return_value = {
        "time_logs": [
            {
                "log_details": [
                    {
                        "id": 101,
                        "date": "2024-01-01",
                        "log_hour": "02:30",
                    },
                    {
                        "id": 102,
                        "date": "2024-01-01",
                        "log_hour": "01:00",
                    },
                ]
            }
        ]
    }

    filters = TimelogFilters(
        start_date="2024-01-01",
        end_date="2024-01-31",
        user_id="user-1",
        bill_type="Billable",
        approval_type="Approved",
        view_type="customdate",
        module="milestone",
        filter_params={"sort_column": "date"},
    )
    result = await timelogs_api_instance.get_all(
        project_id=123,
        page=2,
        per_page=100,
        filters=filters,
    )

    assert [timelog.id for timelog in result] == [101, 102]
    assert all(isinstance(timelog, TimeLog) for timelog in result)

    fake_api_client.get.assert_awaited_once()
    awaited_args, awaited_kwargs = fake_api_client.get.await_args
    assert awaited_args == ("/portal/test_portal/projects/123/timelogs",)

    params = awaited_kwargs["params"]
    assert params["page"] == 2
    assert params["per_page"] == 100
    assert params["start_date"] == "2024-01-01"
    assert params["end_date"] == "2024-01-31"
    assert params["user_id"] == "user-1"
    assert params["billtype"] == "Billable"
    assert params["approvaltype"] == "Approved"
    assert params["view_type"] == "customdate"
    assert params["sort_column"] == "date"
    assert params["module"] == '{"type": "milestone"}'


@pytest.mark.asyncio
async def test_get_all_direct_timelogs_structure(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.get.return_value = {
        "timelogs": [
            {
                "id": 201,
                "date": "2024-01-05",
                "log_hour": "03:00",
            }
        ]
    }

    result = await timelogs_api_instance.get_all(project_id=123)

    assert len(result) == 1
    assert result[0].id == 201
    fake_api_client.get.assert_awaited_once_with(
        "/portal/test_portal/projects/123/timelogs",
        params={
            "page": 1,
            "per_page": 200,
            "view_type": "customdate",
            "module": '{"type": "task"}',
        },
    )


@pytest.mark.asyncio
async def test_get_all_invalid_project_id(
    timelogs_api_instance: TimelogsAPI,
) -> None:
    with pytest.raises(ValueError):
        await timelogs_api_instance.get_all(project_id=0)


@pytest.mark.asyncio
async def test_get_all_per_page_too_large(
    timelogs_api_instance: TimelogsAPI,
) -> None:
    with pytest.raises(ValueError):
        await timelogs_api_instance.get_all(project_id=123, per_page=201)


@pytest.mark.asyncio
async def test_get_all_wraps_generic_exception(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.get.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await timelogs_api_instance.get_all(project_id=123)

    fake_api_client.get.side_effect = Exception("bad response")

    with pytest.raises(ZohoProjectsException, match="Failed to fetch timelogs"):
        await timelogs_api_instance.get_all(project_id=123)


@pytest.mark.asyncio
async def test_get_report_with_log_details_structure(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.get.return_value = {
        "time_logs": [
            {
                "log_details": [
                    {
                        "id": 301,
                        "date": "2024-02-01",
                        "log_hour": "01:15",
                    }
                ]
            }
        ]
    }

    filters = TimelogFilters(
        view_type="date",
        start_date="2024-02-01",
        end_date="2024-02-28",
        module="task",
        filter_params={"group_by": "owner"},
    )
    params = TimelogRequestParams(
        project_id=123,
        page=3,
        per_page=150,
        filters=filters,
    )
    result = await timelogs_api_instance.get_report(
        params=params,
        report_type="user",
    )

    assert len(result) == 1
    assert result[0].id == 301

    fake_api_client.get.assert_awaited_once()
    awaited_args, awaited_kwargs = fake_api_client.get.await_args
    assert awaited_args == ("/portal/test_portal/projects/123/timelogs/report",)

    params = awaited_kwargs["params"]
    assert params["page"] == 3
    assert params["per_page"] == 150
    assert params["report_type"] == "user"
    assert params["view_type"] == "date"
    assert params["start_date"] == "2024-02-01"
    assert params["end_date"] == "2024-02-28"
    assert params["group_by"] == "owner"
    assert params["module"] == '{"type": "task"}'


@pytest.mark.asyncio
async def test_get_report_direct_timelogs_structure(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.get.return_value = {
        "timelogs": [{"id": 302, "date": "2024-02-15", "log_hour": "02:45"}]
    }

    params = TimelogRequestParams(project_id=123)
    result = await timelogs_api_instance.get_report(params=params)

    assert len(result) == 1
    assert result[0].id == 302
    fake_api_client.get.assert_awaited_once_with(
        "/portal/test_portal/projects/123/timelogs/report",
        params={
            "page": 1,
            "per_page": 200,
            "report_type": "user",
            "view_type": "customdate",
            "module": '{"type": "task"}',
        },
    )


@pytest.mark.asyncio
async def test_get_report_wraps_generic_exception(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.get.side_effect = RuntimeError("report boom")

    with pytest.raises(RuntimeError):
        params = TimelogRequestParams(project_id=123)
        await timelogs_api_instance.get_report(params=params)

    fake_api_client.get.side_effect = Exception("bad report")

    with pytest.raises(ZohoProjectsException, match="Failed to fetch timelog report"):
        params = TimelogRequestParams(project_id=123)
        await timelogs_api_instance.get_report(params=params)


@pytest.mark.asyncio
async def test_get_report_input_validation(
    timelogs_api_instance: TimelogsAPI,
) -> None:
    with pytest.raises(ValueError):
        params = TimelogRequestParams(project_id=0)
        await timelogs_api_instance.get_report(params=params)

    with pytest.raises(ValueError):
        params = TimelogRequestParams(project_id=1, per_page=500)
        await timelogs_api_instance.get_report(params=params)


@pytest.mark.asyncio
async def test_get_input_validation(
    timelogs_api_instance: TimelogsAPI,
) -> None:
    with pytest.raises(ValueError):
        params = TimelogOperationParams(project_id=0, timelog_id=1)
        await timelogs_api_instance.get(params=params)

    with pytest.raises(ValueError):
        params = TimelogOperationParams(project_id=1, timelog_id=0)
        await timelogs_api_instance.get(params=params)


@pytest.mark.asyncio
async def test_get_returns_timelog_when_present(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.get.return_value = {
        "timelog": {
            "id": 500,
            "project_id": 123,
            "date": "2024-01-10",
            "log_hour": "04:30",
        }
    }

    params = TimelogOperationParams(project_id=123, timelog_id=500)
    timelog = await timelogs_api_instance.get(params=params)

    assert timelog.id == 500
    assert timelog.project_id == 123


@pytest.mark.asyncio
async def test_get_returns_default_when_missing(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.get.return_value = {}

    params = TimelogOperationParams(project_id=123, timelog_id=42)
    timelog = await timelogs_api_instance.get(params=params)

    assert timelog.id == 42
    assert timelog.log_hour == "00:00"


@pytest.mark.asyncio
async def test_create_returns_api_response(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    payload = TimeLog(
        id=1,
        date="2024-01-01",
        log_hour="01:00",
    )

    fake_api_client.post.return_value = {
        "timelog": {
            "id": 10,
            "date": "2024-01-01",
            "log_hour": "01:00",
        }
    }

    created = await timelogs_api_instance.create(project_id=321, timelog_data=payload)

    assert created.id == 10
    fake_api_client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_returns_payload_when_missing_response(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    payload = TimeLog(
        id=2,
        date="2024-01-02",
        log_hour="02:00",
    )

    fake_api_client.post.return_value = {}

    created = await timelogs_api_instance.create(project_id=123, timelog_data=payload)

    assert created == payload


@pytest.mark.asyncio
async def test_update_returns_api_response(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    payload = TimeLog(
        id=3,
        date="2024-01-03",
        log_hour="03:00",
    )

    fake_api_client.patch.return_value = {
        "timelog": {
            "id": 3,
            "date": "2024-01-03",
            "log_hour": "03:30",
        }
    }

    updated = await timelogs_api_instance.update(
        project_id=111, timelog_id=3, timelog_data=payload
    )

    assert updated.log_hour == "03:30"


@pytest.mark.asyncio
async def test_update_returns_payload_when_missing_response(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    payload = TimeLog(
        id=4,
        date="2024-01-04",
        log_hour="04:00",
    )

    fake_api_client.patch.return_value = {}

    updated = await timelogs_api_instance.update(
        project_id=111, timelog_id=4, timelog_data=payload
    )

    assert updated == payload


@pytest.mark.asyncio
async def test_update_input_validation(timelogs_api_instance: TimelogsAPI) -> None:
    payload = TimeLog(id=1, date="2024-01-01", log_hour="01:00")

    with pytest.raises(ValueError):
        await timelogs_api_instance.update(
            project_id=0, timelog_id=1, timelog_data=payload
        )

    with pytest.raises(ValueError):
        await timelogs_api_instance.update(
            project_id=1, timelog_id=0, timelog_data=payload
        )


@pytest.mark.asyncio
async def test_delete_invokes_api_and_returns_true(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    result = await timelogs_api_instance.delete(project_id=222, timelog_id=5)

    assert result is True
    fake_api_client.delete.assert_awaited_once_with(
        "/portal/test_portal/projects/222/timelogs/5"
    )


@pytest.mark.asyncio
async def test_delete_input_validation(timelogs_api_instance: TimelogsAPI) -> None:
    with pytest.raises(ValueError):
        await timelogs_api_instance.delete(project_id=0, timelog_id=1)

    with pytest.raises(ValueError):
        await timelogs_api_instance.delete(project_id=1, timelog_id=0)


@pytest.mark.asyncio
async def test_bulk_create_returns_api_response(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    payloads = [
        TimeLog(id=1, date="2024-01-01", log_hour="01:00"),
        TimeLog(id=2, date="2024-01-02", log_hour="02:00"),
    ]

    fake_api_client.post.return_value = {
        "timelogs": [
            {"id": 1, "date": "2024-01-01", "log_hour": "01:00"},
            {"id": 2, "date": "2024-01-02", "log_hour": "02:00"},
        ]
    }

    timelogs = await timelogs_api_instance.bulk_create(
        project_id=55, timelogs_data=payloads
    )

    assert [timelog.id for timelog in timelogs] == [1, 2]
    fake_api_client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_bulk_create_returns_original_when_missing_response(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    payloads = [TimeLog(id=10, date="2024-01-01", log_hour="01:00")]

    fake_api_client.post.return_value = {}

    timelogs = await timelogs_api_instance.bulk_create(
        project_id=55, timelogs_data=payloads
    )

    assert timelogs == payloads


@pytest.mark.asyncio
async def test_bulk_create_wraps_exception(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    payloads = [TimeLog(id=1, date="2024-01-01", log_hour="01:00")]
    fake_api_client.post.side_effect = Exception("bulk create failed")

    with pytest.raises(ZohoProjectsException, match="Failed to bulk create timelogs"):
        await timelogs_api_instance.bulk_create(project_id=55, timelogs_data=payloads)


@pytest.mark.asyncio
async def test_bulk_update_returns_api_response(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    payloads = [TimeLog(id=1, date="2024-01-01", log_hour="01:00")]

    fake_api_client.patch.return_value = {
        "timelogs": [
            {
                "id": 1,
                "date": "2024-01-01",
                "log_hour": "01:30",
            }
        ]
    }

    timelogs = await timelogs_api_instance.bulk_update(
        project_id=77, timelogs_data=payloads
    )

    assert timelogs[0].log_hour == "01:30"


@pytest.mark.asyncio
async def test_bulk_update_returns_original_when_missing_response(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    payloads = [TimeLog(id=1, date="2024-01-01", log_hour="01:00")]

    fake_api_client.patch.return_value = {}

    timelogs = await timelogs_api_instance.bulk_update(
        project_id=77, timelogs_data=payloads
    )

    assert timelogs == payloads


@pytest.mark.asyncio
async def test_bulk_update_wraps_exception(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    payloads = [TimeLog(id=1, date="2024-01-01", log_hour="01:00")]
    fake_api_client.patch.side_effect = Exception("bulk update failed")

    with pytest.raises(ZohoProjectsException, match="Failed to bulk update timelogs"):
        await timelogs_api_instance.bulk_update(project_id=77, timelogs_data=payloads)


@pytest.mark.asyncio
async def test_bulk_delete_calls_delete_for_each_id(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    result = await timelogs_api_instance.bulk_delete(project_id=42, timelog_ids=[7, 8])

    assert result is True
    fake_api_client.delete.assert_has_awaits(
        [
            (("/portal/test_portal/projects/42/timelogs/7",), {}),
            (("/portal/test_portal/projects/42/timelogs/8",), {}),
        ]
    )


@pytest.mark.asyncio
async def test_bulk_delete_wraps_exception(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.delete.side_effect = Exception("bulk delete failed")

    with pytest.raises(ZohoProjectsException, match="Failed to bulk delete timelogs"):
        await timelogs_api_instance.bulk_delete(project_id=42, timelog_ids=[1])


@pytest.mark.asyncio
async def test_approve_timelog_returns_timelog_when_present(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.post.return_value = {
        "timelog": {
            "id": 9,
            "project_id": 12,
            "date": "2024-01-09",
            "log_hour": "01:45",
        }
    }

    timelog = await timelogs_api_instance.approve_timelog(project_id=12, timelog_id=9)

    assert timelog.id == 9
    fake_api_client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_approve_timelog_returns_default_when_missing_response(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.post.return_value = {}

    timelog = await timelogs_api_instance.approve_timelog(project_id=12, timelog_id=9)

    assert timelog.id == 9
    assert timelog.log_hour == "00:00"


@pytest.mark.asyncio
async def test_approve_timelog_input_validation(
    timelogs_api_instance: TimelogsAPI,
) -> None:
    with pytest.raises(ValueError):
        await timelogs_api_instance.approve_timelog(project_id=0, timelog_id=1)

    with pytest.raises(ValueError):
        await timelogs_api_instance.approve_timelog(project_id=1, timelog_id=0)


@pytest.mark.asyncio
async def test_reject_timelog_returns_timelog_when_present(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.post.return_value = {
        "timelog": {
            "id": 11,
            "project_id": 34,
            "date": "2024-01-11",
            "log_hour": "02:15",
        }
    }

    timelog = await timelogs_api_instance.reject_timelog(project_id=34, timelog_id=11)

    assert timelog.id == 11


@pytest.mark.asyncio
async def test_reject_timelog_returns_default_when_missing_response(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.post.return_value = {}

    timelog = await timelogs_api_instance.reject_timelog(project_id=34, timelog_id=11)

    assert timelog.id == 11
    assert timelog.log_hour == "00:00"


@pytest.mark.asyncio
async def test_reject_timelog_input_validation(
    timelogs_api_instance: TimelogsAPI,
) -> None:
    with pytest.raises(ValueError):
        await timelogs_api_instance.reject_timelog(project_id=0, timelog_id=1)

    with pytest.raises(ValueError):
        await timelogs_api_instance.reject_timelog(project_id=1, timelog_id=0)


@pytest.mark.asyncio
async def test_create_raises_when_project_id_invalid(
    timelogs_api_instance: TimelogsAPI,
) -> None:
    payload = TimeLog(id=1, date="2024-01-01", log_hour="01:00")

    with pytest.raises(ValueError):
        await timelogs_api_instance.create(project_id=0, timelog_data=payload)


@pytest.mark.asyncio
async def test_bulk_operations_input_validation(
    timelogs_api_instance: TimelogsAPI,
) -> None:
    payload = TimeLog(id=1, date="2024-01-01", log_hour="01:00")

    with pytest.raises(ValueError):
        await timelogs_api_instance.bulk_create(project_id=0, timelogs_data=[payload])

    with pytest.raises(ValueError):
        await timelogs_api_instance.bulk_create(project_id=1, timelogs_data=[])

    with pytest.raises(ValueError):
        await timelogs_api_instance.bulk_update(project_id=0, timelogs_data=[payload])

    with pytest.raises(ValueError):
        await timelogs_api_instance.bulk_update(project_id=1, timelogs_data=[])

    with pytest.raises(ValueError):
        await timelogs_api_instance.bulk_delete(project_id=0, timelog_ids=[1])

    with pytest.raises(ValueError):
        await timelogs_api_instance.bulk_delete(project_id=1, timelog_ids=[])


@pytest.mark.asyncio
async def test_actions_wrap_exceptions(
    timelogs_api_instance: TimelogsAPI, fake_api_client: SimpleNamespace
) -> None:
    fake_api_client.post.side_effect = Exception("create failed")

    payload = TimeLog(id=1, date="2024-01-01", log_hour="01:00")

    with pytest.raises(ZohoProjectsException, match="Failed to create timelog"):
        await timelogs_api_instance.create(project_id=1, timelog_data=payload)

    fake_api_client.post.side_effect = Exception("approve failed")
    with pytest.raises(ZohoProjectsException, match="Failed to approve timelog"):
        await timelogs_api_instance.approve_timelog(project_id=1, timelog_id=1)

    fake_api_client.post.side_effect = Exception("reject failed")
    with pytest.raises(ZohoProjectsException, match="Failed to reject timelog"):
        await timelogs_api_instance.reject_timelog(project_id=1, timelog_id=1)

    fake_api_client.patch.side_effect = Exception("update failed")
    with pytest.raises(ZohoProjectsException, match="Failed to update timelog"):
        await timelogs_api_instance.update(
            project_id=1, timelog_id=1, timelog_data=payload
        )

    fake_api_client.post.side_effect = None
    fake_api_client.patch.side_effect = None
    fake_api_client.delete.side_effect = Exception("delete failed")
    with pytest.raises(ZohoProjectsException, match="Failed to delete timelog"):
        await timelogs_api_instance.delete(project_id=1, timelog_id=1)

    fake_api_client.post.side_effect = None
    fake_api_client.patch.side_effect = None
    fake_api_client.delete.side_effect = None
    fake_api_client.get.side_effect = Exception("get failed")
    with pytest.raises(ZohoProjectsException, match="Failed to fetch timelog"):
        params = TimelogOperationParams(project_id=1, timelog_id=1)
        await timelogs_api_instance.get(params=params)
