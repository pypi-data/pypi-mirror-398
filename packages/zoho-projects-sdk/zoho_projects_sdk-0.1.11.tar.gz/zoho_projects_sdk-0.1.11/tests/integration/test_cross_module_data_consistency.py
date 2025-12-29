"""
Integration tests for cross-module data consistency.
These tests verify that data remains consistent across different modules.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from zoho_projects_sdk.client import ZohoProjects
from zoho_projects_sdk.models import Issue
from zoho_projects_sdk.models.project_models import Project
from zoho_projects_sdk.models.task_models import Task
from zoho_projects_sdk.models.user_models import User


@pytest.mark.asyncio
async def test_project_task_data_consistency() -> None:
    """Test that project and task data remain consistent across modules."""
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
                        "name": "Consistency Test Project",
                        "status": "active",
                        "description": "A project for testing data consistency",
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31",
                    }
                ]
            }

            # Mock response for getting tasks in the project
            mock_tasks_response = {
                "tasks": [
                    {
                        "id": 101,
                        "name": "Task in Consistency Test Project",
                        "description": "A task in the consistency test project",
                        "status": "Not Started",
                        "priority": "High",
                        "project_id": 1,  # Reference to the project
                        "start_date": "2023-01-01",
                        "end_date": "2023-01-10",
                    }
                ]
            }

            # Set up the side effect to return different responses for each call
            mock_api_get.side_effect = [mock_project_response, mock_tasks_response]

            # Get the project
            project = await client.projects.get(project_id=1)
            assert isinstance(project, Project)
            assert project.id == 1
            assert project.name == "Consistency Test Project"

            # Get tasks in the project
            tasks = await client.tasks.get_all(project_id=1)
            assert len(tasks) == 1
            assert isinstance(tasks[0], Task)
            assert tasks[0].id == 101
            assert tasks[0].name == "Task in Consistency Test Project"

            # Verify that the task belongs to the project (data consistency)
            assert tasks[0].project_id == project.id


@pytest.mark.asyncio
async def test_project_bug_data_consistency() -> None:
    """Test that project and bug data remain consistent across modules."""
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
                        "id": 2,
                        "name": "Bug Consistency Test Project",
                        "status": "active",
                        "description": "A project for testing bug data consistency",
                        "start_date": "2023-02-01",
                        "end_date": "2023-11-30",
                    }
                ]
            }

            # Mock response for getting issues in the project
            mock_bugs_response = {
                "issues": [
                    {
                        "id": 201,
                        "name": "Bug in Consistency Test Project",
                        "description": "A bug in the consistency test project",
                        "status": {"id": 1, "name": "Open"},
                        "priority": "Critical",
                        "project_id": 2,  # Reference to the project
                    }
                ]
            }

            # Set up the side effect to return different responses for each call
            mock_api_get.side_effect = [mock_project_response, mock_bugs_response]

            # Get the project
            project = await client.projects.get(project_id=2)
            assert isinstance(project, Project)
            assert project.id == 2
            assert project.name == "Bug Consistency Test Project"

            # Get issues in the project
            issues = await client.issues.get_all(project_id=2)
            assert len(issues) == 1
            assert isinstance(issues[0], Issue)
            assert issues[0].id == 201
            assert issues[0].name == "Bug in Consistency Test Project"

            # Verify that the issue belongs to the project (data consistency)
            assert issues[0].project_id == project.id


@pytest.mark.asyncio
async def test_user_project_assignment_consistency() -> None:
    """Test that user and project assignment data remain consistent across modules."""
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
                        "id": "user_consistency",
                        "name": "Consistency Test User",
                        "email": "consistency@example.com",
                        "status": "active",
                    }
                ]
            }

            # Mock response for getting a project
            mock_project_response = {
                "projects": [
                    {
                        "id": 3,
                        "name": "User Assignment Test Project",
                        "status": "active",
                        "description": "A project for testing user assignment consistency",
                    }
                ]
            }

            # Set up the side effect to return different responses for each call
            mock_api_get.side_effect = [mock_users_response, mock_project_response]

            # Get users
            users = await client.users.get_all(project_id=1)
            assert len(users) == 1
            assert isinstance(users[0], User)
            assert users[0].id == "user_consistency"
            assert users[0].name == "Consistency Test User"

            # Get a project
            project = await client.projects.get(project_id=3)
            assert isinstance(project, Project)
            assert project.id == 3
            assert project.name == "User Assignment Test Project"

            # Verify both entities exist with correct data
            assert users[0].id == "user_consistency"
            assert project.id == 3


@pytest.mark.asyncio
async def test_cross_module_data_updates_consistency() -> None:
    """Test that data updates in one module are reflected consistently in related modules."""
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

        # Mock the API client methods directly
        with (
            patch.object(
                client._api_client, "get", new_callable=AsyncMock
            ) as mock_api_get,
            patch.object(
                client._api_client, "patch", new_callable=AsyncMock
            ) as mock_api_patch,
        ):

            # Mock response for getting a project
            mock_project_response = {
                "projects": [
                    {
                        "id": 4,
                        "name": "Update Consistency Test Project",
                        "status": "active",
                        "description": "A project for testing update consistency",
                    }
                ]
            }

            # Mock response for getting tasks in the project
            mock_tasks_response = {
                "tasks": [
                    {
                        "id": 401,
                        "name": "Original Task Name",
                        "description": "Original task description",
                        "status": "Not Started",
                        "priority": "Medium",
                        "project_id": 4,
                    }
                ]
            }

            # Mock response for updating a task
            mock_updated_task_response = {
                "task": {
                    "id": 401,
                    "name": "Updated Task Name",
                    "description": "Updated task description",
                    "status": "In Progress",
                    "priority": "High",
                    "project_id": 4,
                }
            }

            # Set up the side effect to return different responses for each call
            mock_api_get.side_effect = [mock_project_response, mock_tasks_response]
            mock_api_patch.return_value = mock_updated_task_response

            # Get the project
            project = await client.projects.get(project_id=4)
            assert isinstance(project, Project)
            assert project.id == 4
            assert project.name == "Update Consistency Test Project"

            # Get tasks in the project
            tasks = await client.tasks.get_all(project_id=4)
            assert len(tasks) == 1
            assert isinstance(tasks[0], Task)
            assert tasks[0].id == 401
            assert tasks[0].name == "Original Task Name"

            # Update the task
            updated_task_data = Task(
                id=401,
                name="Updated Task Name",
                description="Updated task description",
                status="In Progress",
                priority="High",
            )
            updated_task = await client.tasks.update(
                project_id=4, task_id=401, task_data=updated_task_data
            )

            # Verify the task was updated
            assert isinstance(updated_task, Task)
            assert updated_task.id == 401
            assert updated_task.name == "Updated Task Name"
            assert updated_task.status == "In Progress"
            assert updated_task.priority == "High"

            # Verify that the task still belongs to the correct project (consistency maintained)
            assert updated_task.project_id == project.id


@pytest.mark.asyncio
async def test_project_task_issue_cross_referencing() -> None:
    """Test that projects, tasks, and issues maintain consistent cross-references."""
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
                        "id": 5,
                        "name": "Cross Reference Test Project",
                        "status": "active",
                        "description": "A project for testing cross-references",
                    }
                ]
            }

            # Mock response for getting tasks in the project
            mock_tasks_response = {
                "tasks": [
                    {
                        "id": 501,
                        "name": "Task with Cross Reference",
                        "description": "A task that should be linked to the project",
                        "status": "Medium",
                        "priority": "Medium",
                        "project_id": 5,  # Reference to project 5
                    }
                ]
            }

            # Mock response for getting issues in the project
            mock_issues_response = {
                "issues": [
                    {
                        "id": 502,
                        "name": "Issue with Cross Reference",
                        "description": "An issue that should be linked to the project",
                        "status": {"id": 1, "name": "Open"},
                        "priority": "High",
                        "project_id": 5,  # Reference to project 5
                    }
                ]
            }

            # Set up the side effect to return different responses for each call
            mock_api_get.side_effect = [
                mock_project_response,
                mock_tasks_response,
                mock_issues_response,
            ]

            # Get the project
            project = await client.projects.get(project_id=5)
            assert isinstance(project, Project)
            assert project.id == 5
            assert project.name == "Cross Reference Test Project"

            # Get tasks in the project
            tasks = await client.tasks.get_all(project_id=5)
            assert len(tasks) == 1
            assert isinstance(tasks[0], Task)
            assert tasks[0].id == 501
            assert tasks[0].project_id == 5  # Consistent with project ID

            # Get issues in the project
            issues = await client.issues.get_all(project_id=5)
            assert len(issues) == 1
            assert isinstance(issues[0], Issue)
            assert issues[0].id == 502
            assert issues[0].project_id == 5  # Consistent with project ID

            # Verify all entities reference the same project (data consistency)
            assert project.id == tasks[0].project_id == issues[0].project_id


@pytest.mark.asyncio
async def test_data_consistency_with_multiple_projects_and_tasks() -> None:
    """Test data consistency when working with multiple projects and their tasks."""
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
            # Mock response for getting multiple projects
            mock_projects_response = {
                "projects": [
                    {
                        "id": 10,
                        "name": "First Project",
                        "status": "active",
                    },
                    {
                        "id": 11,
                        "name": "Second Project",
                        "status": "active",
                    },
                ]
            }

            # Mock response for getting tasks in first project
            mock_tasks_project_10_response = {
                "tasks": [
                    {
                        "id": 1001,
                        "name": "Task in First Project",
                        "status": "Not Started",
                        "priority": "High",
                        "project_id": 10,  # Reference to project 10
                    }
                ]
            }

            # Mock response for getting tasks in second project
            mock_tasks_project_11_response = {
                "tasks": [
                    {
                        "id": 1002,
                        "name": "Task in Second Project",
                        "status": "Not Started",
                        "priority": "Medium",
                        "project_id": 11,  # Reference to project 11
                    }
                ]
            }

            # Mock response for getting project 10 specifically
            mock_project_10_response = {
                "projects": [
                    {
                        "id": 10,
                        "name": "First Project",
                        "status": "active",
                    }
                ]
            }

            # Mock response for getting project 11 specifically
            mock_project_11_response = {
                "projects": [
                    {
                        "id": 11,
                        "name": "Second Project",
                        "status": "active",
                    }
                ]
            }

            # Set up the side effect to return different responses for each call
            responses = [
                mock_projects_response,  # For get_all projects
                mock_project_10_response,  # For getting specific project 10
                mock_tasks_project_10_response,  # For tasks in project 10
                mock_project_11_response,  # For getting specific project 11
                mock_tasks_project_11_response,  # For tasks in project 11
            ]
            mock_api_get.side_effect = responses

            # Get all projects
            projects = await client.projects.get_all()
            assert len(projects) == 2
            assert all(isinstance(p, Project) for p in projects)

            # Get first project and its tasks
            project_10 = await client.projects.get(project_id=10)
            tasks_10 = await client.tasks.get_all(project_id=10)
            assert len(tasks_10) == 1
            assert tasks_10[0].project_id == project_10.id

            # Get second project and its tasks
            project_11 = await client.projects.get(project_id=11)
            tasks_11 = await client.tasks.get_all(project_id=11)
            assert len(tasks_11) == 1
            assert tasks_11[0].project_id == project_11.id
            assert project_11.id == 11

            # Verify data consistency: tasks belong to correct projects
            assert tasks_10[0].project_id == 10
            assert tasks_11[0].project_id == 11
            assert (
                tasks_10[0].project_id != tasks_11[0].project_id
            )  # Different projects
