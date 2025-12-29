from typing import TYPE_CHECKING, List

from zoho_projects_sdk.models.event_models import (
    Event,
    EventCreateRequest,
    EventUpdateRequest,
)

if TYPE_CHECKING:
    from zoho_projects_sdk.http_client import ApiClient


class EventsAPI:
    """
    API class for managing events in Zoho Projects.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(self, project_id: str) -> List[Event]:
        """
        Get all events for a project.

        Args:
            project_id: The ID of the project

        Returns:
            List of Event objects
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/events"
        response = await self._client.get(url)
        return [
            Event.model_validate(event_data)
            for event_data in response.get("events", [])
        ]

    async def get(self, project_id: str, event_id: str) -> Event:
        """
        Get a specific event by ID.

        Args:
            project_id: The ID of the project
            event_id: The ID of the event

        Returns:
            Event object
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/events/{event_id}"
        response = await self._client.get(url)
        return Event.model_validate(response.get("event", {}))

    async def create(self, project_id: str, event_data: EventCreateRequest) -> Event:
        """
        Create a new event.

        Args:
            project_id: The ID of the project
            event_data: EventCreateRequest object containing event details

        Returns:
            Created Event object
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/events"
        payload = event_data.model_dump(exclude_none=True)
        response = await self._client.post(url, json=payload)
        return Event.model_validate(response.get("event", {}))

    async def update(
        self, project_id: str, event_id: str, event_data: EventUpdateRequest
    ) -> Event:
        """
        Update an existing event.

        Args:
            project_id: The ID of the project
            event_id: The ID of the event to update
            event_data: EventUpdateRequest object containing updated event details

        Returns:
            Updated Event object
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/events/{event_id}"
        payload = event_data.model_dump(exclude_none=True)
        response = await self._client.patch(url, json=payload)
        return Event.model_validate(response.get("event", {}))

    async def delete(self, project_id: str, event_id: str) -> bool:
        """
        Delete an event.

        Args:
            project_id: The ID of the project
            event_id: The ID of the event to delete

        Returns:
            True if deletion was successful
        """
        portal_id = self._client.portal_id
        url = f"/portal/{portal_id}/projects/{project_id}/events/{event_id}"
        await self._client.delete(url)
        return True
