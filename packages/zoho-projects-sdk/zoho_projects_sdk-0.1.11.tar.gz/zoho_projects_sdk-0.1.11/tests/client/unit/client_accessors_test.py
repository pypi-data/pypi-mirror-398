from typing import cast
from unittest.mock import AsyncMock, patch

import pytest

from zoho_projects_sdk.api.attachments import AttachmentsAPI
from zoho_projects_sdk.api.baselines import BaselinesAPI
from zoho_projects_sdk.api.business_hours import BusinessHoursAPI
from zoho_projects_sdk.api.clients import ClientsAPI
from zoho_projects_sdk.api.comments import CommentsAPI
from zoho_projects_sdk.api.contacts import ContactsAPI
from zoho_projects_sdk.api.events import EventsAPI
from zoho_projects_sdk.api.issues import IssuesAPI
from zoho_projects_sdk.api.milestones import MilestonesAPI
from zoho_projects_sdk.api.phases import PhasesAPI
from zoho_projects_sdk.api.portals import PortalsAPI
from zoho_projects_sdk.api.projects import ProjectsAPI
from zoho_projects_sdk.api.roles import RolesAPI
from zoho_projects_sdk.api.tags import TagsAPI
from zoho_projects_sdk.api.tasklists import TasklistsAPI
from zoho_projects_sdk.api.tasks import TasksAPI
from zoho_projects_sdk.api.timelogs import TimelogsAPI
from zoho_projects_sdk.api.users import UsersAPI
from zoho_projects_sdk.client import ZohoProjects
from zoho_projects_sdk.config import ZohoAuthConfig
from zoho_projects_sdk.http_client import ApiClient


@pytest.fixture()
def sdk_client() -> ZohoProjects:
    return ZohoProjects(
        client_id="id",
        client_secret="secret",
        refresh_token="refresh",
        portal_id="portal",
    )


@pytest.mark.parametrize(
    ("attr", "expected"),
    [
        ("projects", ProjectsAPI),
        ("portals", PortalsAPI),
        ("tasks", TasksAPI),
        ("tasklists", TasklistsAPI),
        ("issues", IssuesAPI),
        ("users", UsersAPI),
        ("timelogs", TimelogsAPI),
        ("comments", CommentsAPI),
        ("events", EventsAPI),
        ("milestones", MilestonesAPI),
        ("phases", PhasesAPI),
        ("business_hours", BusinessHoursAPI),
        ("baselines", BaselinesAPI),
        ("attachments", AttachmentsAPI),
        ("tags", TagsAPI),
        ("clients", ClientsAPI),
        ("contacts", ContactsAPI),
        ("roles", RolesAPI),
    ],
)
def test_property_returns_expected_api_instances(
    sdk_client: ZohoProjects, attr: str, expected: type
) -> None:
    # pylint: disable=redefined-outer-name
    assert isinstance(getattr(sdk_client, attr), expected)


def test_api_instances_share_http_client(sdk_client: ZohoProjects) -> None:
    # pylint: disable=redefined-outer-name,protected-access
    projects = sdk_client.projects
    tasks = sdk_client.tasks
    assert projects._client is tasks._client  # noqa: W0212
    assert projects._client is sdk_client._api_client  # noqa: W0212


@pytest.mark.asyncio()
async def test_close_delegates_to_api_client(sdk_client: ZohoProjects) -> None:
    # pylint: disable=redefined-outer-name,protected-access
    closer = AsyncMock()
    setattr(sdk_client._api_client, "close", closer)  # noqa: W0212
    await sdk_client.close()
    closer.assert_awaited_once()


@pytest.mark.asyncio()
async def test_close_handles_missing_api_client(sdk_client: ZohoProjects) -> None:
    # pylint: disable=redefined-outer-name,protected-access
    sdk_client._api_client = cast(ApiClient, None)  # noqa: W0212
    await sdk_client.close()


@pytest.mark.asyncio()
async def test_async_context_manager_returns_self() -> None:
    # pylint: disable=protected-access
    test_client = ZohoProjects(
        client_id="id",
        client_secret="secret",
        refresh_token="refresh",
        portal_id="portal",
    )
    closer = AsyncMock()
    setattr(test_client._api_client, "close", closer)  # noqa: W0212

    async with test_client as context_client:
        assert context_client is test_client

    closer.assert_awaited_once()


@pytest.mark.asyncio()
async def test_async_context_manager_handles_missing_api_client(
    sdk_client: ZohoProjects,
) -> None:
    # pylint: disable=redefined-outer-name,protected-access
    sdk_client._api_client = cast(ApiClient, None)  # noqa: W0212

    async with sdk_client:
        pass


