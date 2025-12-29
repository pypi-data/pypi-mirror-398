"""
API methods for interacting with Zoho Attachments.
"""

from typing import TYPE_CHECKING, List

from ..models.attachment_models import Attachment

if TYPE_CHECKING:
    from ..http_client import ApiClient


class AttachmentsAPI:
    """
    Provides methods for accessing the attachments-related endpoints of the
    Zoho Projects API.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(self, project_id: int) -> List[Attachment]:
        """
        Fetches all attachments for a given project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/attachments"
        response_data = await self._client.get(endpoint)
        # Zoho API returns attachments in an 'attachments' key
        attachments_data = response_data.get("attachments", [])
        return [Attachment.model_validate(a) for a in attachments_data]

    async def get(self, project_id: int, attachment_id: int) -> Attachment:
        """
        Fetches a single attachment by its ID within a project.
        """
        portal_id = self._client.portal_id
        endpoint = (
            f"/portal/{portal_id}/projects/{project_id}/attachments/{attachment_id}"
        )

        response_data = await self._client.get(endpoint)
        # The API returns a list even for a single attachment fetch
        attachments_list = response_data.get("attachments", [])
        if attachments_list:
            return Attachment.model_validate(attachments_list[0])
        # Return an empty Attachment instance when no attachment is found
        return Attachment.model_construct(id=0, name="")

    async def create(self, project_id: int, attachment_data: Attachment) -> Attachment:
        """
        Creates a new attachment in the specified project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/attachments"

        response_data = await self._client.post(
            endpoint, json=attachment_data.model_dump(by_alias=True)
        )
        attachment_data = response_data.get("attachment", {})

        return Attachment.model_validate(attachment_data)

    async def delete(self, project_id: int, attachment_id: int) -> bool:
        """
        Deletes an attachment by its ID within a project.
        """
        portal_id = self._client.portal_id
        endpoint = (
            f"/portal/{portal_id}/projects/{project_id}/attachments/{attachment_id}"
        )

        await self._client.delete(endpoint)
        return True

    async def associate_with_module(
        self, project_id: int, attachment_id: int, entity_type: str, entity_id: int
    ) -> bool:
        """
        Associates an attachment with a specific module/entity.
        """
        portal_id = self._client.portal_id
        endpoint = (
            f"/portal/{portal_id}/projects/{project_id}/attachments/{attachment_id}"
        )

        payload = {
            "associate_module": {"entity_type": entity_type, "entity_id": entity_id}
        }

        await self._client.post(endpoint, json=payload)
        return True
