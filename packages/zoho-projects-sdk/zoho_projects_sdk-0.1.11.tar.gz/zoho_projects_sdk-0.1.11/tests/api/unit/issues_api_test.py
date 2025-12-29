from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from zoho_projects_sdk.api.issues import IssuesAPI, ListParams
from zoho_projects_sdk.models.issue_models import (
    Issue,
    IssueCreateRequest,
    IssueUpdateRequest,
)


def test_portal_id_missing_raises_value_error() -> None:
    client = SimpleNamespace(portal_id=None)
    issues_api = IssuesAPI(client)

    with pytest.raises(ValueError, match="Portal ID is not configured"):
        _ = issues_api._portal_id


def test_serialize_payload_from_pydantic_model_filters_none() -> None:
    payload = IssuesAPI._serialize_payload(
        IssueCreateRequest(name="Critical bug", attachments=None, severity=None)
    )

    assert payload == {"name": "Critical bug"}


def test_serialize_payload_with_model_dump_filters_none() -> None:
    class ModelDumpOnly:
        def model_dump(
            self, *, by_alias: bool, exclude_none: bool
        ) -> dict[str, object]:
            assert by_alias is True
            assert exclude_none is True
            return {"title": "Bug", "optional": None}

    payload = IssuesAPI._serialize_payload(ModelDumpOnly())

    assert payload == {"title": "Bug"}


def test_serialize_payload_with_mapping_returns_filtered_dict() -> None:
    payload = IssuesAPI._serialize_payload({"title": "Bug", "optional": None})

    assert payload == {"title": "Bug"}


def test_serialize_payload_with_dict_method_excludes_private_fields() -> None:
    class DictMethodOnly:
        def dict(self) -> dict[str, object]:
            return {"title": "Bug", "_secret": "hidden", "optional": None}

    payload = IssuesAPI._serialize_payload(DictMethodOnly())

    assert payload == {"title": "Bug"}


def test_serialize_payload_with_object_attrs_excludes_private_fields() -> None:
    class HasAttrs:
        def __init__(self) -> None:
            self.title = "Bug"
            self._private = "ignore"
            self.optional = None

    payload = IssuesAPI._serialize_payload(HasAttrs())

    assert payload == {"title": "Bug"}


def test_serialize_payload_rejects_unsupported_types() -> None:
    with pytest.raises(TypeError):
        IssuesAPI._serialize_payload(42)


def test_serialize_payload_with_mapping_subclass() -> None:
    class MappingSubclass(dict[str, object]):
        pass

    payload = IssuesAPI._serialize_payload(MappingSubclass(title="Bug", optional=None))

    assert payload == {"title": "Bug"}


def test_serialize_payload_with_object_attrs_filters_private_and_none() -> None:
    class AttrOnly:
        def __init__(self) -> None:
            self.visible = "value"
            self._private = "hidden"
            self.none_field = None

    payload = IssuesAPI._serialize_payload(AttrOnly())

    assert payload == {"visible": "value"}


def test_serialize_payload_with_model_dump_non_dict_falls_back_to_attrs() -> None:
    class ModelDumpList:
        def __init__(self) -> None:
            self.visible = "value"

        def model_dump(self, *, by_alias: bool, exclude_none: bool) -> list[str]:
            return ["not", "dict"]

    payload = IssuesAPI._serialize_payload(ModelDumpList())

    assert payload == {"visible": "value"}


def test_serialize_payload_with_dict_method_non_dict_falls_back_to_attrs() -> None:
    class DictMethodList:
        def __init__(self) -> None:
            self.visible = "value"

        def dict(self) -> list[str]:
            return ["not", "dict"]

    payload = IssuesAPI._serialize_payload(DictMethodList())

    assert payload == {"visible": "value"}


@pytest.mark.asyncio
async def test_list_by_portal_builds_params_and_returns_issues() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(return_value={"issues": [{"id": 1, "name": "Issue"}]}),
    )

    params = ListParams(
        page=2,
        per_page=5,
        sort_by="created_time",
        view_id="open",
        issue_ids="1,2",
        filter_={"status": "open"},
    )
    issues = await IssuesAPI(client).list_by_portal(params=params)

    assert len(issues) == 1
    assert isinstance(issues[0], Issue)
    client.get.assert_awaited_once()
    _, kwargs = client.get.call_args
    assert kwargs["params"] == {
        "page": 2,
        "per_page": 5,
        "sort_by": "created_time",
        "view_id": "open",
        "issue_ids": "1,2",
        "filter": '{"status": "open"}',
    }


