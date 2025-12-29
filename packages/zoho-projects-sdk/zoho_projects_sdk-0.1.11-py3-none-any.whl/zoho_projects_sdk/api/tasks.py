"""API methods for interacting with Zoho Tasks."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Union

from pydantic import BaseModel

from ..models.task_models import Task, TaskCreateRequest, TaskUpdateRequest

if TYPE_CHECKING:
    from ..http_client import ApiClient


class ListParams(BaseModel):
    """Parameters for list operations."""

    page: int = 1
    per_page: int = 20
    filter_: Optional[Union[str, Dict[str, Any]]] = None
    sort_by: Optional[str] = None
    view_id: Optional[Union[int, str]] = None


class TasksAPI:
    """Task endpoint helpers for the Zoho Projects API."""

    def __init__(self, client: "ApiClient"):
        self._client = client

    @property
    def _portal_id(self) -> str:
        portal_id = self._client.portal_id
        if portal_id is None:
            raise ValueError("Portal ID is not configured on the API client")
        return portal_id

    async def list_by_portal(
        self,
        params: Optional[ListParams] = None,
    ) -> List[Task]:
        """Retrieve tasks across the entire portal."""
        params = params or ListParams()
        endpoint = f"/portal/{self._portal_id}/tasks"
        query_params = self._build_list_params(params)
        response_data = await self._client.get(endpoint, params=query_params)
        return [Task.model_validate(task) for task in response_data.get("tasks", [])]

    async def list_by_project(
        self,
        project_id: Union[int, str],
        params: Optional[ListParams] = None,
    ) -> List[Task]:
        """Retrieve tasks scoped to a single project."""
        params = params or ListParams()
        endpoint = f"/portal/{self._portal_id}/projects/{project_id}/tasks"
        query_params = self._build_list_params(params)
        response_data = await self._client.get(endpoint, params=query_params)
        return [Task.model_validate(task) for task in response_data.get("tasks", [])]

    async def get(self, project_id: Union[int, str], task_id: Union[int, str]) -> Task:
        """Fetch details for a specific task within a project."""

        endpoint = f"/portal/{self._portal_id}/projects/{project_id}/tasks/{task_id}"
        response_data = await self._client.get(endpoint)
        tasks_list = response_data.get("tasks", [])
        if tasks_list:
            return Task.model_validate(tasks_list[0])
        return Task.model_construct(id=None)

    async def create(
        self,
        project_id: Union[int, str],
        task_data: Union[TaskCreateRequest, Task, Dict[str, Any]],
    ) -> Task:
        """Create a task within the specified project."""

        endpoint = f"/portal/{self._portal_id}/projects/{project_id}/tasks"
        payload = self._serialize_payload(task_data)
        response_data = await self._client.post(endpoint, json=payload)
        return Task.model_validate(response_data.get("task", {}))

    async def update(
        self,
        project_id: Union[int, str],
        task_id: Union[int, str],
        task_data: Union[TaskUpdateRequest, Task, Dict[str, Any]],
    ) -> Task:
        """Update a task within the specified project."""

        endpoint = f"/portal/{self._portal_id}/projects/{project_id}/tasks/{task_id}"
        payload = self._serialize_payload(task_data)
        response_data = await self._client.patch(endpoint, json=payload)
        return Task.model_validate(response_data.get("task", {}))

    async def delete(
        self, project_id: Union[int, str], task_id: Union[int, str]
    ) -> bool:
        """Delete a task within the specified project."""

        endpoint = f"/portal/{self._portal_id}/projects/{project_id}/tasks/{task_id}"
        await self._client.delete(endpoint)
        return True

    async def clone(
        self,
        project_id: Union[int, str],
        task_id: Union[int, str],
        *,
        no_of_instances: int,
    ) -> Dict[str, Any]:
        """Clone a task within a project."""

        endpoint = (
            f"/portal/{self._portal_id}/projects/{project_id}/tasks/{task_id}/clone"
        )
        payload = {"no_of_instances": no_of_instances}
        response: Dict[str, Any] = await self._client.post(endpoint, json=payload)
        return response

    async def move(
        self,
        project_id: Union[int, str],
        task_id: Union[int, str],
        *,
        target_tasklist_id: Union[int, str],
        status_mapping: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> bool:
        """Move a task to a different task list."""

        endpoint = (
            f"/portal/{self._portal_id}/projects/{project_id}/tasks/{task_id}/move"
        )
        payload: Dict[str, Any] = {"target_tasklist_id": target_tasklist_id}
        if status_mapping:
            payload["status_mapping"] = list(status_mapping)
        await self._client.post(endpoint, json=payload)
        return True

    async def get_associated_bugs(
        self, project_id: Union[int, str], task_id: Union[int, str]
    ) -> List[Dict[str, Any]]:
        """Retrieve bugs associated with a task."""

        endpoint = (
            f"/portal/{self._portal_id}/projects/{project_id}/tasks/{task_id}"
            "/associated-bugs"
        )
        response_data = await self._client.get(endpoint)
        associated: Any = response_data.get("associated_bugs", [])
        if isinstance(associated, list):
            return associated
        return []

    async def associate_bugs(
        self,
        project_id: Union[int, str],
        task_id: Union[int, str],
        bug_ids: Sequence[Union[int, str]],
    ) -> bool:
        """Associate bugs to a task."""

        endpoint = (
            f"/portal/{self._portal_id}/projects/{project_id}/tasks/{task_id}"
            "/associate-bugs"
        )
        payload = {"bug_ids": list(bug_ids)}
        await self._client.post(endpoint, json=payload)
        return True

    async def get_all(
        self,
        project_id: Union[int, str],
        page: int = 1,
        per_page: int = 20,
    ) -> List[Task]:
        """Backward compatibility shim for the previous list method."""
        params = ListParams(page=page, per_page=per_page)
        return await self.list_by_project(project_id, params=params)

    @staticmethod
    def _build_list_params(params: ListParams) -> Dict[str, Any]:
        """Build query parameters from ListParams object."""
        query_params: Dict[str, Any] = {
            "page": params.page,
            "per_page": params.per_page,
        }
        if params.filter_ is not None:
            query_params["filter"] = (
                params.filter_
                if isinstance(params.filter_, str)
                else json.dumps(params.filter_)
            )
        if params.sort_by is not None:
            query_params["sort_by"] = params.sort_by
        if params.view_id is not None:
            query_params["view_id"] = params.view_id
        return query_params

    @staticmethod
    def _serialize_payload(
        data: Union[TaskCreateRequest, TaskUpdateRequest, Task, Dict[str, Any]],
    ) -> Dict[str, Any]:
        if isinstance(data, BaseModel):
            return data.model_dump(by_alias=True, exclude_none=True)
        model_dump = getattr(data, "model_dump", None)
        if callable(model_dump):
            payload = model_dump(by_alias=True, exclude_none=True)
            if isinstance(payload, dict):
                return {
                    key: value for key, value in payload.items() if value is not None
                }
        if isinstance(data, Mapping):
            return {key: value for key, value in data.items() if value is not None}
        dict_method = getattr(data, "dict", None)
        if callable(dict_method):
            payload_dict = dict_method()
            if isinstance(payload_dict, dict):
                return {
                    key: value
                    for key, value in payload_dict.items()
                    if value is not None and not key.startswith("_")
                }
        if hasattr(data, "__dict__"):
            return {
                key: value
                for key, value in vars(data).items()
                if not key.startswith("_") and value is not None
            }
        raise TypeError(
            "task_data must be a TaskCreateRequest, TaskUpdateRequest, Task, or dict"
        )
