from typing import TYPE_CHECKING, List

from zoho_projects_sdk.models.milestone_models import (
    Milestone,
    MilestoneCreateRequest,
    MilestoneUpdateRequest,
)

if TYPE_CHECKING:
    from zoho_projects_sdk.http_client import ApiClient


class MilestonesAPI:
    """
    API class for managing milestones in Zoho Projects.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(self, project_id: str) -> List[Milestone]:
        """
        Get all milestones for a project.

        Args:
            project_id: The ID of the project

        Returns:
            List of Milestone objects
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/milestones"
        response = await self._client.get(url)
        return [
            Milestone.model_validate(milestone_data)
            for milestone_data in response.get("milestones", [])
        ]

    async def get(self, project_id: str, milestone_id: str) -> Milestone:
        """
        Get a specific milestone by ID.

        Args:
            project_id: The ID of the project
            milestone_id: The ID of the milestone

        Returns:
            Milestone object
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/milestones/{milestone_id}"
        response = await self._client.get(url)
        return Milestone.model_validate(response.get("milestone", {}))

    async def create(
        self, project_id: str, milestone_data: MilestoneCreateRequest
    ) -> Milestone:
        """
        Create a new milestone.

        Args:
            project_id: The ID of the project
            milestone_data: MilestoneCreateRequest object containing milestone details

        Returns:
            Created Milestone object
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/milestones"
        payload = milestone_data.model_dump(exclude_none=True)
        response = await self._client.post(url, json=payload)
        return Milestone.model_validate(response.get("milestone", {}))

    async def update(
        self, project_id: str, milestone_id: str, milestone_data: MilestoneUpdateRequest
    ) -> Milestone:
        """
        Update an existing milestone.

        Args:
            project_id: The ID of the project
            milestone_id: The ID of the milestone to update
            milestone_data: MilestoneUpdateRequest object containing updated milestone
            details

        Returns:
            Updated Milestone object
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/milestones/{milestone_id}"
        payload = milestone_data.model_dump(exclude_none=True)
        response = await self._client.patch(url, json=payload)
        return Milestone.model_validate(response.get("milestone", {}))

    async def delete(self, project_id: str, milestone_id: str) -> bool:
        """
        Delete a milestone.

        Args:
            project_id: The ID of the project
            milestone_id: The ID of the milestone to delete

        Returns:
            True if deletion was successful
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/milestones/{milestone_id}"
        await self._client.delete(url)
        return True
