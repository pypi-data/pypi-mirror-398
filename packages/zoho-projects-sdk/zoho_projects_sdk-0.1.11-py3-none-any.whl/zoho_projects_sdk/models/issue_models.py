"""Pydantic models for Zoho Projects Issues."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from pydantic import AliasChoices, BaseModel, Field, field_validator
from pydantic.config import ConfigDict


class IssueReference(BaseModel):
    """Generic lightweight reference object that wraps an issue relation ID."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[Union[int, str]] = Field(None, alias="id")


class IssueAssignee(BaseModel):
    """Represents the assignee payload accepted by the Issues API."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    zpuid: Optional[Union[int, str]] = Field(None, alias="zpuid")
    id: Optional[Union[int, str]] = Field(None, alias="id")


class IssueReminder(BaseModel):
    """Reminder configuration for issues."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    type: Optional[str] = Field(None, alias="type")
    reminder_custom_date: Optional[str] = Field(None, alias="reminder_custom_date")
    days_before: Optional[Union[int, str]] = Field(None, alias="days_before")
    time: Optional[str] = Field(None, alias="time")
    notify_users: Optional[Sequence[Union[int, str, Dict[str, Any]]]] = Field(
        None, alias="notify_users"
    )


class IssueTagMutation(BaseModel):
    """Describe tag additions or removals supported in update calls."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    add: Optional[Sequence[Union[int, str, Dict[str, Any]]]] = Field(None, alias="add")
    remove: Optional[Sequence[Union[int, str, Dict[str, Any]]]] = Field(
        None, alias="remove"
    )
    id: Optional[Union[int, str]] = Field(None, alias="id")


IssueTagsUpdate = Union[
    IssueTagMutation,
    Dict[str, Any],
    Sequence[Union[int, str]],
    Sequence[Dict[str, Any]],
]


class Issue(BaseModel):
    """A Pydantic model representing an Issue in Zoho Projects."""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="allow",
    )

    id: Optional[Union[int, str]] = Field(None, alias="id")
    name: Optional[str] = Field(
        None,
        alias="name",
        validation_alias=AliasChoices("name", "title"),
    )
    description: Optional[str] = Field(None, alias="description")
    status: Optional[Union[str, Dict[str, Any], IssueReference]] = Field(
        None, alias="status"
    )
    priority: Optional[str] = Field(None, alias="priority")
    severity: Optional[Union[str, Dict[str, Any], IssueReference]] = Field(
        None, alias="severity"
    )
    resolution: Optional[str] = Field(None, alias="resolution")
    created_time: Optional[str] = Field(None, alias="created_time")
    updated_time: Optional[str] = Field(None, alias="updated_time")
    project_id: Optional[Union[int, str]] = Field(None, alias="project_id")
    task_id: Optional[Union[int, str]] = Field(None, alias="task_id")
    flag: Optional[str] = Field(None, alias="flag")
    due_date: Optional[str] = Field(None, alias="due_date")
    release_milestone: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="release_milestone"
    )
    affected_milestone: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="affected_milestone"
    )
    classification: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="classification"
    )
    module: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="module"
    )
    assignee: Optional[Union[Dict[str, Any], IssueAssignee]] = Field(
        None, alias="assignee"
    )
    reporter: Optional[Dict[str, Any]] = Field(None, alias="reporter")
    is_it_reproducible: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="is_it_reproducible"
    )
    attachments: Optional[Sequence[Union[int, str, Dict[str, Any]]]] = Field(
        None, alias="attachments"
    )
    tags: Optional[IssueTagsUpdate] = Field(None, alias="tags")
    associated_teams: Optional[Sequence[Union[Dict[str, Any], IssueReference]]] = Field(
        None, alias="associated_teams"
    )
    followers: Optional[Sequence[Union[int, str, Dict[str, Any]]]] = Field(
        None, alias="followers"
    )
    reminder: Optional[Union[Dict[str, Any], IssueReminder]] = Field(
        None, alias="reminder"
    )
    rate_per_hour: Optional[Union[int, float]] = Field(None, alias="rate_per_hour")
    cost_rate_per_hour: Optional[Union[int, float]] = Field(
        None, alias="cost_rate_per_hour"
    )

    @field_validator("associated_teams", mode="before")
    @classmethod
    def _normalise_associated_teams(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (dict, IssueReference)):
            return [value]
        return value

    @property
    def title(self) -> Optional[str]:
        """Alias for the issue name to mirror API field terminology."""

        return self.name


class IssueCreateRequest(BaseModel):
    """Payload for creating an issue via the API."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    name: str = Field(alias="name")
    description: Optional[str] = Field(None, alias="description")
    flag: Optional[str] = Field(None, alias="flag")
    associated_teams: Optional[Sequence[Union[Dict[str, Any], IssueReference]]] = Field(
        None, alias="associated_teams"
    )
    assignee: Optional[Union[Dict[str, Any], IssueAssignee]] = Field(
        None, alias="assignee"
    )
    status: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="status"
    )
    due_date: Optional[str] = Field(None, alias="due_date")
    release_milestone: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="release_milestone"
    )
    affected_milestone: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="affected_milestone"
    )
    severity: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="severity"
    )
    is_it_reproducible: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="is_it_reproducible"
    )
    classification: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="classification"
    )
    module: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="module"
    )
    attachments: Optional[Sequence[Union[int, str, Dict[str, Any]]]] = Field(
        None, alias="attachments"
    )
    tags: Optional[IssueTagsUpdate] = Field(None, alias="tags")
    followers: Optional[Sequence[Union[int, str, Dict[str, Any]]]] = Field(
        None, alias="followers"
    )
    reminder: Optional[Union[Dict[str, Any], IssueReminder]] = Field(
        None, alias="reminder"
    )
    rate_per_hour: Optional[Union[int, float]] = Field(None, alias="rate_per_hour")
    cost_rate_per_hour: Optional[Union[int, float]] = Field(
        None, alias="cost_rate_per_hour"
    )

    @field_validator("associated_teams", mode="before")
    @classmethod
    def _normalise_associated_teams(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (dict, IssueReference)):
            return [value]
        return value


