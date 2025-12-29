from unittest.mock import AsyncMock

import pytest

from zoho_projects_sdk.api.users import UsersAPI
from zoho_projects_sdk.models.user_models import User


class _ClientWithoutPortal(AsyncMock):
    portal_id = None


@pytest.mark.asyncio()
async def test_users_api_requires_portal_id() -> None:
    client = _ClientWithoutPortal()
    api = UsersAPI(client)
    with pytest.raises(ValueError, match="Portal ID is required"):
        await api.get_all(project_id=1)


@pytest.mark.asyncio()
async def test_users_api_requires_portal_id_for_get() -> None:
    client = _ClientWithoutPortal()
    api = UsersAPI(client)
    with pytest.raises(ValueError, match="Portal ID is required"):
        await api.get(user_id=1)


@pytest.mark.asyncio()
async def test_users_api_requires_portal_id_for_update() -> None:
    client = _ClientWithoutPortal()
    api = UsersAPI(client)
    with pytest.raises(ValueError, match="Portal ID is required"):
        await api.update(
            user_id=1,
            user_data=User.model_validate({"id": 1, "name": "n", "email": "e"}),
        )


@pytest.mark.asyncio()
async def test_users_api_requires_portal_id_for_delete() -> None:
    client = _ClientWithoutPortal()
    api = UsersAPI(client)
    with pytest.raises(ValueError, match="Portal ID is required"):
        await api.delete(user_id=1)
