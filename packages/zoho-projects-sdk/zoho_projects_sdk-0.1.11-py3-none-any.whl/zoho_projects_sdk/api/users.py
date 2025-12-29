"""
API methods for interacting with Zoho Users.
"""

from typing import TYPE_CHECKING, List, Union

from ..models.user_models import User

if TYPE_CHECKING:
    from ..http_client import ApiClient


class UsersAPI:
    """
    Provides methods for accessing the user-related endpoints of the Zoho Projects API.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(
        self, project_id: int, page: int = 1, per_page: int = 20
    ) -> List[User]:
        """
        Fetches all users for a given project with pagination support.

        Args:
            project_id: The ID of the project to fetch users for
            page: The page number to retrieve (starting from 1)
            per_page: The number of records per page (default 20, max usually 100)
        """
        portal_id = self._client.portal_id
        if portal_id is None:
            raise ValueError("Portal ID is required but not available")
        endpoint = f"/portal/{portal_id}/projects/{project_id}/users"

        params = {"page": page, "per_page": per_page}
        response_data = await self._client.get(endpoint, params=params)
        # Zoho API returns users in a 'users' key
        users_data = response_data.get("users", [])
        return [User.model_validate(u) for u in users_data]

    async def get(self, user_id: Union[str, int]) -> User:
        """
        Fetches a single user by their ID.
        """
        portal_id = self._client.portal_id
        if portal_id is None:
            raise ValueError("Portal ID is required but not available")
        # Convert user_id to string with "user" prefix if it's an integer
        if isinstance(user_id, int):
            user_id_str = f"user{user_id}"
        else:
            user_id_str = str(user_id)
        endpoint = f"/portal/{portal_id}/users/{user_id_str}"

        response_data = await self._client.get(endpoint)
        # The API returns a list even for a single user fetch
        users_list = response_data.get("users", [])
        if users_list:
            return User.model_validate(users_list[0])
        # Return an empty User instance when no user is found
        return User.model_validate({"id": 0, "name": "", "email": "", "costRate": None})

    async def update(self, user_id: Union[str, int], user_data: User) -> User:
        """
        Updates an existing user.
        """
        portal_id = self._client.portal_id
        if portal_id is None:
            raise ValueError("Portal ID is required but not available")
        # Convert user_id to string with "user" prefix if it's an integer
        if isinstance(user_id, int):
            user_id_str = f"user{user_id}"
        else:
            user_id_str = str(user_id)
        endpoint = f"/portal/{portal_id}/users/{user_id_str}"

        response_data = await self._client.patch(
            endpoint, json=user_data.model_dump(by_alias=True)
        )
        user_data = response_data.get("user", {})

        return User.model_validate(user_data)

    async def delete(self, user_id: Union[str, int]) -> bool:
        """
        Deletes a user by their ID.
        """
        portal_id = self._client.portal_id
        if portal_id is None:
            raise ValueError("Portal ID is required but not available")
        # Convert user_id to string with "user" prefix if it's an integer
        if isinstance(user_id, int):
            user_id_str = f"user{user_id}"
        else:
            user_id_str = str(user_id)
        endpoint = f"/portal/{portal_id}/users/{user_id_str}"

        await self._client.delete(endpoint)
        return True
