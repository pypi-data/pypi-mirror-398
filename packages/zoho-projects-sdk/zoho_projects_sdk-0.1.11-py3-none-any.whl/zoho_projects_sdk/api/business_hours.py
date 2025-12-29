"""
API methods for interacting with Zoho Business Hours.
"""

from typing import TYPE_CHECKING, List

from ..models.business_hours_models import BusinessHour, BusinessHourUser

if TYPE_CHECKING:
    from ..http_client import ApiClient


class BusinessHoursAPI:
    """
    Provides methods for accessing the business hours-related endpoints of the
    Zoho Projects API.
    """

    def __init__(self, client: "ApiClient"):
        self._client = client

    async def get_all(self) -> List[BusinessHour]:
        """
        Fetches all business hours for the portal.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/business-hours"
        response_data = await self._client.get(endpoint)
        # Zoho API returns business hours in a 'businesshours' key
        business_hours_data = response_data.get("businesshours", [])
        return [BusinessHour.model_validate(bh) for bh in business_hours_data]

    async def get(self, business_hour_id: int) -> BusinessHour:
        """
        Fetches a single business hour by its ID.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/business-hours/{business_hour_id}"

        response_data = await self._client.get(endpoint)
        # The API returns a list even for a single business hour fetch
        business_hours_list = response_data.get("businesshours", [])
        if business_hours_list:
            return BusinessHour.model_validate(business_hours_list[0])
        # Return an empty BusinessHour instance when no business hour is found
        return BusinessHour.model_construct()

    async def create(self, business_hour_data: BusinessHour) -> BusinessHour:
        """
        Creates a new business hour.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/business-hours"

        response_data = await self._client.post(
            endpoint, json=business_hour_data.model_dump(by_alias=True)
        )
        business_hour_data = response_data.get("businesshour", {})

        return BusinessHour.model_validate(business_hour_data)

    async def update(
        self, business_hour_id: int, business_hour_data: BusinessHour
    ) -> BusinessHour:
        """
        Updates an existing business hour.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/business-hours/{business_hour_id}"

        response_data = await self._client.patch(
            endpoint, json=business_hour_data.model_dump(by_alias=True)
        )
        business_hour_data = response_data.get("businesshour", {})

        return BusinessHour.model_validate(business_hour_data)

    async def delete(self, business_hour_id: int) -> bool:
        """
        Deletes a business hour by its ID.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/business-hours/{business_hour_id}"

        await self._client.delete(endpoint)
        return True

    async def get_users(self, business_hour_id: int) -> List[BusinessHourUser]:
        """
        Fetches all users associated with a business hour.
        """
        portal_id = self._client.portal_id
        endpoint = f"/portal/{portal_id}/business-hours/{business_hour_id}/users"
        response_data = await self._client.get(endpoint)
        # Zoho API returns users in a 'users' key
        users_data = response_data.get("users", [])
        return [BusinessHourUser.model_validate(user) for user in users_data]
