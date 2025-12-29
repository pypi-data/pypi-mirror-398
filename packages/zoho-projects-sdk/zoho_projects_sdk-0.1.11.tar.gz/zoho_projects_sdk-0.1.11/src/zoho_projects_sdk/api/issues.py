"""API methods for interacting with Zoho Issues."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from pydantic import BaseModel

from ..models.issue_models import Issue, IssueCreateRequest, IssueUpdateRequest

if TYPE_CHECKING:
    from ..http_client import ApiClient


class ListParams(BaseModel):
    """Parameters for list operations."""

    page: int = 1
    per_page: int = 20
    sort_by: Optional[str] = None
    view_id: Optional[Union[int, str]] = None
    issue_ids: Optional[str] = None
    filter_: Optional[Union[str, Dict[str, Any]]] = None


class IssuesAPI:
    """Helpers for the Zoho Projects Issues endpoints."""

    def __init__(self, client: "ApiClient") -> None:
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
    ) -> List[Issue]:
        """Retrieve issues across the entire portal."""
        params = params or ListParams()
        endpoint = f"/portal/{self._portal_id}/issues"
        query_params = self._build_list_params(params)
        response_data = await self._client.get(endpoint, params=query_params)
        return [
            Issue.model_validate(issue) for issue in response_data.get("issues", [])
        ]

    async def list_by_project(
        self,
        project_id: Union[int, str],
        params: Optional[ListParams] = None,
    ) -> List[Issue]:
        """Retrieve issues scoped to a single project."""
        params = params or ListParams()
        endpoint = f"/portal/{self._portal_id}/projects/{project_id}/issues"
        query_params = self._build_list_params(params)
        response_data = await self._client.get(endpoint, params=query_params)
        return [
            Issue.model_validate(issue) for issue in response_data.get("issues", [])
        ]

    async def get(
        self, project_id: Union[int, str], issue_id: Union[int, str]
    ) -> Issue:
        """Fetch details for a specific issue within a project."""

        endpoint = f"/portal/{self._portal_id}/projects/{project_id}/issues/{issue_id}"
        response_data = await self._client.get(endpoint)
        issues = response_data.get("issues", [])
        if issues:
            return Issue.model_validate(issues[0])
        return Issue.model_construct(id=None)

    async def create(
        self,
        project_id: Union[int, str],
        issue_data: Union[IssueCreateRequest, Issue, Dict[str, Any]],
    ) -> Issue:
        """Create an issue within the specified project."""

        endpoint = f"/portal/{self._portal_id}/projects/{project_id}/issues"
        payload = self._serialize_payload(issue_data)
        response_data = await self._client.post(endpoint, json=payload)
        issue = response_data.get("issue")
        return Issue.model_validate(issue)

    async def update(
        self,
        project_id: Union[int, str],
        issue_id: Union[int, str],
        issue_data: Union[IssueUpdateRequest, Issue, Dict[str, Any]],
    ) -> Issue:
        """Update an issue within the specified project."""

        endpoint = f"/portal/{self._portal_id}/projects/{project_id}/issues/{issue_id}"
        payload = self._serialize_payload(issue_data)
        response_data = await self._client.patch(endpoint, json=payload)
        issue = response_data.get("issue")
        return Issue.model_validate(issue)

    async def delete(
        self, project_id: Union[int, str], issue_id: Union[int, str]
    ) -> bool:
        """Delete an issue by its ID within a project."""

        endpoint = f"/portal/{self._portal_id}/projects/{project_id}/issues/{issue_id}"
        await self._client.delete(endpoint)
        return True

    async def get_all(
        self, project_id: Union[int, str], page: int = 1, per_page: int = 20
    ) -> List[Issue]:
        """Backward compatible alias for :meth:`list_by_project`."""
        params = ListParams(page=page, per_page=per_page)
        return await self.list_by_project(project_id, params=params)

    @staticmethod
    def _build_list_params(params: ListParams) -> Dict[str, Any]:
        """Build query parameters from ListParams object."""
        query_params: Dict[str, Any] = {
            "page": params.page,
            "per_page": params.per_page,
        }
        if params.sort_by is not None:
            query_params["sort_by"] = params.sort_by
        if params.view_id is not None:
            query_params["view_id"] = params.view_id
        if params.issue_ids is not None:
            query_params["issue_ids"] = params.issue_ids
        if params.filter_ is not None:
            filter_value = (
                params.filter_
                if isinstance(params.filter_, str)
                else json.dumps(params.filter_)
            )
            query_params["filter"] = filter_value
        return query_params

    @staticmethod
    def _serialize_payload(
        data: Union[IssueCreateRequest, IssueUpdateRequest, Issue, Dict[str, Any]],
    ) -> Dict[str, Any]:
        if isinstance(data, BaseModel):
            payload = data.model_dump(by_alias=True, exclude_none=True)
            return {key: value for key, value in payload.items() if value is not None}
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
            "issue_data must be an IssueCreateRequest, IssueUpdateRequest, "
            "Issue, or dict"
        )
