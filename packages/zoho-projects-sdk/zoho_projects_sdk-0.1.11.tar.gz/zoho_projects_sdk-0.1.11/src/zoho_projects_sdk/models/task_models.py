"""Pydantic models for Zoho Projects task entities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class TaskOwner(BaseModel):
    """Represents an owner entry within a task."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    zpuid: Optional[str] = Field(None, alias="zpuid")
    zuid: Optional[Union[int, str]] = Field(None, alias="zuid")
    name: Optional[str] = Field(None, alias="name")
    email: Optional[str] = Field(None, alias="email")
    first_name: Optional[str] = Field(None, alias="first_name")
    last_name: Optional[str] = Field(None, alias="last_name")
    work_values: Optional[str] = Field(None, alias="work_values")


class TaskStatus(BaseModel):
    """Represents the status metadata returned for a task."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[Union[int, str]] = Field(None, alias="id")
    name: Optional[str] = Field(None, alias="name")
    color: Optional[str] = Field(None, alias="color")
    color_hexcode: Optional[str] = Field(None, alias="color_hexcode")
    is_closed_type: Optional[bool] = Field(None, alias="is_closed_type")


class TaskSequence(BaseModel):
    """Represents sequence information for a task."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    sequence: Optional[Union[int, str]] = Field(None, alias="sequence")


class TaskOwnersAndWork(BaseModel):
    """Represents task owner/work allocation details."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    work_type: Optional[str] = Field(None, alias="work_type")
    total_work: Optional[str] = Field(None, alias="total_work")
    unit: Optional[str] = Field(None, alias="unit")
    copy_task_duration: Optional[bool] = Field(None, alias="copy_task_duration")
    owners: Optional[List[TaskOwner]] = Field(default=None, alias="owners")


class TaskDuration(BaseModel):
    """Represents the duration metadata for a task."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    value: Optional[Union[int, str, float]] = Field(None, alias="value")
    type: Optional[str] = Field(None, alias="type")


TaskStatusType = Union[TaskStatus, Dict[str, Any], str]


class Task(BaseModel):
    """A Pydantic model representing a task in Zoho Projects."""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="allow",
    )

    id: Optional[Union[int, str]] = Field(None, alias="id")
    prefix: Optional[str] = Field(None, alias="prefix")
    name: Optional[str] = Field(None, alias="name")
    description: Optional[str] = Field(None, alias="description")
    status: Optional[TaskStatusType] = Field(None, alias="status")
    priority: Optional[str] = Field(None, alias="priority")
    tasklist: Optional[Dict[str, Any]] = Field(None, alias="tasklist")
    tasklist_id: Optional[Union[int, str]] = Field(None, alias="tasklist_id")
    owners_and_work: Optional[Union[TaskOwnersAndWork, Dict[str, Any]]] = Field(
        None, alias="owners_and_work"
    )
    duration: Optional[Union[TaskDuration, Dict[str, Any]]] = Field(
        None, alias="duration"
    )
    completion_percentage: Optional[Union[int, str]] = Field(
        None, alias="completion_percentage"
    )
    sequence: Optional[Union[TaskSequence, Dict[str, Any]]] = Field(
        None, alias="sequence"
    )
    depth: Optional[Union[int, str]] = Field(None, alias="depth")
    created_time: Optional[str] = Field(None, alias="created_time")
    last_modified_time: Optional[str] = Field(None, alias="last_modified_time")
    updated_time: Optional[str] = Field(None, alias="updated_time")
    created_via: Optional[str] = Field(None, alias="created_via")
    created_by: Optional[Dict[str, Any]] = Field(None, alias="created_by")
    is_completed: Optional[bool] = Field(None, alias="is_completed")
    completed: Optional[bool] = Field(None, alias="completed")
    billing_type: Optional[str] = Field(None, alias="billing_type")
    budget_info: Optional[Dict[str, Any]] = Field(None, alias="budget_info")
    start: Optional[str] = Field(None, alias="start")
    end: Optional[str] = Field(None, alias="end")
    start_date: Optional[str] = Field(None, alias="start_date")
    end_date: Optional[str] = Field(None, alias="end_date")
    project_id: Optional[Union[int, str]] = Field(None, alias="project_id")
    assignee: Optional[Dict[str, Any]] = Field(None, alias="assignee")
    tags: Optional[List[Any]] = Field(None, alias="tags")


class TaskCreateRequest(BaseModel):
    """Payload for creating a task via the API."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    tasklist: Dict[str, Any] = Field(alias="tasklist")
    name: str = Field(alias="name")
    parental_info: Optional[Dict[str, Any]] = Field(None, alias="parental_info")
    description: Optional[str] = Field(None, alias="description")
    status: Optional[Dict[str, Any]] = Field(None, alias="status")
    priority: Optional[str] = Field(None, alias="priority")
    start_date: Optional[str] = Field(None, alias="start_date")
    end_date: Optional[str] = Field(None, alias="end_date")
    duration: Optional[Dict[str, Any]] = Field(None, alias="duration")
    completion_percentage: Optional[int] = Field(None, alias="completion_percentage")
    billing_type: Optional[str] = Field(None, alias="billing_type")
    attachments: Optional[List[Any]] = Field(None, alias="attachments")
    owners_and_work: Optional[Dict[str, Any]] = Field(None, alias="owners_and_work")
    tags: Optional[List[Any]] = Field(None, alias="tags")
    teams: Optional[List[Any]] = Field(None, alias="teams")
    recurrence: Optional[Dict[str, Any]] = Field(None, alias="recurrence")
    budget_info: Optional[Dict[str, Any]] = Field(None, alias="budget_info")


class TaskUpdateRequest(BaseModel):
    """Payload for updating a task via the API."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: Optional[Union[int, str]] = Field(None, alias="id")
    tasklist: Optional[Dict[str, Any]] = Field(None, alias="tasklist")
    parental_info: Optional[Dict[str, Any]] = Field(None, alias="parental_info")
    name: Optional[str] = Field(None, alias="name")
    description: Optional[str] = Field(None, alias="description")
    status: Optional[Dict[str, Any]] = Field(None, alias="status")
    priority: Optional[str] = Field(None, alias="priority")
    start_date: Optional[str] = Field(None, alias="start_date")
    end_date: Optional[str] = Field(None, alias="end_date")
    duration: Optional[Dict[str, Any]] = Field(None, alias="duration")
    completion_percentage: Optional[int] = Field(None, alias="completion_percentage")
    billing_type: Optional[str] = Field(None, alias="billing_type")
    attachments: Optional[List[Any]] = Field(None, alias="attachments")
    owners_and_work: Optional[Dict[str, Any]] = Field(None, alias="owners_and_work")
    tags: Optional[List[Any]] = Field(None, alias="tags")
    teams: Optional[List[Any]] = Field(None, alias="teams")
    recurrence: Optional[Dict[str, Any]] = Field(None, alias="recurrence")
    reminder: Optional[Dict[str, Any]] = Field(None, alias="reminder")
    budget_info: Optional[Dict[str, Any]] = Field(None, alias="budget_info")
    remove_dependency_lag: Optional[bool] = Field(None, alias="remove_dependency_lag")
