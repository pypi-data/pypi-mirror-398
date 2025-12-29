"""
Integration tests for model validation and API responses.
These tests verify that API responses are properly validated by Pydantic models.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from zoho_projects_sdk.client import ZohoProjects
from zoho_projects_sdk.models import Issue
from zoho_projects_sdk.models.project_models import Project
from zoho_projects_sdk.models.task_models import Task
from zoho_projects_sdk.models.user_models import User


@pytest.mark.asyncio
async def test_project_model_validation_from_api_response() -> None:
    """Ensure project responses validate through the Project model."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Mock the API client's get method directly
        with patch(
            "zoho_projects_sdk.http_client.ApiClient.get",
            new_callable=AsyncMock,
        ) as mock_api_get:
            # Mock response for getting a project with all fields
            mock_project_response = {
                "projects": [
                    {
                        "id": 123,
                        "name": "Test Project with Full Details",
                        "status": "active",
                        "description": "A comprehensive test project",
                        "created_time": "2023-01-01T00:00:00Z",
                        "updated_time": "2023-01-02T00:00:00Z",
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31",
                        "owner": {"id": "owner123", "name": "Project Owner"},
                        "portal_id": "test_portal_id",
                        "prefix": "TP",
                        "is_active": True,
                    }
                ]
            }
            mock_api_get.return_value = mock_project_response

            # Use the projects module to get a project
            project = await client.projects.get(project_id=123)

            # Verify the project was returned and validated correctly
            assert isinstance(project, Project)
            assert project.id == 123
            assert project.name == "Test Project with Full Details"
            assert project.status_name == "active"
            assert project.description == "A comprehensive test project"
            assert project.created_time == "2023-01-01T00:00:00Z"
            assert project.updated_time == "2023-01-02T00:00:00Z"
            assert project.start_date == "2023-01-01"
            assert project.end_date == "2023-12-31"
            assert project.owner == {"id": "owner123", "name": "Project Owner"}
            assert project.portal_id == "test_portal_id"
            assert project.prefix == "TP"
            assert project.is_active is True


@pytest.mark.asyncio
async def test_task_model_validation_from_api_response() -> None:
    """Ensure task responses validate through the Task model."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Mock the API client's get method directly
        with patch(
            "zoho_projects_sdk.http_client.ApiClient.get",
            new_callable=AsyncMock,
        ) as mock_api_get:
            # Mock response for getting a task with all fields
            mock_task_response = {
                "tasks": [
                    {
                        "id": 456,
                        "name": "Test Task with Full Details",
                        "description": "A comprehensive test task",
                        "status": "In Progress",
                        "priority": "High",
                        "start_date": "2023-02-01",
                        "end_date": "2023-02-10",
                        "created_time": "2023-01-15T10:00:00Z",
                        "updated_time": "2023-01-16T14:30:00Z",
                        "assignee": {"id": "user456", "name": "Task Assignee"},
                        "duration": {"value": 10.5, "type": "hours"},
                        "completed": False,
                    }
                ]
            }
            mock_api_get.return_value = mock_task_response

            # Use the tasks module to get a task
            task = await client.tasks.get(project_id=1, task_id=456)

            # Verify the task was returned and validated correctly
            assert isinstance(task, Task)
            assert task.id == 456
            assert task.name == "Test Task with Full Details"
            assert task.description == "A comprehensive test task"
            assert task.status == "In Progress"
            assert task.priority == "High"
            assert task.start_date == "2023-02-01"
            assert task.end_date == "2023-02-10"
            assert task.created_time == "2023-01-15T10:00:00Z"
            assert task.updated_time == "2023-01-16T14:30:00Z"
            assert task.assignee == {"id": "user456", "name": "Task Assignee"}
            assert task.duration is not None
            assert task.duration.value == 10.5
            assert task.duration.type == "hours"
            assert task.completed is False


@pytest.mark.asyncio
async def test_issue_model_validation_from_api_response() -> None:
    """Ensure issue responses validate through the Issue model."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Mock the API client's get method directly
        with patch(
            "zoho_projects_sdk.http_client.ApiClient.get",
            new_callable=AsyncMock,
        ) as mock_api_get:
            # Mock response for getting a bug with all fields
            mock_bug_response = {
                "issues": [
                    {
                        "id": 789,
                        "name": "Test Bug with Full Details",
                        "description": "A comprehensive test bug report",
                        "status": {"id": 3, "name": "Resolved"},
                        "priority": "Critical",
                        "severity": {"id": 2, "name": "High"},
                        "created_time": "2023-03-01T09:00:00Z",
                        "updated_time": "2023-03-02T11:30:00Z",
                        "assignee": {"id": "user987", "name": "Bug Assignee"},
                        "resolution": "Fixed",
                    }
                ]
            }
            mock_api_get.return_value = mock_bug_response

            # Use the issues module to get an issue
            bug = await client.issues.get(project_id=1, issue_id=789)

            # Verify the bug was returned and validated correctly
            assert isinstance(bug, Issue)
            assert bug.id == 789
            assert bug.name == "Test Bug with Full Details"
            assert bug.description == "A comprehensive test bug report"
            assert bug.status == {"id": 3, "name": "Resolved"}
            assert bug.priority == "Critical"
            assert bug.severity == {"id": 2, "name": "High"}
            assert bug.created_time == "2023-03-01T09:00:00Z"
            assert bug.updated_time == "2023-03-02T11:30:00Z"
            assert bug.assignee == {"id": "user987", "name": "Bug Assignee"}
            assert bug.resolution == "Fixed"