class IssueUpdateRequest(BaseModel):
    """Payload for updating an issue via the API."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    name: Optional[str] = Field(None, alias="name")
    description: Optional[str] = Field(None, alias="description")
    flag: Optional[str] = Field(None, alias="flag")
    associated_teams: Optional[
        Union[None, Sequence[Union[Dict[str, Any], IssueReference]]]
    ] = Field(None, alias="associated_teams")
    assignee: Optional[Union[Dict[str, Any], IssueAssignee]] = Field(
        None, alias="assignee"
    )
    status: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="status"
    )
    due_date: Optional[str] = Field(None, alias="due_date")
    tags: Optional[IssueTagsUpdate] = Field(None, alias="tags")
    release_milestone: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="release_milestone"
    )
    affected_milestone: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="affected_milestone"
    )
    severity: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="severity"
    )
    is_it_reproducible: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="is_it_reproducible"
    )
    classification: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="classification"
    )
    module: Optional[Union[Dict[str, Any], IssueReference]] = Field(
        None, alias="module"
    )
    rate_per_hour: Optional[Union[int, float]] = Field(None, alias="rate_per_hour")
    cost_rate_per_hour: Optional[Union[int, float]] = Field(
        None, alias="cost_rate_per_hour"
    )
    reminder: Optional[Union[Dict[str, Any], IssueReminder]] = Field(
        None, alias="reminder"
    )
    followers: Optional[Union[Sequence[Union[int, str]], Dict[str, Any]]] = Field(
        None, alias="followers"
    )

    @field_validator("associated_teams", mode="before")
    @classmethod
    def _normalise_associated_teams(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (dict, IssueReference)):
            return [value]
        return value
