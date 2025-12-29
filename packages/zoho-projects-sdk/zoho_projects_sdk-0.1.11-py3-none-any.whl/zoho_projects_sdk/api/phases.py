from typing import TYPE_CHECKING, List

from zoho_projects_sdk.models.phase_models import (
    Phase,
    PhaseCreateRequest,
    PhaseUpdateRequest,
)

if TYPE_CHECKING:
    from zoho_projects_sdk.http_client import ApiClient


class PhasesAPI:
    """
    API class for managing phases in Zoho Projects.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(self, project_id: str) -> List[Phase]:
        """
        Get all phases for a project.

        Args:
            project_id: The ID of the project

        Returns:
            List of Phase objects
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/phases"
        response = await self._client.get(url)
        return [
            Phase.model_validate(phase_data)
            for phase_data in response.get("phases", [])
        ]

    async def get(self, project_id: str, phase_id: str) -> Phase:
        """
        Get a specific phase by ID.

        Args:
            project_id: The ID of the project
            phase_id: The ID of the phase

        Returns:
            Phase object
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/phases/{phase_id}"
        response = await self._client.get(url)
        return Phase.model_validate(response.get("phase", {}))

    async def create(self, project_id: str, phase_data: PhaseCreateRequest) -> Phase:
        """
        Create a new phase.

        Args:
            project_id: The ID of the project
            phase_data: PhaseCreateRequest object containing phase details

        Returns:
            Created Phase object
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/phases"
        payload = phase_data.model_dump(exclude_none=True)
        response = await self._client.post(url, json=payload)
        return Phase.model_validate(response.get("phase", {}))

    async def update(
        self, project_id: str, phase_id: str, phase_data: PhaseUpdateRequest
    ) -> Phase:
        """
        Update an existing phase.

        Args:
            project_id: The ID of the project
            phase_id: The ID of the phase to update
            phase_data: PhaseUpdateRequest object containing updated phase details

        Returns:
            Updated Phase object
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/phases/{phase_id}"
        payload = phase_data.model_dump(exclude_none=True)
        response = await self._client.patch(url, json=payload)
        return Phase.model_validate(response.get("phase", {}))

    async def delete(self, project_id: str, phase_id: str) -> bool:
        """
        Delete a phase.

        Args:
            project_id: The ID of the project
            phase_id: The ID of the phase to delete

        Returns:
            True if deletion was successful
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/phases/{phase_id}"
        await self._client.delete(url)
        return True
