"""
Test fixtures and mock configurations for API endpoints in the Zoho Projects SDK.
"""

from typing import Any
from unittest.mock import AsyncMock

import httpx
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
from zoho_projects_sdk.http_client import ApiClient


@pytest.fixture
def mock_projects_api(mock_api_client: Any) -> ProjectsAPI:
    """Fixture to create a mock ProjectsAPI instance."""
    return ProjectsAPI(mock_api_client)


@pytest.fixture
def mock_tasks_api(mock_api_client: Any) -> TasksAPI:
    """Fixture to create a mock TasksAPI instance."""
    return TasksAPI(mock_api_client)


@pytest.fixture
def mock_issues_api(mock_api_client: Any) -> IssuesAPI:
    """Fixture to create a mock IssuesAPI instance."""
    return IssuesAPI(mock_api_client)


@pytest.fixture
def mock_users_api(mock_api_client: Any) -> UsersAPI:
    """Fixture to create a mock UsersAPI instance."""
    return UsersAPI(mock_api_client)


@pytest.fixture
def mock_clients_api(mock_api_client: Any) -> ClientsAPI:
    """Fixture to create a mock ClientsAPI instance."""
    return ClientsAPI(mock_api_client)


@pytest.fixture
def mock_contacts_api(mock_api_client: Any) -> ContactsAPI:
    """Fixture to create a mock ContactsAPI instance."""
    return ContactsAPI(mock_api_client)


@pytest.fixture
def mock_portals_api(mock_api_client: Any) -> PortalsAPI:
    """Fixture to create a mock PortalsAPI instance."""
    return PortalsAPI(mock_api_client)


@pytest.fixture
def mock_roles_api(mock_api_client: Any) -> RolesAPI:
    """Fixture to create a mock RolesAPI instance."""
    return RolesAPI(mock_api_client)


@pytest.fixture
def mock_tags_api(mock_api_client: Any) -> TagsAPI:
    """Fixture to create a mock TagsAPI instance."""
    return TagsAPI(mock_api_client)


@pytest.fixture
def mock_tasklists_api(mock_api_client: Any) -> TasklistsAPI:
    """Fixture to create a mock TasklistsAPI instance."""
    return TasklistsAPI(mock_api_client)


@pytest.fixture
def mock_timelogs_api(mock_api_client: Any) -> TimelogsAPI:
    """Fixture to create a mock TimelogsAPI instance."""
    return TimelogsAPI(mock_api_client)


@pytest.fixture
def mock_comments_api(mock_api_client: Any) -> CommentsAPI:
    """Fixture to create a mock CommentsAPI instance."""
    return CommentsAPI(mock_api_client)


@pytest.fixture
def mock_attachments_api(mock_api_client: Any) -> AttachmentsAPI:
    """Fixture to create a mock AttachmentsAPI instance."""
    return AttachmentsAPI(mock_api_client)


@pytest.fixture
def mock_baselines_api(mock_api_client: Any) -> BaselinesAPI:
    """Fixture to create a mock BaselinesAPI instance."""
    return BaselinesAPI(mock_api_client)


@pytest.fixture
def mock_business_hours_api(mock_api_client: Any) -> BusinessHoursAPI:
    """Fixture to create a mock BusinessHoursAPI instance."""
    return BusinessHoursAPI(mock_api_client)


@pytest.fixture
def mock_events_api(mock_api_client: Any) -> EventsAPI:
    """Fixture to create a mock EventsAPI instance."""
    return EventsAPI(mock_api_client)


@pytest.fixture
def mock_milestones_api(mock_api_client: Any) -> MilestonesAPI:
    """Fixture to create a mock MilestonesAPI instance."""
    return MilestonesAPI(mock_api_client)


@pytest.fixture
def mock_phases_api(mock_api_client: Any) -> PhasesAPI:
    """Fixture to create a mock PhasesAPI instance."""
    return PhasesAPI(mock_api_client)


@pytest.fixture
def mock_http_response() -> AsyncMock:
    """Fixture to create a mock HTTP response."""
    response = AsyncMock(spec=httpx.Response)
    response.json.return_value = {"data": "test_data"}
    response.status_code = 200
    response.text = '{"data": "test_data"}'
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    """Fixture to create a mock httpx.AsyncClient."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def mock_api_client_with_responses(mock_auth_handler: Any) -> ApiClient:
    """Fixture to create an ApiClient with mocked HTTP responses."""
    api_client = ApiClient(auth_handler=mock_auth_handler)

    # Mock the internal http client using setattr to avoid protected access warning
    setattr(api_client, "_http_client", AsyncMock())

    return api_client
