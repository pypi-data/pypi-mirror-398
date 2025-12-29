from __future__ import annotations

from types import SimpleNamespace

import pytest

from zoho_projects_sdk.api.users import UsersAPI
from zoho_projects_sdk.models.user_models import User


class _RecordingClient:
    def __init__(self) -> None:
        self.portal_id = "portal-123"
        self._auth_handler = SimpleNamespace(portal_id="portal-123")
        self.calls: dict[str, str] = {}

    async def get(self, endpoint: str, params=None):  # type: ignore[override]
        self.calls["get"] = endpoint
        return {
            "users": [
                {
                    "id": "user-123",
                    "name": "Test User",
                    "email": "user@example.com",
                }
            ]
        }

    async def patch(self, endpoint: str, json):  # type: ignore[override]
        self.calls["patch"] = endpoint
        return {
            "user": {
                "id": "user-123",
                "name": "Updated User",
                "email": "updated@example.com",
            }
        }

    async def delete(self, endpoint: str):  # type: ignore[override]
        self.calls["delete"] = endpoint
        return {}


@pytest.mark.asyncio()
async def test_users_api_get_accepts_string_identifier() -> None:
    client = _RecordingClient()
    api = UsersAPI(client)

    result = await api.get("user-123")

    assert result.id == "user-123"
    assert client.calls["get"].endswith("/portal/portal-123/users/user-123")


@pytest.mark.asyncio()
async def test_users_api_update_accepts_string_identifier() -> None:
    client = _RecordingClient()
    api = UsersAPI(client)
    payload = User.model_validate(
        {"id": "user-123", "name": "Name", "email": "user@example.com"}
    )

    result = await api.update("user-123", payload)

    assert result.email == "updated@example.com"
    assert client.calls["patch"].endswith("/portal/portal-123/users/user-123")


@pytest.mark.asyncio()
async def test_users_api_delete_accepts_string_identifier() -> None:
    client = _RecordingClient()
    api = UsersAPI(client)

    result = await api.delete("user-123")

    assert result is True
    assert client.calls["delete"].endswith("/portal/portal-123/users/user-123")