@pytest.mark.asyncio()
async def test_async_context_manager_propagates_exceptions() -> None:
    # pylint: disable=protected-access
    test_client = ZohoProjects(
        client_id="id",
        client_secret="secret",
        refresh_token="refresh",
        portal_id="portal",
    )
    closer = AsyncMock()
    setattr(test_client._api_client, "close", closer)  # noqa: W0212

    with pytest.raises(RuntimeError):
        async with test_client:
            raise RuntimeError("boom")

    closer.assert_awaited_once()


@pytest.mark.asyncio()
async def test_dunder_async_context_methods() -> None:
    # pylint: disable=protected-access,unnecessary-dunder-call
    test_client = ZohoProjects(
        client_id="id",
        client_secret="secret",
        refresh_token="refresh",
        portal_id="portal",
    )
    closer = AsyncMock()
    setattr(test_client._api_client, "close", closer)  # noqa: W0212

    result = await test_client.__aenter__()
    assert result is test_client

    await test_client.__aexit__(None, None, None)
    closer.assert_awaited_once()


def test_init_with_parameters() -> None:
    """
    Test initialization with explicit parameters.
    """
    # pylint: disable=protected-access
    test_client = ZohoProjects(
        client_id="test_client_id",
        client_secret="test_client_secret",
        refresh_token="test_refresh_token",
        portal_id="test_portal_id",
    )

    assert test_client._auth_handler.client_id == "test_client_id"  # noqa: W0212
    assert (
        test_client._auth_handler.client_secret == "test_client_secret"
    )  # noqa: W0212
    assert (
        test_client._auth_handler.refresh_token == "test_refresh_token"
    )  # noqa: W0212
    assert test_client._auth_handler.portal_id == "test_portal_id"  # noqa: W0212
    assert test_client._api_client is not None  # noqa: W0212


def test_init_with_invalid_string_timeout_defaults_to_none() -> None:
    """
    Test initialization with invalid string timeout defaults to None.
    """
    # pylint: disable=protected-access
    test_client = ZohoProjects(
        client_id="test_client_id",
        client_secret="test_client_secret",
        refresh_token="test_refresh_token",
        portal_id="test_portal_id",
        timeout="invalid_timeout",
    )

    assert test_client._auth_handler.timeout is None  # noqa: W0212


def test_init_with_config_object() -> None:
    """
    Test initialization with ZohoAuthConfig object.
    """
    # pylint: disable=protected-access
    config = ZohoAuthConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        refresh_token="test_refresh_token",
        portal_id="test_portal_id",
        timeout=30.0,
    )
    test_client = ZohoProjects(config=config)

    assert test_client._auth_handler.timeout == 30.0  # noqa: W0212
    assert test_client._api_client is not None  # noqa: W0212


def test_init_with_none_parameters() -> None:
    """
    Test initialization with None parameters (should use environment variables).
    """
    # pylint: disable=protected-access
    with patch.dict(
        "os.environ",
        {
            "ZOHO_PROJECTS_CLIENT_ID": "env_client_id",
            "ZOHO_PROJECTS_CLIENT_SECRET": "env_client_secret",
            "ZOHO_PROJECTS_REFRESH_TOKEN": "env_refresh_token",
            "ZOHO_PROJECTS_PORTAL_ID": "env_portal_id",
        },
    ):
        test_client = ZohoProjects(
            client_id=None,
            client_secret=None,
            refresh_token=None,
            portal_id=None,
        )

        assert test_client._auth_handler.client_id == "env_client_id"  # noqa: W0212
        assert (
            test_client._auth_handler.client_secret == "env_client_secret"
        )  # noqa: W0212
        assert (
            test_client._auth_handler.refresh_token == "env_refresh_token"
        )  # noqa: W0212
        assert test_client._auth_handler.portal_id == "env_portal_id"  # noqa: W0212
        assert test_client._api_client is not None  # noqa: W0212


def test_init_creates_api_client_with_auth_handler() -> None:
    """
    Test that initialization creates ApiClient with the correct auth handler.
    """
    # pylint: disable=protected-access
    test_client = ZohoProjects(
        client_id="test_client_id",
        client_secret="test_client_secret",
        refresh_token="test_refresh_token",
        portal_id="test_portal_id",
    )

    assert test_client._api_client is not None  # noqa: W0212
    api_client = test_client._api_client  # noqa: W0212
    assert api_client is not None
    assert api_client._auth_handler is test_client._auth_handler  # noqa: W0212


def test_init_auth_handler_and_api_client_are_different_instances() -> None:
    """
    Test that auth handler and API client are separate instances.
    """
    # pylint: disable=protected-access
    test_client = ZohoProjects(
        client_id="test_client_id",
        client_secret="test_client_secret",
        refresh_token="test_refresh_token",
        portal_id="test_portal_id",
    )

    assert test_client._auth_handler is not test_client._api_client  # noqa: W0212
    api_client = test_client._api_client  # noqa: W0212
    assert api_client is not None
    # Check that the auth handlers are the same instance
    assert test_client._auth_handler is api_client._auth_handler  # noqa: W0212
