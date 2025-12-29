"""
API methods for interacting with Zoho Comments.
"""

from typing import TYPE_CHECKING, List

from ..models.comment_models import Comment

if TYPE_CHECKING:
    from ..http_client import ApiClient


class CommentsAPI:
    """
    Provides methods for accessing the comment-related endpoints of the
    Zoho Projects API.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(
        self, project_id: int, page: int = 1, per_page: int = 20
    ) -> List[Comment]:
        """
        Fetches all comments for a given project with pagination support.

        Args:
            project_id: The ID of the project to fetch comments for
            page: The page number to retrieve (starting from 1)
            per_page: The number of records per page (default 20, max usually 100)
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/comments"

        params = {"page": page, "per_page": per_page}
        response_data = await self._client.get(endpoint, params=params)
        # Zoho API returns comments in a 'comments' key
        comments_data = response_data.get("comments", [])
        return [Comment.model_validate(c) for c in comments_data]

    async def get(self, project_id: int, comment_id: int) -> Comment:
        """
        Fetches a single comment by its ID within a project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/comments/{comment_id}"

        response_data = await self._client.get(endpoint)
        # The API returns a list even for a single comment fetch
        comments_list = response_data.get("comments", [])
        if comments_list:
            return Comment.model_validate(comments_list[0])
        # Return an empty Comment instance when no comment is found
        return Comment.model_construct(id=0)

    async def create(self, project_id: int, comment_data: Comment) -> Comment:
        """
        Creates a new comment in the specified project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/comments"

        response_data = await self._client.post(
            endpoint, json=comment_data.model_dump(by_alias=True)
        )
        comment_data = response_data.get("comment", {})

        return Comment.model_validate(comment_data)

    async def update(
        self, project_id: int, comment_id: int, comment_data: Comment
    ) -> Comment:
        """
        Updates an existing comment in the specified project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/comments/{comment_id}"

        response_data = await self._client.patch(
            endpoint, json=comment_data.model_dump(by_alias=True)
        )
        comment_data = response_data.get("comment", {})

        return Comment.model_validate(comment_data)

    async def delete(self, project_id: int, comment_id: int) -> bool:
        """
        Deletes a comment by its ID within a project.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/projects/{project_id}/comments/{comment_id}"

        await self._client.delete(endpoint)
        return True
