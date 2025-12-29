"""
Integration tests for API client and various API modules.
These tests verify that the API client properly integrates with different API modules.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from zoho_projects_sdk.client import ZohoProjects
from zoho_projects_sdk.models import Issue
from zoho_projects_sdk.models.project_models import Project
from zoho_projects_sdk.models.task_models import Task
from zoho_projects_sdk.models.user_models import User


@pytest.mark.asyncio
async def test_api_client_integration_with_projects_module() -> None:
    """Test that the API client properly integrates with the projects module."""
    # pylint: disable=protected-access
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
        with patch.object(
            client._api_client, "get", new_callable=AsyncMock
        ) as mock_api_get:
            # Mock response for getting a project
            mock_project_response = {
                "projects": [
                    {
                        "id": 1,
                        "name": "Test Project",
                        "status": "active",
                        "description": "A test project",
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31",
                    }
                ]
            }
            mock_api_get.return_value = mock_project_response

            # Use the projects module to get a project
            project = await client.projects.get(project_id=1)

            # Verify the project was returned correctly
            assert isinstance(project, Project)
            assert project.id == 1
            assert project.name == "Test Project"
            assert project.status_name == "active"

            # Verify the API call was made with the correct parameters
            mock_api_get.assert_called_once()
            call_args = mock_api_get.call_args
            assert call_args[0][0].endswith("/portal/test_portal_id/projects/1")
    # pylint: enable=protected-access


@pytest.mark.asyncio
async def test_api_client_integration_with_tasks_module() -> None:
    """Test that the API client properly integrates with the tasks module."""
    # pylint: disable=protected-access
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
        with patch.object(
            client._api_client, "get", new_callable=AsyncMock
        ) as mock_api_get:
            # Mock response for getting tasks
            mock_tasks_response = {
                "tasks": [
                    {
                        "id": 1,
                        "name": "Test Task",
                        "status": "Not Started",
                        "priority": "High",
                        "start_date": "2023-01-01",
                        "end_date": "2023-01-10",
                    }
                ]
            }
            mock_api_get.return_value = mock_tasks_response

            # Use the tasks module to get tasks
            tasks = await client.tasks.get_all(project_id=1)

            # Verify the tasks were returned correctly
            assert len(tasks) == 1
            assert isinstance(tasks[0], Task)
            assert tasks[0].id == 1
            assert tasks[0].name == "Test Task"
            assert tasks[0].priority == "High"

            # Verify the API call was made with the correct parameters
            mock_api_get.assert_called_once()
            call_args = mock_api_get.call_args
            assert call_args[0][0].endswith("/portal/test_portal_id/projects/1/tasks")
    # pylint: enable=protected-access


@pytest.mark.asyncio
async def test_api_client_integration_with_issues_module() -> None:
    """Test that the API client properly integrates with the issues module."""
    # pylint: disable=protected-access
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
        with patch.object(
            client._api_client, "get", new_callable=AsyncMock
        ) as mock_api_get:
            # Mock response for getting issues
            mock_bugs_response = {
                "issues": [
                    {
                        "id": 1,
                        "name": "Test Bug",
                        "status": {"id": 1, "name": "Open"},
                        "priority": "High",
                        "description": "A test bug",
                        "severity": {"id": 1, "name": "High"},
                    }
                ]
            }
            mock_api_get.return_value = mock_bugs_response

            # Use the issues module to get issues
            bugs = await client.issues.get_all(project_id=1)

            # Verify the bugs were returned correctly
            assert len(bugs) == 1
            assert isinstance(bugs[0], Issue)
            assert bugs[0].id == 1
            assert bugs[0].name == "Test Bug"
            assert bugs[0].priority == "High"

            # Verify the API call was made with the correct parameters
            mock_api_get.assert_called_once()
            call_args = mock_api_get.call_args
            assert call_args[0][0].endswith("/portal/test_portal_id/projects/1/issues")
    # pylint: enable=protected-access


@pytest.mark.asyncio
async def test_api_client_integration_with_users_module() -> None:
    """Test that the API client properly integrates with the users module."""
    # pylint: disable=protected-access
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
        with patch.object(
            client._api_client, "get", new_callable=AsyncMock
        ) as mock_api_get:
            # Mock response for getting users
            mock_users_response = {
                "users": [
                    {
                        "id": "user1",
                        "name": "Test User",
                        "email": "test@example.com",
                        "status": "active",
                    }
                ]
            }
            mock_api_get.return_value = mock_users_response

            # Use the users module to get users
            users = await client.users.get_all(project_id=1)

            # Verify the users were returned correctly
            assert len(users) == 1
            assert isinstance(users[0], User)
            assert users[0].id == "user1"
            assert users[0].name == "Test User"
            assert users[0].email == "test@example.com"

            # Verify the API call was made with the correct parameters
            mock_api_get.assert_called_once()
            call_args = mock_api_get.call_args
            assert call_args[0][0].endswith("/portal/test_portal_id/projects/1/users")
    # pylint: enable=protected-access


@pytest.mark.asyncio
async def test_api_client_integration_with_multiple_modules_sequentially() -> None:
    """Test that the API client can work with multiple modules in sequence."""
    # pylint: disable=protected-access
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
        with patch.object(
            client._api_client, "get", new_callable=AsyncMock
        ) as mock_api_get:
            # Mock responses for different API calls
            responses = [
                {  # Response for getting a project
                    "projects": [
                        {
                            "id": 1,
                            "name": "Test Project",
                            "status": "active",
                        }
                    ]
                },
                {  # Response for getting tasks
                    "tasks": [
                        {
                            "id": 1,
                            "name": "Test Task",
                            "status": "Not Started",
                        }
                    ]
                },
                {  # Response for getting issues
                    "issues": [
                        {
                            "id": 1,
                            "name": "Test Bug",
                            "status": {"id": 1, "name": "Open"},
                        }
                    ]
                },
            ]

            # Set up the side effect to return different responses for each call
            mock_api_get.side_effect = responses

            # Use the projects module to get a project
            project = await client.projects.get(project_id=1)
            assert isinstance(project, Project)
            assert project.id == 1

            # Use the tasks module to get tasks
            tasks = await client.tasks.get_all(project_id=1)
            assert len(tasks) == 1
            assert isinstance(tasks[0], Task)
            assert tasks[0].id == 1

            # Use the issues module to get issues
            bugs = await client.issues.get_all(project_id=1)
            assert len(bugs) == 1
            assert isinstance(bugs[0], Issue)
            assert bugs[0].id == 1

            # Verify that 3 API calls were made
            assert mock_api_get.call_count == 3
    # pylint: enable=protected-access


@pytest.mark.asyncio
async def test_api_client_integration_with_post_requests() -> None:
    """Test that the API client properly handles POST requests from API modules."""
    # pylint: disable=protected-access
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
        with patch.object(
            client._api_client, "post", new_callable=AsyncMock
        ) as mock_api_post:
            # Mock response for creating a project
            mock_project_response = {
                "project": {
                    "id": 1,
                    "name": "New Test Project",
                    "status": "active",
                }
            }
            mock_api_post.return_value = mock_project_response

            # Create a project using the projects module
            project_data = Project(
                id=1,
                name="New Test Project",
                status="active",
                description="A newly created test project",
            )
            created_project = await client.projects.create(project_data=project_data)

            # Verify the project was created correctly
            assert isinstance(created_project, Project)
            assert created_project.id == 1
            assert created_project.name == "New Test Project"

            # Verify the API call was made with the correct parameters
            mock_api_post.assert_called_once()
            args, kwargs = mock_api_post.call_args

            # Check the endpoint
            assert args[0].endswith("/portal/test_portal_id/projects")

            # Check the JSON data
            assert kwargs["json"]["name"] == "New Test Project"
            # The status is now serialized as a ProjectStatus object
            assert kwargs["json"]["status"]["name"] == "active"
            assert kwargs["json"]["description"] == "A newly created test project"
    # pylint: enable=protected-access
