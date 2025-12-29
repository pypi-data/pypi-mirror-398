"""
API methods for interacting with Zoho Contacts.
"""

from typing import TYPE_CHECKING, List

from ..models.contact_models import Contact

if TYPE_CHECKING:
    from ..http_client import ApiClient


class ContactsAPI:
    """
    Provides methods for accessing the contacts-related endpoints of the
    Zoho Projects API.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(self, client_id: int) -> List[Contact]:
        """
        Fetches all contacts for a given client.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/client/{client_id}/contacts"
        response_data = await self._client.get(endpoint)
        # Zoho API returns contacts in a 'contacts' key
        contacts_data = response_data.get("contacts", [])
        return [Contact.model_validate(c) for c in contacts_data]

    async def get(self, client_id: int, contact_id: int) -> Contact:
        """
        Fetches a single contact by its ID within a client.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/client/{client_id}/contacts/{contact_id}"

        response_data = await self._client.get(endpoint)
        # The API returns a list even for a single contact fetch
        contacts_list = response_data.get("contacts", [])
        if contacts_list:
            return Contact.model_validate(contacts_list[0])
        # Return an empty Contact instance when no contact is found
        return Contact.model_construct()

    async def create(self, client_id: int, contact_data: Contact) -> Contact:
        """
        Creates a new contact in the specified client.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/client/{client_id}/contacts"

        response_data = await self._client.post(
            endpoint, json=contact_data.model_dump(by_alias=True)
        )
        contact_data = response_data.get("contact", {})

        return Contact.model_validate(contact_data)

    async def update(
        self, client_id: int, contact_id: int, contact_data: Contact
    ) -> Contact:
        """
        Updates an existing contact in the specified client.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/client/{client_id}/contacts/{contact_id}"

        response_data = await self._client.patch(
            endpoint, json=contact_data.model_dump(by_alias=True)
        )
        contact_data = response_data.get("contact", {})

        return Contact.model_validate(contact_data)

    async def delete(self, client_id: int, contact_id: int) -> bool:
        """
        Deletes a contact by its ID within a client.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/client/{client_id}/contacts/{contact_id}"

        await self._client.delete(endpoint)
        return True