@pytest.mark.asyncio
async def test_user_model_validation_from_api_response() -> None:
    """Test that API responses for users are properly validated by the User model."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Mock the API client's get method directly
        with patch(
            "zoho_projects_sdk.http_client.ApiClient.get",
            new_callable=AsyncMock,
        ) as mock_api_get:
            # Mock response for getting a user with all fields
            mock_user_response = {
                "users": [
                    {
                        "id": "user101",
                        "zuid": "zoho_user101",
                        "name": "Test User with Full Details",
                        "first_name": "Test",
                        "last_name": "User",
                        "display_name": "Test User",
                        "email": "testuser@example.com",
                        "status": "active",
                        "user_type": "Project User",
                        "is_active": True,
                        "is_confirmed": True,
                        "added_time": "2023-01-10T08:0:00Z",
                        "updated_time": "2023-01-11T12:00:00Z",
                        "profile": {"id": "profile101", "name": "User Profile"},
                        "full_name": "Test User",
                        "cost_per_hour": "50",
                        "costRate": "60",
                        "invoice": "invoice_101",
                        "zohocrm_contact_id": "crm_101",
                        "projects": [{"id": 1, "name": "Project 1"}],
                    }
                ]
            }
            mock_api_get.return_value = mock_user_response

            # Use the users module to get a user
            user = await client.users.get(user_id="user101")

            # Verify the user was returned and validated correctly
            assert isinstance(user, User)
            assert user.id == "user101"
            assert user.zuid == "zoho_user101"
            assert user.name == "Test User with Full Details"
            assert user.first_name == "Test"
            assert user.last_name == "User"
            assert user.display_name == "Test User"
            assert user.email == "testuser@example.com"
            assert user.status == "active"
            assert user.user_type == "Project User"
            assert user.is_active is True
            assert user.is_confirmed is True
            assert user.added_time == "2023-01-10T08:0:00Z"
            assert user.updated_time == "2023-01-11T12:00:00Z"
            assert user.profile == {"id": "profile101", "name": "User Profile"}
            assert user.full_name == "Test User"
            assert user.cost_per_hour == "50"
            assert user.cost_rate == "60"
            assert user.invoice == "invoice_101"
            assert user.zohocrm_contact_id == "crm_101"
            assert user.projects == [{"id": 1, "name": "Project 1"}]


@pytest.mark.asyncio
async def test_model_validation_with_missing_optional_fields() -> None:
    """Test that models properly handle API responses with missing optional fields."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Mock the API client's get method directly
        with patch(
            "zoho_projects_sdk.http_client.ApiClient.get",
            new_callable=AsyncMock,
        ) as mock_api_get:
            # Mock response for getting a project with only required fields
            mock_project_response = {
                "projects": [
                    {
                        "id": 999,
                        "name": "Minimal Project",
                        "status": "active",
                        # Missing all optional fields
                    }
                ]
            }
            mock_api_get.return_value = mock_project_response

            # Use the projects module to get a project
            project = await client.projects.get(project_id=999)

            # Verify the project was returned with defaults for missing fields
            assert isinstance(project, Project)
            assert project.id == 999
            assert project.name == "Minimal Project"
            assert project.status_name == "active"
            assert project.description is None
            assert project.created_time is None
            assert project.updated_time is None
            assert project.start_date is None
            assert project.end_date is None
            assert project.owner is None
            assert project.portal_id is None
            assert project.prefix is None
            assert project.is_active is None


@pytest.mark.asyncio
async def test_model_validation_with_invalid_data() -> None:
    """Ensure models raise when API responses contain invalid data."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Mock the API client's get method directly
        with patch(
            "zoho_projects_sdk.http_client.ApiClient.get",
            new_callable=AsyncMock,
        ) as mock_api_get:
            # Mock response for getting a project with invalid data (string ID instead
            # of int)
            mock_project_response = {
                "projects": [
                    {
                        "id": "invalid_id",
                        "name": "Invalid Project",
                        "status": "active",
                    }
                ]
            }
            mock_api_get.return_value = mock_project_response

            # Use the projects module to get a project; this should raise a validation
            # error
            with pytest.raises(Exception):
                await client.projects.get(project_id=1)


@pytest.mark.asyncio
async def test_model_validation_in_create_operations() -> None:
    """Test that models validate data when creating resources via API."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Mock the API client's post method directly
        with patch(
            "zoho_projects_sdk.http_client.ApiClient.post",
            new_callable=AsyncMock,
        ) as mock_api_post:
            # Mock response for creating a task
            mock_task_response = {
                "task": {
                    "id": 111,
                    "name": "Created Task",
                    "status": "Not Started",
                    "priority": "Medium",
                    "created_time": "2023-04-01T10:00Z",
                }
            }
            mock_api_post.return_value = mock_task_response

            # Create a task using the tasks module with valid data
            task_data = Task(
                id=111, name="Created Task", status="Not Started", priority="Medium"
            )
            created_task = await client.tasks.create(project_id=1, task_data=task_data)

            # Verify the task was created and validated correctly
            assert isinstance(created_task, Task)
            assert created_task.id == 111
            assert created_task.name == "Created Task"
            assert created_task.status == "Not Started"
            assert created_task.priority == "Medium"
            assert created_task.created_time == "2023-04-01T10:00Z"