@pytest.mark.asyncio
async def test_list_by_project_uses_project_endpoint() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(return_value={"issues": [{"id": 2, "name": "Issue"}]}),
    )

    params = ListParams(page=1, per_page=10, filter_="status:open")
    issues = await IssuesAPI(client).list_by_project(project_id="proj", params=params)

    assert len(issues) == 1
    assert isinstance(issues[0], Issue)
    client.get.assert_awaited_once_with(
        "/portal/portal-123/projects/proj/issues",
        params={"page": 1, "per_page": 10, "filter": "status:open"},
    )


@pytest.mark.asyncio
async def test_get_returns_constructed_issue_when_empty() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(return_value={"issues": []}),
    )

    issue = await IssuesAPI(client).get(project_id="proj", issue_id="issue")

    assert isinstance(issue, Issue)
    assert issue.id is None
    client.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_returns_first_issue_when_present() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(return_value={"issues": [{"id": 99, "name": "Issue"}]}),
    )

    issue = await IssuesAPI(client).get(project_id="proj", issue_id="issue")

    assert isinstance(issue, Issue)
    assert issue.id == 99
    client.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_prefers_issue_key_in_response() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        post=AsyncMock(return_value={"issue": {"id": 5, "name": "Bug"}}),
    )
    payload = IssueCreateRequest(name="Bug")

    issue = await IssuesAPI(client).create(project_id="proj", issue_data=payload)

    assert isinstance(issue, Issue)
    assert issue.id == 5
    client.post.assert_awaited_once_with(
        "/portal/portal-123/projects/proj/issues",
        json={"name": "Bug"},
    )


@pytest.mark.asyncio
async def test_create_uses_issue_key() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        post=AsyncMock(return_value={"issue": {"id": 6, "name": "Issue"}}),
    )

    issue = await IssuesAPI(client).create(
        project_id="proj", issue_data={"name": "Issue"}
    )

    assert isinstance(issue, Issue)
    assert issue.id == 6


@pytest.mark.asyncio
async def test_update_returns_issue() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        patch=AsyncMock(return_value={"issue": {"id": 7, "name": "Updated"}}),
    )
    payload = IssueUpdateRequest(name="Updated")

    issue = await IssuesAPI(client).update(
        project_id="proj",
        issue_id="issue",
        issue_data=payload,
    )

    assert isinstance(issue, Issue)
    assert issue.id == 7
    client.patch.assert_awaited_once_with(
        "/portal/portal-123/projects/proj/issues/issue",
        json={"name": "Updated"},
    )


@pytest.mark.asyncio
async def test_delete_calls_client_and_returns_true() -> None:
    client = SimpleNamespace(portal_id="portal-123", delete=AsyncMock())

    result = await IssuesAPI(client).delete(project_id="proj", issue_id="issue")

    assert result is True
    client.delete.assert_awaited_once_with(
        "/portal/portal-123/projects/proj/issues/issue"
    )


@pytest.mark.asyncio
async def test_get_all_delegates_to_list_by_project() -> None:
    client = SimpleNamespace(
        portal_id="portal-123",
        get=AsyncMock(return_value={"issues": []}),
    )

    issues = await IssuesAPI(client).get_all(project_id="proj", page=3, per_page=7)

    assert issues == []
    client.get.assert_awaited_once_with(
        "/portal/portal-123/projects/proj/issues",
        params={"page": 3, "per_page": 7},
    )


def test_build_list_params_handles_none_and_strings() -> None:
    list_params = ListParams(
        page=1,
        per_page=50,
        sort_by=None,
        view_id=None,
        issue_ids=None,
        filter_="status:open",
    )
    params = IssuesAPI._build_list_params(list_params)

    assert params == {"page": 1, "per_page": 50, "filter": "status:open"}

    list_params = ListParams(
        page=3,
        per_page=25,
        sort_by="priority",
        view_id="high",
        issue_ids="1,2,3",
        filter_={"severity": "high"},
    )
    params = IssuesAPI._build_list_params(list_params)

    assert params == {
        "page": 3,
        "per_page": 25,
        "sort_by": "priority",
        "view_id": "high",
        "issue_ids": "1,2,3",
        "filter": '{"severity": "high"}',
    }
