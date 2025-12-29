"""
API methods for interacting with Zoho Clients.
"""

from typing import TYPE_CHECKING, List

from ..models.client_models import Client, ClientProject

if TYPE_CHECKING:
    from ..http_client import ApiClient


class ClientsAPI:
    """
    Provides methods for accessing the clients-related endpoints of the
    Zoho Projects API.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(self) -> List[Client]:
        """
        Fetches all clients for the portal.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/clients"
        response_data = await self._client.get(endpoint)
        # Zoho API returns clients in a 'clients' key
        clients_data = response_data.get("clients", [])
        return [Client.model_validate(c) for c in clients_data]

    async def get(self, client_id: int) -> Client:
        """
        Fetches a single client by its ID.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/clients/{client_id}"

        response_data = await self._client.get(endpoint)
        # The API returns a list even for a single client fetch
        clients_list = response_data.get("clients", [])
        if clients_list:
            return Client.model_validate(clients_list[0])
        # Return an empty Client instance when no client is found
        return Client.model_construct()

    async def create(self, client_data: Client) -> Client:
        """
        Creates a new client.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/clients"

        response_data = await self._client.post(
            endpoint, json=client_data.model_dump(by_alias=True)
        )
        client_data = response_data.get("client", {})

        return Client.model_validate(client_data)

    async def update(self, client_id: int, client_data: Client) -> Client:
        """
        Updates an existing client.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/clients/{client_id}"

        response_data = await self._client.patch(
            endpoint, json=client_data.model_dump(by_alias=True)
        )
        client_data = response_data.get("client", {})

        return Client.model_validate(client_data)

    async def delete(self, client_id: int) -> bool:
        """
        Deletes a client by its ID.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/clients/{client_id}"

        await self._client.delete(endpoint)
        return True

    async def get_projects(self, client_id: int) -> List[ClientProject]:
        """
        Fetches all projects associated with a client.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/clients/{client_id}/projects"
        response_data = await self._client.get(endpoint)
        # Zoho API returns projects in a 'projects' key
        projects_data = response_data.get("projects", [])
        return [ClientProject.model_validate(p) for p in projects_data]
