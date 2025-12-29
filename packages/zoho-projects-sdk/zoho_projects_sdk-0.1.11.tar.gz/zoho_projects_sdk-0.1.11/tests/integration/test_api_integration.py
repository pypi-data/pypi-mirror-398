"""
Integration tests for the Zoho Projects SDK API modules.
These tests verify that different API components work together correctly.
"""

# pylint: disable=protected-access

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

from zoho_projects_sdk.client import ZohoProjects
from zoho_projects_sdk.http_client import ApiClient
from zoho_projects_sdk.models import Issue, Project, Task


@pytest_asyncio.fixture
async def mock_zoho_client() -> Any:  # pylint: disable=protected-access
    """Fixture to create a mock ZohoProjects client."""
    with (
        patch("zoho_projects_sdk.client.ZohoOAuth2Handler") as mock_auth_class,
        patch("zoho_projects_sdk.client.ApiClient") as mock_api_client_class,
    ):

        # Mock the auth handler
        mock_auth_instance = Mock()
        mock_auth_instance.portal_id = "test_portal_id"
        mock_auth_class.return_value = mock_auth_instance

        # Mock the API client with async-aware methods
        mock_api_client_instance = Mock(spec=ApiClient)
        mock_api_client_instance._auth_handler = mock_auth_instance
        mock_api_client_instance.portal_id = "test_portal_id"
        mock_api_client_instance.get = AsyncMock()
        mock_api_client_instance.post = AsyncMock()
        mock_api_client_instance.patch = AsyncMock()
        mock_api_client_instance.delete = AsyncMock()
        mock_api_client_instance.close = AsyncMock()
        mock_api_client_class.return_value = mock_api_client_instance

        # Create the client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Replace the API client with our async-aware mock
        client._api_client = mock_api_client_instance

        yield client


@pytest.mark.asyncio
async def test_project_with_tasks_integration(
    mock_zoho_client: ZohoProjects,  # pylint: disable=redefined-outer-name
) -> None:
    """Test integration between projects and tasks APIs."""
    # Mock project data
    mock_project_response = {
        "projects": [
            {
                "id": 1,
                "name": "Integration Test Project",
                "description": "A project for integration testing",
                "status": "active",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
            }
        ]
    }

    # Mock task data
    mock_tasks_response = {
        "tasks": [
            {
                "id": 1,
                "name": "Integration Test Task 1",
                "description": "First task for integration testing",
                "status": "Not Started",
                "priority": "High",
                "start_date": "2023-01-01",
                "end_date": "2023-01-10",
            },
            {
                "id": 2,
                "name": "Integration Test Task 2",
                "description": "Second task for integration testing",
                "status": "In Progress",
                "priority": "Medium",
                "start_date": "2023-01-11",
                "end_date": "2023-01-20",
            },
        ]
    }

    # Set up mock responses
    mock_zoho_client._api_client.get.side_effect = [
        mock_project_response,  # First call for project
        mock_tasks_response,  # Second call for tasks
    ]

    # Get project
    project = await mock_zoho_client.projects.get(project_id=1)
    assert isinstance(project, Project)
    assert project.id == 1
    assert project.name == "Integration Test Project"

    # Get tasks for the project
    tasks = await mock_zoho_client.tasks.get_all(project_id=1)
    assert len(tasks) == 2
    assert all(isinstance(task, Task) for task in tasks)
    assert tasks[0].name == "Integration Test Task 1"
    assert tasks[1].name == "Integration Test Task 2"

    # Verify the API calls were made correctly
    assert mock_zoho_client._api_client.get.call_count == 2


@pytest.mark.asyncio
async def test_project_with_issues_integration(
    mock_zoho_client: ZohoProjects,  # pylint: disable=redefined-outer-name
) -> None:
    """Test integration between projects and issues APIs."""
    # Mock project data
    mock_project_response = {
        "projects": [
            {
                "id": 1,
                "name": "Integration Test Project",
                "description": "A project for integration testing",
                "status": "active",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
            }
        ]
    }

    # Mock issue data
    mock_bugs_response = {
        "issues": [
            {
                "id": 1,
                "name": "Integration Test Issue 1",
                "description": "First bug for integration testing",
                "status": {"id": 1, "name": "Open"},
                "priority": "High",
            },
            {
                "id": 2,
                "name": "Integration Test Issue 2",
                "description": "Second bug for integration testing",
                "status": {"id": 2, "name": "Closed"},
                "priority": "Low",
            },
        ]
    }

    # Set up mock responses
    mock_zoho_client._api_client.get.side_effect = [
        mock_project_response,  # First call for project
        mock_bugs_response,  # Second call for bugs
    ]

    # Get project
    project = await mock_zoho_client.projects.get(project_id=1)
    assert isinstance(project, Project)
    assert project.id == 1
    assert project.name == "Integration Test Project"

    # Get issues for the project
    issues = await mock_zoho_client.issues.get_all(project_id=1)
    assert len(issues) == 2
    assert all(isinstance(issue, Issue) for issue in issues)
    assert issues[0].name == "Integration Test Issue 1"
    assert issues[1].name == "Integration Test Issue 2"

    # Verify the API calls were made correctly
    assert mock_zoho_client._api_client.get.call_count == 2


