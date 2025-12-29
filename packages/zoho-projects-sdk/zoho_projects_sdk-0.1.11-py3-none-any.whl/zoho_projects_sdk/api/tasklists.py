"""
API methods for interacting with Zoho Tasklists.
"""

from typing import TYPE_CHECKING, List

from ..models.tasklist_models import Tasklist

if TYPE_CHECKING:
    from ..http_client import ApiClient


class TasklistsAPI:
    """
    Provides methods for accessing the tasklist-related endpoints of the
    Zoho Projects API.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(
        self, project_id: int, page: int = 1, per_page: int = 20
    ) -> List[Tasklist]:
        """
        Fetches all tasklists for a given project with pagination support.

        Args:
            project_id: The ID of the project to fetch tasklists for
            page: The page number to retrieve (starting from 1)
            per_page: The number of records per page (default 20, max usually 100)
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/tasklists"

        params = {"page": page, "per_page": per_page}
        response_data = await self._client.get(endpoint, params=params)
        # Zoho API returns tasklists in a 'tasklists' key
        tasklists_data = response_data.get("tasklists", [])
        return [Tasklist.model_validate(t) for t in tasklists_data]

    async def get(self, project_id: int, tasklist_id: int) -> Tasklist:
        """
        Fetches a single tasklist by its ID within a project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/tasklists/{tasklist_id}"

        response_data = await self._client.get(endpoint)
        # The API returns a list even for a single tasklist fetch
        tasklists_list = response_data.get("tasklists", [])
        if tasklists_list:
            return Tasklist.model_validate(tasklists_list[0])
        # Return an empty Tasklist instance when no tasklist is found
        return Tasklist.model_construct()

    async def create(self, project_id: int, tasklist_data: Tasklist) -> Tasklist:
        """
        Creates a new tasklist in the specified project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/tasklists"

        response_data = await self._client.post(
            endpoint, json=tasklist_data.model_dump(by_alias=True)
        )
        tasklist_data = response_data.get("tasklist", {})

        return Tasklist.model_validate(tasklist_data)

    async def update(
        self, project_id: int, tasklist_id: int, tasklist_data: Tasklist
    ) -> Tasklist:
        """
        Updates an existing tasklist in the specified project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/tasklists/{tasklist_id}"

        response_data = await self._client.patch(
            endpoint, json=tasklist_data.model_dump(by_alias=True)
        )
        tasklist_data = response_data.get("tasklist", {})

        return Tasklist.model_validate(tasklist_data)

    async def delete(self, project_id: int, tasklist_id: int) -> bool:
        """
        Deletes a tasklist by its ID within a project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/tasklists/{tasklist_id}"

        await self._client.delete(endpoint)
        return True
