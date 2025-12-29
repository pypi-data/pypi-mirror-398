"""
API methods for interacting with Zoho Baselines.
"""

from typing import TYPE_CHECKING, List

from ..models.baseline_models import Baseline

if TYPE_CHECKING:
    from ..http_client import ApiClient


class BaselinesAPI:
    """
    Provides methods for accessing the baselines-related endpoints of the
    Zoho Projects API.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(self, project_id: int) -> List[Baseline]:
        """
        Fetches all baselines for a given project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/baselines"
        response_data = await self._client.get(endpoint)
        # Zoho API returns baselines in a 'baselines' key
        baselines_data = response_data.get("baselines", [])
        return [Baseline.model_validate(b) for b in baselines_data]

    async def get(self, project_id: int, baseline_id: int) -> Baseline:
        """
        Fetches a single baseline by its ID within a project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/baselines/{baseline_id}"

        response_data = await self._client.get(endpoint)
        # The API returns a list even for a single baseline fetch
        baselines_list = response_data.get("baselines", [])
        if baselines_list:
            return Baseline.model_validate(baselines_list[0])
        # Return an empty Baseline instance when no baseline is found
        return Baseline.model_construct(id=0, name="")

    async def create(self, project_id: int, baseline_data: Baseline) -> Baseline:
        """
        Creates a new baseline in the specified project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/baselines"

        response_data = await self._client.post(
            endpoint, json=baseline_data.model_dump(by_alias=True)
        )
        baseline_data = response_data.get("baseline", {})

        return Baseline.model_validate(baseline_data)

    async def update(
        self, project_id: int, baseline_id: int, baseline_data: Baseline
    ) -> Baseline:
        """
        Updates an existing baseline in the specified project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/baselines/{baseline_id}"

        response_data = await self._client.patch(
            endpoint, json=baseline_data.model_dump(by_alias=True)
        )
        baseline_data = response_data.get("baseline", {})

        return Baseline.model_validate(baseline_data)

    async def delete(self, project_id: int, baseline_id: int) -> bool:
        """
        Deletes a baseline by its ID within a project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/baselines/{baseline_id}"

        await self._client.delete(endpoint)
        return True
