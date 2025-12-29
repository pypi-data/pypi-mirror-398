"""
API methods for interacting with Zoho Tags.
"""

from typing import TYPE_CHECKING, List

from ..models.tag_models import Tag

if TYPE_CHECKING:
    from ..http_client import ApiClient


class TagsAPI:
    """
    Provides methods for accessing the tags-related endpoints of the Zoho Projects API.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(self) -> List[Tag]:
        """
        Fetches all tags for the portal.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/tags"
        response_data = await self._client.get(endpoint)
        # Zoho API returns tags in a 'tags' key
        tags_data = response_data.get("tags", [])
        return [Tag.model_validate(t) for t in tags_data]

    async def get(self, tag_id: int) -> Tag:
        """
        Fetches a single tag by its ID.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/tags/{tag_id}"

        response_data = await self._client.get(endpoint)
        # The API returns a list even for a single tag fetch
        tags_list = response_data.get("tags", [])
        if tags_list:
            return Tag.model_validate(tags_list[0])
        # Return an empty Tag instance when no tag is found
        return Tag.model_construct()

    async def create(self, tag_data: Tag) -> Tag:
        """
        Creates a new tag.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/tags"

        response_data = await self._client.post(
            endpoint, json=tag_data.model_dump(by_alias=True)
        )
        tag_data = response_data.get("tag", {})

        return Tag.model_validate(tag_data)

    async def update(self, tag_id: int, tag_data: Tag) -> Tag:
        """
        Updates an existing tag.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/tags/{tag_id}"

        response_data = await self._client.patch(
            endpoint, json=tag_data.model_dump(by_alias=True)
        )
        tag_data = response_data.get("tag", {})

        return Tag.model_validate(tag_data)

    async def delete(self, tag_id: int) -> bool:
        """
        Deletes a tag by its ID.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/tags/{tag_id}"

        await self._client.delete(endpoint)
        return True
