"""
API methods for interacting with Zoho Roles.
"""

from typing import TYPE_CHECKING, List

from ..models.role_models import Role

if TYPE_CHECKING:
    from ..http_client import ApiClient


class RolesAPI:
    """
    Provides methods for accessing the roles-related endpoints of the Zoho Projects API.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(self) -> List[Role]:
        """
        Fetches all roles for the portal.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/roles"
        response_data = await self._client.get(endpoint)
        # Zoho API returns roles in a 'roles' key
        roles_data = response_data.get("roles", [])
        return [Role.model_validate(r) for r in roles_data]
