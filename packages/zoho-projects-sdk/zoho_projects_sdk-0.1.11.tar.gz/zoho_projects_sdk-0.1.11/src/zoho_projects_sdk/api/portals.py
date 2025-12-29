"""
API methods for interacting with Zoho Portals.
"""

from typing import TYPE_CHECKING, List

from ..models.portal_models import Portal  # This will be created later

if TYPE_CHECKING:
    from ..http_client import ApiClient


class PortalsAPI:
    """
    Provides methods for accessing the portal-related endpoints of the
    Zoho Projects API.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(self) -> List[Portal]:
        """
        Fetches all portals using the /portals/ endpoint.
        """
        endpoint = "/portals/"
        response_data = await self._client.get(endpoint)

        # Handle both response formats: direct list or dict with "portals" key
        if isinstance(response_data, list):
            # Response is a direct list of portals
            portals_data = response_data
        else:
            # Response is a dict with "portals" key
            portals_data = response_data.get("portals", [])

        return [Portal.model_validate(p) for p in portals_data]

    async def get(self, portal_id: int) -> Portal:
        """
        Fetches a single portal by ID.
        """
        endpoint = f"/portals/{portal_id}/"
        response_data = await self._client.get(endpoint)

        # Handle response format
        if isinstance(response_data, list) and len(response_data) > 0:
            portal_data = response_data[0]
        else:
            portals_list = (
                response_data.get("portals", [])
                if isinstance(response_data, dict)
                else []
            )
            portal_data = portals_list[0] if portals_list else {}

        if portal_data:
            return Portal.model_validate(portal_data)

        # Provide a minimal fallback when the API response contains no portal data
        return Portal.model_construct(id=0, name="")

    async def create(self, portal_data: Portal) -> Portal:
        """
        Creates a new portal.
        """
        endpoint = "/portals/"
        response_data = await self._client.post(
            endpoint, json=portal_data.model_dump(by_alias=True)
        )
        portal_result = response_data.get("portal", response_data)
        return Portal.model_validate(portal_result)

    async def update(self, portal_id: int, portal_data: Portal) -> Portal:
        """
        Updates an existing portal.
        """
        endpoint = f"/portals/{portal_id}/"
        response_data = await self._client.patch(
            endpoint, json=portal_data.model_dump(by_alias=True)
        )
        portal_result = response_data.get("portal", response_data)
        return Portal.model_validate(portal_result)

    async def delete(self, portal_id: int) -> bool:
        """
        Deletes a portal.
        """
        endpoint = f"/portals/{portal_id}/"
        await self._client.delete(endpoint)
        return True