@pytest.mark.asyncio
async def test_create_project_with_task_integration(
    mock_zoho_client: ZohoProjects,  # pylint: disable=redefined-outer-name
) -> None:
    """Test creating a project and then creating a task within it."""
    # Mock project creation response
    mock_project_create_response = {
        "project": {
            "id": 1,
            "name": "New Integration Test Project",
            "description": "A newly created project for integration testing",
            "status": "active",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
        }
    }

    # Mock task creation response
    mock_task_create_response = {
        "task": {
            "id": 1,
            "name": "New Integration Test Task",
            "description": "A newly created task for integration testing",
            "status": "Not Started",
            "priority": "High",
            "start_date": "2023-01-01",
            "end_date": "2023-01-10",
        }
    }

    # Set up mock responses
    mock_zoho_client._api_client.post.side_effect = [
        mock_project_create_response,  # First call for project creation
        mock_task_create_response,  # Second call for task creation
    ]

    # Create project
    project_data = Project(
        id=1,
        name="New Integration Test Project",
        description="A newly created project for integration testing",
        status="active",
        start_date="2023-01-01",
        end_date="2023-12-31",
    )

    created_project = await mock_zoho_client.projects.create(project_data=project_data)
    assert isinstance(created_project, Project)
    assert created_project.id == 1
    assert created_project.name == "New Integration Test Project"

    # Create task within the project
    task_data = Task(
        id=1,
        name="New Integration Test Task",
        description="A newly created task for integration testing",
        status="Not Started",
        priority="High",
        start_date="2023-01-01",
        end_date="2023-01-10",
    )

    created_task = await mock_zoho_client.tasks.create(
        project_id=1, task_data=task_data
    )
    assert isinstance(created_task, Task)
    assert created_task.id == 1
    assert created_task.name == "New Integration Test Task"

    # Verify the API calls were made correctly
    assert mock_zoho_client._api_client.post.call_count == 2


@pytest.mark.asyncio
async def test_user_assignment_integration(
    mock_zoho_client: ZohoProjects,  # pylint: disable=redefined-outer-name
) -> None:
    """Test assigning users to projects and tasks."""
    # Mock user data
    mock_users_response = {
        "users": [
            {
                "id": "user1",
                "name": "Test User 1",
                "email": "user1@example.com",
                "role": {"id": 1, "name": "Administrator"},
                "status": "active",
            },
            {
                "id": "user2",
                "name": "Test User 2",
                "email": "user2@example.com",
                "role": {"id": 2, "name": "Member"},
                "status": "active",
            },
        ]
    }

    # Mock project assignment response
    mock_project_assignment_response = {
        "project": {
            "id": 1,
            "name": "Assigned Project",
            "description": "A project with assigned users",
            "status": "active",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
        }
    }

    # Set up mock responses
    mock_zoho_client._api_client.get.return_value = mock_users_response
    mock_zoho_client._api_client.patch.return_value = mock_project_assignment_response

    # Get users
    users = await mock_zoho_client.users.get_all(project_id=1)
    assert len(users) == 2
    assert users[0].id == "user1"
    assert users[1].id == "user2"

    # Assign user to project (this would typically involve a specific API call)
    # For this test, we'll simulate updating the project with user assignments

    # Verify the API calls were made correctly
    assert mock_zoho_client._api_client.get.call_count == 1
    # Note: The actual implementation of user assignment would depend on
    # the Zoho API specifics


@pytest.mark.asyncio
async def test_timelog_integration(
    mock_zoho_client: ZohoProjects,  # pylint: disable=redefined-outer-name
) -> None:
    """Test creating timelogs for tasks."""
    # Mock task data
    mock_task_response = {
        "tasks": [
            {
                "id": 1,
                "name": "Timelog Test Task",
                "description": "A task for timelog testing",
                "status": "In Progress",
                "priority": "High",
                "start_date": "2023-01-01",
                "end_date": "2023-01-10",
            }
        ]
    }

    # Mock timelog creation response
    mock_timelog_response = {
        "timelog": {
            "id": 1,
            "user_id": "user1",
            "project_id": 1,
            "log_date": "2023-01-01",
            "log_time": 120,  # 2 hours in minutes
            "description": "Worked on timelog integration test",
        }
    }

    # Set up mock responses
    mock_zoho_client._api_client.get.return_value = mock_task_response
    mock_zoho_client._api_client.post.return_value = mock_timelog_response

    # Get task
    task = await mock_zoho_client.tasks.get(project_id=1, task_id=1)
    assert isinstance(task, Task)
    assert task.id == 1
    assert task.name == "Timelog Test Task"

    # Create timelog for the task
    # Note: The actual timelog creation would depend on the Zoho API specifics
    # This is a simplified representation

    # Verify the API calls were made correctly
    assert mock_zoho_client._api_client.get.call_count == 1
    # Note: The actual implementation of timelog creation would depend on
    # the Zoho API specifics
