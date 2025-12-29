"""Unit tests for Issue Pydantic model behaviour."""

from zoho_projects_sdk.models import Issue
from zoho_projects_sdk.models.issue_models import IssueCreateRequest, IssueUpdateRequest


def test_issue_accepts_title_alias_and_optional_fields() -> None:
    payload = {
        "id": 101,
        "title": "Critical issue",
        "status": {"name": "Open"},
        "severity": "High",
        "attachments": [1, 2],
        "tags": ["backend"],
    }

    bug = Issue.model_validate(payload)

    assert bug.id == 101
    assert bug.name == "Critical issue"
    assert bug.status == {"name": "Open"}
    assert bug.attachments == [1, 2]
    assert bug.tags == ["backend"]


def test_issue_title_property_returns_name() -> None:
    bug = Issue(id=2, name="UI Bug")

    assert bug.title == "UI Bug"


def test_issue_normalises_associated_teams_when_dict() -> None:
    payload = {
        "id": 123,
        "name": "Issue",
        "associated_teams": {"id": "team-1", "name": "Song Division"},
    }

    issue = Issue.model_validate(payload)

    assert issue.associated_teams == [{"id": "team-1", "name": "Song Division"}]


def test_issue_allows_associated_teams_none() -> None:
    payload = {"id": 124, "name": "Issue", "associated_teams": None}

    issue = Issue.model_validate(payload)

    assert issue.associated_teams is None


def test_issue_leaves_associated_teams_list_unchanged() -> None:
    payload = {
        "id": 125,
        "name": "Issue",
        "associated_teams": [{"id": "team-1", "name": "Song Division"}],
    }

    issue = Issue.model_validate(payload)

    assert issue.associated_teams == [{"id": "team-1", "name": "Song Division"}]


def test_issue_create_request_allows_associated_teams_none() -> None:
    request = IssueCreateRequest(name="Issue", associated_teams=None)

    assert request.associated_teams is None


def test_issue_create_request_normalises_associated_teams_when_dict() -> None:
    request = IssueCreateRequest(
        name="Issue",
        associated_teams={"id": "team-1", "name": "Song Division"},
    )

    assert request.associated_teams == [{"id": "team-1", "name": "Song Division"}]


def test_issue_create_request_leaves_associated_teams_list_unchanged() -> None:
    request = IssueCreateRequest(
        name="Issue",
        associated_teams=[{"id": "team-1", "name": "Song Division"}],
    )

    assert request.associated_teams == [{"id": "team-1", "name": "Song Division"}]


def test_issue_update_request_allows_associated_teams_none() -> None:
    request = IssueUpdateRequest(associated_teams=None)

    assert request.associated_teams is None


def test_issue_update_request_normalises_associated_teams_when_dict() -> None:
    request = IssueUpdateRequest(
        associated_teams={"id": "team-1", "name": "Song Division"}
    )

    assert request.associated_teams == [{"id": "team-1", "name": "Song Division"}]


def test_issue_update_request_leaves_associated_teams_list_unchanged() -> None:
    request = IssueUpdateRequest(
        associated_teams=[{"id": "team-1", "name": "Song Division"}]
    )

    assert request.associated_teams == [{"id": "team-1", "name": "Song Division"}]
